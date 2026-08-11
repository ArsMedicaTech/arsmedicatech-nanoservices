"""
ICD Autocoder Service.

Two-stage retrieval: Typesense candidate lookup is primary; UMLS is optional
best-effort enrichment. Every returned code traces to a document in the
`icd_codes` index.
"""

import json
import os
from typing import Any, Dict, List, Optional, TypedDict

import openai
import requests

from amt_nano.db.surreal import DbController
from amt_nano.services.cache_service import (
    create_text_hash,
    get_entity_cache,
    store_entity_cache,
)
from amt_nano.services.icd_search_service import IcdCandidate, IcdSearchService
from amt_nano.services.umls_api_service import UMLSApiService
from settings import (
    ICD_RANKING_ENABLED,
    ICD_RANKING_MODEL,
    NER_SERVICE_URL,
    NER_TIMEOUT_SECONDS,
    UMLS_API_KEY,
    logger,
)

CANDIDATE_ASSERTIONS = {"present", "historical"}


class Span(TypedDict, total=False):
    """A span produced by the v2 NER service."""

    text: str
    label: str
    start_char: int
    end_char: int
    assertion: str
    is_uncertain: bool
    sentence: str
    sentence_start_char: int
    cui: Optional[str]
    candidates: List[IcdCandidate]


class IcdAutocoderResponse(TypedDict, total=False):
    """v2 response contract for the ICD autocoder."""

    schema_version: int
    spans: List[Span]
    non_asserted_spans: List[Span]
    cached: bool
    ranking_applied: bool


