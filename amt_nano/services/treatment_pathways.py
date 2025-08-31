"""
Service for looking up treatment pathways using hybrid vector/graph search.
"""

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
