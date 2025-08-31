"""
Service for looking up treatment pathways using hybrid vector/graph search.
"""

from typing import Any, Dict, List

from sentence_transformers import SentenceTransformer
from surrealdb import Surreal  # type: ignore

from settings import SURREALDB_URL
from tests.test_pathways import OUTCOMES, PATIENTS, TREATMENT_RECORDS, TREATMENTS

# This model creates a 384-dimension vector.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


async def migrate():
    """Connects to DB, generates embeddings, and populates the graph."""
    print("Starting database population...")

    # 1. Initialize Embedding Model
    model = SentenceTransformer(EMBEDDING_MODEL)

    async with Surreal(SURREALDB_URL) as db:  # type: ignore
        await db.signin({"user": "root", "pass": "root"})  # type: ignore
        await db.use("test", "test")  # type: ignore

        print("Connected to SurrealDB.")

        # 2. Generate and Insert Patient Data with Embeddings
        print("Generating embeddings and inserting patient data...")
        for patient in PATIENTS:
            summary = patient.pop("summary")
            embedding = model.encode(summary).tolist()
            # The `CREATE` statement inserts the record and its vector
            await db.create(patient["id"], {**patient, "summary": summary, "embedding": embedding})  # type: ignore

        # 3. Insert Treatment and Outcome Nodes
        print("Inserting treatment and outcome nodes...")
        for treatment in TREATMENTS:
            await db.create(treatment["id"], treatment)  # type: ignore
        for outcome in OUTCOMES:
            await db.create(outcome["id"], outcome)  # type: ignore

        # 4. Create Graph Relationships (Edges)
        print("Creating graph relationships...")
        for record in TREATMENT_RECORDS:
            # The RELATE statement builds the graph connections
            await db.query(  # type: ignore
                "RELATE $patient->received_treatment->$treatment SET outcome = $outcome",
                {
                    "patient": record["patient"],
                    "treatment": record["treatment"],
                    "outcome": record["outcome"],
                },
            )

        # 5. Define Vector Index for efficient search
        print("Defining a vector index on patient embeddings...")
        await db.query(  # type: ignore
            f"DEFINE INDEX patient_embedding_idx ON TABLE patient COLUMNS embedding MTREE DIMENSION {model.get_sentence_embedding_dimension() or 384}"
        )

        print("\nDatabase population complete.")


async def find_recommendations(new_patient_summary: str):
    """Finds treatment recommendations for a new patient."""
    print(f"Finding recommendations for new patient:\n'{new_patient_summary}'\n")

    # 1. Initialize Embedding Model
    model = SentenceTransformer(EMBEDDING_MODEL)

    async with Surreal(SURREALDB_URL) as db:  # type: ignore
        await db.signin({"user": "root", "pass": "root"})  # type: ignore
        await db.use("test", "test")  # type: ignore

        # 2. Generate the query vector for the new patient
        query_vector = model.encode(new_patient_summary).tolist()

        # 3. The Hybrid Graph-Vector Query
        # This one SurrealQL query performs both the vector search and graph traversal.
        hybrid_query = """
            SELECT
                id,
                summary,
                vector::similarity::cosine(embedding, $query_vector) AS similarity,
                ->received_treatment->treatment.name AS treatments,
                ->received_treatment.outcome->(SELECT status FROM ONLY $value) AS outcomes
            FROM patient
            WHERE embedding <|3|> $query_vector
            ORDER BY similarity DESC;
        """

        print("Executing hybrid query...")
        results: List[Dict[str, Any]] = await db.query(hybrid_query, {"query_vector": query_vector})  # type: ignore

        # 4. Process and Display the Results
        print("\n--- Top 3 Similar Past Cases & Outcomes ---\n")

        if results and results[0].get("result"):
            similar_cases: List[Dict[str, Any]] = results[0]["result"]
            for i, case in enumerate(similar_cases):
                print(
                    f"Case #{i + 1}: Patient {case['id']} (Similarity: {case['similarity']})"
                )
                print(f"  Summary: {case['summary']}")
                for j, treatment in enumerate(case["treatments"]):
                    outcome_status = (
                        case["outcomes"][j][0]
                        if case["outcomes"] and case["outcomes"][j]
                        else "Unknown"
                    )
                    print(f"  -> Treatment Taken: {treatment}")
                    print(f"     Outcome: {outcome_status}")
                print("-" * 20)
        else:
            print("No similar cases found.")