class ICDAutoCoderService:
    """
    Extract asserted medical spans from a note and suggest ICD-10-CM candidates.
    """

    def __init__(self, text: str, db: Optional[DbController] = None) -> None:
        self.text = text
        self.umls_service: Optional[UMLSApiService] = (
            UMLSApiService(api_key=UMLS_API_KEY) if UMLS_API_KEY else None
        )
        self.icd_search = IcdSearchService()
        if db is None:
            db = DbController()
            db.connect()
        self.db = db

    def ner_concept_extraction(self, text: str) -> List[Span]:
        """
        Extract named entities from the provided text using the v2 NER endpoint.
        """
        headers = {"Content-Type": "application/json"}
        payload = {"text": text}

        response = requests.post(
            NER_SERVICE_URL,
            json=payload,
            headers=headers,
            timeout=NER_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"NER extraction failed: {response.status_code} {response.text}"
            )

        data = response.json()
        if data.get("schema_version") != 2:
            raise RuntimeError(
                f"NER service returned schema_version={data.get('schema_version')}, expected 2. "
                "Deploy TASK_FEATURES_SPEC_NER_ASSERTION first."
            )

        entities = data.get("entities", [])
        if not entities:
            raise ValueError("No entities found in the response.")

        return [Span(**entity) for entity in entities]

    def _enrich_with_umls(self, candidate_entities: List[Span]) -> None:
        """
        Best-effort UMLS enrichment: set `cui` and boost crosswalk-matched
        candidates. Errors and a missing UMLS_API_KEY are ignored.
        """
        if not self.umls_service:
            for entity in candidate_entities:
                entity["cui"] = None
            return

        for entity in candidate_entities:
            cui: Optional[str] = None
            crosswalk_codes: set[str] = set()
            try:
                norm = self.umls_service.search_concept(
                    entity["text"], sabs=["SNOMEDCT_US", "ICD10CM"]
                )
                if norm and norm.get("cui"):
                    cui = str(norm["cui"])
                    icd_matches = self.umls_service.get_icd10cm_from_cui(cui)
                    crosswalk_codes = {
                        str(item["code"]).replace(".", "")
                        for item in icd_matches
                        if item.get("code")
                    }
            except Exception as e:
                logger.warning(f"UMLS enrichment failed for '{entity['text']}': {e}")

            entity["cui"] = cui
            candidates = entity.get("candidates", [])
            if crosswalk_codes and candidates:
                matched = []
                unmatched = []
                for cand in candidates:
                    if cand.get("code", "").replace(".", "") in crosswalk_codes:
                        matched.append(cand)
                    else:
                        unmatched.append(cand)
                entity["candidates"] = matched + unmatched

    def _rank_candidates(self, candidate_entities: List[Span]) -> bool:
        """
        Optional LLM re-ranking. Returns True when ranking was applied.
        On failure, returns False and leaves the original order.
        """
        if not ICD_RANKING_MODEL:
            logger.warning("ICD ranking enabled but no model configured")
            return False

        request_spans: List[Dict[str, Any]] = []
        for idx, entity in enumerate(candidate_entities):
            cands = [
                {
                    "index": i,
                    "code": c["code"],
                    "display": c.get("display", ""),
                }
                for i, c in enumerate(entity.get("candidates", []))
            ]
            request_spans.append(
                {
                    "span_index": idx,
                    "text": entity["text"],
                    "sentence": entity.get("sentence", ""),
                    "candidates": cands,
                }
            )

        try:
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            prompt = (
                "You are an ICD-10-CM coding assistant. For each clinical span, "
                "return the candidate indices in preferred order. Respond only with JSON."
            )
            schema = {
                "type": "object",
                "properties": {
                    "spans": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "span_index": {"type": "integer"},
                                "ordered_candidate_indices": {
                                    "type": "array",
                                    "items": {"type": "integer"},
                                },
                                "rationales": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": [
                                "span_index",
                                "ordered_candidate_indices",
                                "rationales",
                            ],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["spans"],
                "additionalProperties": False,
            }
            completion = client.chat.completions.create(
                model=ICD_RANKING_MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {"spans": request_spans}, ensure_ascii=False
                        ),
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "ranking_response",
                        "schema": schema,
                        "strict": True,
                    },
                },
                timeout=30,
            )
            content = completion.choices[0].message.content
            if not content:
                raise ValueError("Empty response from ranking model")
            ranked = json.loads(content)
        except Exception as e:
            logger.warning(f"Ranking request failed: {e}")
            return False

        if not isinstance(ranked, dict) or "spans" not in ranked:
            return False

        for span_result in ranked["spans"]:
            idx = span_result.get("span_index")
            if not isinstance(idx, int) or idx < 0 or idx >= len(candidate_entities):
                continue
            entity = candidate_entities[idx]
            candidates = entity.get("candidates", [])

            raw_indices = span_result.get("ordered_candidate_indices", [])
            if not isinstance(raw_indices, list):
                continue
            if any(not isinstance(i, int) for i in raw_indices):
                # Contract violation: a returned code string is not an index.
                continue

            valid_indices = [i for i in raw_indices if 0 <= i < len(candidates)]
            rationales = span_result.get("rationales", [])

            new_candidates: List[IcdCandidate] = []
            for position, cand_idx in enumerate(valid_indices):
                cand = dict(candidates[cand_idx])
                cand["rationale"] = (
                    rationales[position] if position < len(rationales) else None
                )
                new_candidates.append(IcdCandidate(**cand))

            seen = set(valid_indices)
            for i, cand in enumerate(candidates):
                if i not in seen:
                    new_cand = dict(cand)
                    new_cand["rationale"] = None
                    new_candidates.append(IcdCandidate(**new_cand))

            entity["candidates"] = new_candidates

        return True

    def main(self) -> IcdAutocoderResponse:
        """
        Run the two-stage autocoder pipeline with caching.
        """
        text_hash = create_text_hash(self.text)

        cached_result = get_entity_cache(self.db, text_hash)
        if cached_result:
            logger.info(f"Using cached entity results for text hash: {text_hash}")
            return IcdAutocoderResponse(
                schema_version=2,
                spans=cached_result.get("spans", []),
                non_asserted_spans=cached_result.get("non_asserted_spans", []),
                cached=True,
                ranking_applied=cached_result.get("ranking_applied", False),
            )

        logger.info(f"No cache found for text hash: {text_hash}, processing")

        try:
            original_entities = self.ner_concept_extraction(self.text)
        except (RuntimeError, requests.RequestException) as e:
            logger.warning(f"NER unavailable, returning suggestions disabled: {e}")
            return IcdAutocoderResponse(
                schema_version=2, spans=[], non_asserted_spans=[],
                cached=False, ranking_applied=False,
            )
        
        candidate_entities = [
            e for e in original_entities if e["assertion"] in CANDIDATE_ASSERTIONS
        ]
        non_asserted = [
            e for e in original_entities if e["assertion"] not in CANDIDATE_ASSERTIONS
        ]

        if original_entities and not candidate_entities:
            logger.info(
                "NER returned %d spans, none asserted-present", len(original_entities)
            )

        # Primary retrieval from Typesense
        candidate_texts = [e["text"] for e in candidate_entities]
        candidates_by_span = (
            self.icd_search.search_spans(
                candidate_texts, top_k=10, billable_only=False
            )
            if candidate_texts
            else []
        )
        for entity, candidates in zip(candidate_entities, candidates_by_span):
            entity["candidates"] = candidates

        # Optional UMLS enrichment
        self._enrich_with_umls(candidate_entities)

        # Optional ranking
        ranking_applied = False
        if ICD_RANKING_ENABLED:
            ranking_applied = self._rank_candidates(candidate_entities)

        # Shape non-asserted spans to match the response contract.
        for entity in non_asserted:
            entity["candidates"] = []
            entity["cui"] = None

        store_entity_cache(
            self.db,
            text_hash,
            candidate_entities,
            non_asserted_spans=non_asserted,
            ranking_applied=ranking_applied,
        )
        logger.info(f"Stored entity results in cache for text hash: {text_hash}")

        return IcdAutocoderResponse(
            schema_version=2,
            spans=candidate_entities,
            non_asserted_spans=non_asserted,
            cached=False,
            ranking_applied=ranking_applied,
        )
