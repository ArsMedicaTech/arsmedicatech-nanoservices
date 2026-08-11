"""
Typesense-backed ICD-10-CM candidate retrieval.
"""

from typing import Any, Dict, List, Optional, TypedDict

import requests

from settings import (
    TYPESENSE_API_KEY,
    TYPESENSE_ICD_COLLECTION,
    TYPESENSE_URL,
    logger,
)


class IcdCandidate(TypedDict, total=False):
    """A single ICD-10-CM candidate returned by the search index."""

    code: str
    system: str
    display: str
    billable: bool
    is_unspecified: bool
    text_match_score: int
    rank: int
    rationale: Optional[str]


class IcdSearchService:
    """
    Search the Typesense `icd_codes` collection for candidate codes.

    Uses a search-only API key and performs batched multi_search calls for
    the lowest possible per-note latency.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection: Optional[str] = None,
    ) -> None:
        self.url = (url or TYPESENSE_URL or "").rstrip("/")
        self.api_key = api_key or TYPESENSE_API_KEY or ""
        self.collection = collection or TYPESENSE_ICD_COLLECTION or "icd_codes"
        self.headers = {
            "X-TYPESENSE-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

    def candidates(
        self, span_text: str, top_k: int = 10, billable_only: bool = False
    ) -> List[IcdCandidate]:
        """
        Retrieve the top-K ICD-10-CM candidates for a single span.
        """
        results = self.search_spans(
            [span_text], top_k=top_k, billable_only=billable_only
        )
        return results[0] if results else []

    def search_spans(
        self,
        span_texts: List[str],
        top_k: int = 10,
        billable_only: bool = False,
    ) -> List[List[IcdCandidate]]:
        """
        Retrieve top-K candidates for multiple spans in one multi_search request.
        """
        if not self.api_key or not self.url or not self.collection:
            logger.warning("Typesense not configured; returning empty candidates")
            return [[] for _ in span_texts]

        base_search: Dict[str, Any] = {
            "collection": self.collection,
            "query_by": "code,code_nodot,short_desc,long_desc,synonyms",
            "sort_by": "_text_match:desc,rank:desc",
            "per_page": top_k,
            "limit_hits": top_k,
        }
        if billable_only:
            base_search["filter_by"] = "billable:=true"

        payload: Dict[str, Any] = {
            "searches": [{**base_search, "q": text} for text in span_texts]
        }

        try:
            response = requests.post(
                f"{self.url}/multi_search",
                json=payload,
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.warning(f"Typesense multi_search failed: {e}")
            return [[] for _ in span_texts]

        results = data.get("results", [])
        output: List[List[IcdCandidate]] = []

        for result in results:
            hits = result.get("hits", [])
            candidates: List[IcdCandidate] = []
            for hit in hits:
                doc = hit.get("document", {})
                code = str(doc.get("code", doc.get("code_nodot", "")))
                display = str(
                    doc.get("long_desc")
                    or doc.get("short_desc")
                    or doc.get("code", "")
                )
                system = str(
                    doc.get("system")
                    or "http://hl7.org/fhir/sid/icd-10-cm"
                )
                candidates.append(
                    IcdCandidate(
                        code=code,
                        system=system,
                        display=display,
                        billable=bool(doc.get("billable", True)),
                        is_unspecified=bool(doc.get("is_unspecified", False)),
                        text_match_score=int(hit.get("text_match", 0)),
                        rank=int(doc.get("rank", 0)),
                        rationale=None,
                    )
                )
            output.append(candidates)

        while len(output) < len(span_texts):
            output.append([])
        return output
