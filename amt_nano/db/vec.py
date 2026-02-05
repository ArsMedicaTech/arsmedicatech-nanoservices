"""
Vector database for RAG (retrieval-augmented generation) with SurrealDB.
"""

import json
from typing import Any, Dict, List, Optional, cast

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

# Import surrealdb with type ignore since it lacks proper stubs
from surrealdb import AsyncSurreal  # type: ignore[import-untyped]

from settings import (
    SURREALDB_DATABASE,
    SURREALDB_HOST,
    SURREALDB_NAMESPACE,
    SURREALDB_PASS,
    SURREALDB_PORT,
    SURREALDB_PROTOCOL,
    SURREALDB_USER,
    logger,
)

DB_URL = f"{SURREALDB_PROTOCOL}://{SURREALDB_HOST}:{SURREALDB_PORT}/rpc"

knowledge_hsnw = """
-- Switch to your namespace / database
USE ns {ns} DB {db};

-- Table for each passage / triple
DEFINE TABLE {table_name}
  PERMISSIONS NONE
  SCHEMAFULL;

-- Add fields
DEFINE FIELD text       ON {table_name} TYPE string;
DEFINE FIELD embedding  ON {table_name} TYPE array;   -- OpenAI returns 1536-floats arrays

-- Create a 1536-dim HNSW vector index for cosine similarity
DEFINE INDEX idx_knn ON {table_name}
  FIELDS embedding
  HNSW DIMENSION 1536 DIST COSINE;
"""

knowledge_hsnw_v2 = """
-- Switch to your namespace / database
USE ns {ns} DB {db};

-- Table for each passage / triple
DEFINE TABLE {table_name}
  PERMISSIONS NONE
  SCHEMAFULL;

-- ONE-TIME migration -------------------------------------------
REMOVE FIELD embedding ON {table_name};           -- if the field exists
REMOVE INDEX idx_knn ON {table_name};             -- if the index exists

-- Re-define field as an array of 64-bit floats, dimension 1536
DEFINE FIELD embedding ON {table_name}
  TYPE array<float>
  ASSERT array::len($value) = 1536;

-- Re-create the same HNSW index
DEFINE INDEX idx_knn ON {table_name}
  FIELDS embedding
  HNSW DIMENSION 1536 DIST COSINE TYPE F64;
"""

DEFAULT_SYSTEM_PROMPT = """
You are a medical knowledge retrieval assistant who has access to a large database of medical knowledge.
Your task is to answer questions based on the provided context.
If the context does not contain enough information, you should indicate that you cannot answer the question.
"""


class BatchItem:
    """
    A simple class to represent a single item in a batch for insertion.
    Each item should have 'id' and 'text' keys.
    """

    def __init__(self, id: str, text: str) -> None:
        """
        Initialize a BatchItem instance.
        :param id: Unique identifier for the item.
        :param text: The text content of the item.
        :raises ValueError: If id or text is empty.
        :return: None
        """
        if not id or not text:
            raise ValueError(
                "Both 'id' and 'text' must be provided and cannot be empty."
            )
        self.id = id
        self.text = text


class BatchList:
    """
    A simple class to represent a list of dictionaries for batch processing.
    """

    def __init__(self, data: List[BatchItem]) -> None:
        """
        Initialize a BatchList instance.
        :param data: A list of BatchItem instances.
        :raises ValueError: If data is empty or contains non-BatchItem instances.
        :return: None
        """
        if not data:
            raise ValueError("Data cannot be empty.")
        self.data = data


class Vec:
    """
    Vector database for RAG (retrieval-augmented generation) with SurrealDB.

    Example usage:
    ```python
    client = AsyncOpenAI(api_key="your-openai-api-key")
    vec = Vec(client)
    msg = asyncio.run(vec.rag_chat("Some query..."))
    logger.debug(msg)
    ```
    """

    def __init__(
        self,
        openai_client: Optional[AsyncOpenAI] = None,
        db_url: str = DB_URL,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        embed_model: str = "text-embedding-3-small",
        inference_model: str = "gpt-4.1-nano",
        surrealdb_namespace: Optional[str] = SURREALDB_NAMESPACE,
        surrealdb_database: Optional[str] = SURREALDB_DATABASE,
        surrealdb_user: Optional[str] = SURREALDB_USER,
        surrealdb_pass: Optional[str] = SURREALDB_PASS,
        surrealdb_table: Optional[str] = "knowledge",
        logger: Any = logger,
    ) -> None:
        """
        Initialize the Vec instance.
        :param openai_client: An instance of AsyncOpenAI client for making API calls.
        :param db_url: URL of the SurrealDB instance.
        :param system_prompt: A system prompt to guide the model's responses.
        :param embed_model: The OpenAI model to use for embeddings (default: "text-embedding-3-small").
        :param inference_model: The OpenAI model to use for inference (default: "gpt-4.1-nano").
        :param surrealdb_namespace: Namespace for SurrealDB.
        :param surrealdb_database: Database name for SurrealDB.
        :param surrealdb_user: Username for SurrealDB authentication.
        :param surrealdb_pass: Password for SurrealDB authentication.
        :param surrealdb_table: Table name in SurrealDB to store knowledge data.
        :param logger: Logger instance for logging.
        :return: None
        """
        self.client: Optional[AsyncOpenAI] = openai_client
        self.system_prompt = system_prompt
        self.db_url = db_url
        self.embed_model = embed_model
        self.model = inference_model

        self.surrealdb_namespace = surrealdb_namespace
        self.surrealdb_database = surrealdb_database
        self.surrealdb_user = surrealdb_user
        self.surrealdb_pass = surrealdb_pass
        self.surrealdb_table = surrealdb_table

        self.logger = logger

    async def init(self) -> None:
        """
        Initialize the vector database.
        This method connects to the SurrealDB instance, signs in with credentials,
        and sets up the necessary schema for the knowledge table.
        It creates the knowledge table with the required fields and indices.
        :raises Exception: If the connection or query fails.
        :return: None
        """
        db = AsyncSurreal(self.db_url)  # type: ignore[no-untyped-call]
        try:
            await db.connect()  # type: ignore[no-untyped-call]
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to connect to SurrealDB: {e}")
            raise
        try:
            await db.signin({"username": self.surrealdb_user, "password": self.surrealdb_pass})  # type: ignore[no-untyped-call]
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to sign in to SurrealDB: {e}")
            raise
        try:
            await db.use(self.surrealdb_namespace, self.surrealdb_database)  # type: ignore[no-untyped-call]
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to use namespace/database: {e}")
            raise
        try:
            await db.query(
                knowledge_hsnw_v2.format(
                    ns=self.surrealdb_namespace,
                    db=self.surrealdb_database,
                    table_name=self.surrealdb_table,
                )
            )  # type: ignore[no-untyped-call]
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to create knowledge table: {e}")
            raise
        try:
            await db.close()  # type: ignore[no-untyped-call]
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to close SurrealDB connection: {e}")
            raise

    async def seed(
        self,
        data_source: str,
        data_type: str = "json",
        chunk: int = 96,
        files: bool = False,
        root_file_path: Optional[str] = None,
    ) -> None:
        """
        Seed the vector database with knowledge data.
        :param data_source: Path to the data source file (JSON or JSONL).
        :param data_type: Type of the data source file ('json' or 'jsonl').
        :param chunk: Number of records to insert in each batch.
        :param files: Whether the JSON passed in refers to files to read.
        :param root_file_path: Root path to prepend to file names if 'files' is True.
        :return: None
        """
        db = AsyncSurreal(self.db_url)  # type: ignore[no-untyped-call]
        await db.connect()  # type: ignore[no-untyped-call]
        await db.signin({"username": self.surrealdb_user, "password": self.surrealdb_pass})  # type: ignore[no-untyped-call]
        await db.use(self.surrealdb_namespace, self.surrealdb_database)  # type: ignore[no-untyped-call]

        res = await db.query("INFO FOR DB;")  # type: ignore[no-untyped-call]
        self.logger.debug(f"Database info: {res}")

        res = await db.query(f"INFO FOR TABLE {self.surrealdb_table};")  # type: ignore[no-untyped-call]
        self.logger.debug(f"Table info: {res}")

        if data_type == "jsonl":
            docs: List[Dict[str, Any]] = [
                json.loads(new_line)
                for new_line in open(data_source, "r", encoding="utf-8")
                if new_line.strip()
            ]
        elif data_type == "json":
            with open(data_source, "r", encoding="utf-8") as f:
                docs = json.load(f)
        else:
            raise ValueError(
                f"Unsupported data type: {data_type}. Supported types are 'jsonl' and 'json'."
            )

        batch: List[Dict[str, Any]] = []
        batch_data: List[Dict[str, str]] = []

        for doc in docs:
            batch.append(doc)
            if len(batch) == chunk:
                self.logger.debug(f"[SEED] Inserting {len(batch)} records...")
                if files:
                    batch_data = []
                    for d in batch:
                        file_path = (
                            d["filename"]
                            if root_file_path is None
                            else f"{root_file_path}/{d['filename']}"
                        )
                        with open(file_path, "r", encoding="utf-8") as f:
                            file_text = f.read()
                        batch_data.append({"id": str(d["id"]), "text": file_text})
                else:
                    batch_data = [
                        {"id": str(d["id"]), "text": str(d["text"])} for d in batch
                    ]
                batch_list = BatchList([BatchItem(**d) for d in batch_data])
                await self.insert(batch_list, db)
                self.logger.debug("[SEED] Insert complete.")
                batch = []
        if batch:
            self.logger.debug(f"[SEED] Inserting {len(batch)} records...")
            if files:
                batch_data = []
                for d in batch:
                    file_path = (
                        d["filename"]
                        if root_file_path is None
                        else f"{root_file_path}/{d['filename']}"
                    )
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_text = f.read()
                    batch_data.append({"id": str(d["id"]), "text": file_text})
            else:
                batch_data = [
                    {"id": str(d["id"]), "text": str(d["text"])} for d in batch
                ]
            batch_list = BatchList([BatchItem(**d) for d in batch_data])
            await self.insert(batch_list, db)
            self.logger.debug("[SEED] Insert complete.")

        res = await db.query(f"SELECT id, text FROM {self.surrealdb_table} LIMIT 5;")  # type: ignore[no-untyped-call]
        self.logger.debug(f"Sample records: {res}")

    async def insert(self, batch: BatchList, db: Any) -> None:
        """
        Insert a batch of records into the knowledge table.
        :param batch: A list of dictionaries, each containing 'id' and 'text' keys.
        :param db: An instance of AsyncSurreal connected to the database.
        :return: None
        """
        if not self.client:
            raise ValueError(
                "This function requires an OpenAI client to be initialized."
            )

        if not batch.data:
            self.logger.warning("Batch is empty. Nothing to insert.")
            return
        # All items in batch.data are guaranteed to be BatchItem instances by BatchList validation.
        self.logger.debug(
            f"[DEBUG] Inserting {len(batch.data)} records into SurrealDB..."
        )
        # Prepare the batch for OpenAI embedding
        batch_dicts = [
            item.__dict__ for item in batch.data
        ]  # Convert BatchItem to dict

        texts = [d["text"] for d in batch_dicts]
        resp = await self.client.embeddings.create(model=self.embed_model, input=texts)
        embeds: List[List[float]] = [e.embedding for e in resp.data]

        items = []
        for b, e in zip(batch_dicts, embeds):
            # REMOVE the table prefix if it exists to avoid coaching:coaching:ID
            raw_id = b["id"].split(":")[-1]
            items.append(
                {
                    "id": f"{self.surrealdb_table}:{raw_id}",
                    "text": b["text"],
                    "embedding": e,
                }
            )

        try:
            # 4. Use a single UPSERT to handle both new and existing records
            query = f"INSERT INTO {self.surrealdb_table} $data ON DUPLICATE KEY UPDATE text = $after.text, embedding = $after.embedding;"

            result = await db.query(query, {"data": items})
            # self.logger.debug(f"[DEBUG] SurrealDB UPSERT result: {json.dumps(result, indent=2)}")
            self.logger.debug(
                f"[DEBUG] SurrealDB UPSERT result: {str(result)[:500]}..."
            )  # Log only the beginning of the result for brevity

            print(f"Type of result: {type(result)}")

            if isinstance(result, str):
                first_500_chars = result[:500]
                last_500_chars = result[-500:]
                self.logger.error(
                    f"SURREALDB ERROR: Result is a string. First 500 chars: {first_500_chars}... Last 500 chars: ...{last_500_chars}"
                )
                return

            # Check for errors in the SurrealDB response list
            if isinstance(result, list) and len(result) > 0:
                print(result[0].keys())
                if "status" in result[0] and result[0]["status"] == "ERR":
                    self.logger.error(f"SURREALDB ERROR: {result[0]['detail']}")
                    return  # Stop here so you don't think it succeeded

            self.logger.debug(f"[OK] Processed {len(items)} records.")
        except Exception as ex:
            self.logger.error(f"[FAIL] Batch insertion failed: {ex}")

    async def get_context(
        self, question: str, k: int = 4, table_name: str = "knowledge"
    ) -> Optional[List[str]]:
        """
        Retrieve context from the knowledge base for a given question.
        :param question: The question for which context is to be retrieved.
        :param k: The number of nearest neighbors to retrieve (default: 4).
        :param table_name: The name of the table to query (default: "knowledge").
        :return: List of context strings or None if an error occurs.
        """
        if not self.client:
            raise ValueError(
                "This function requires an OpenAI client to be initialized."
            )
        resp = await self.client.embeddings.create(
            model=self.embed_model, input=[question]
        )
        qvec: List[float] = resp.data[0].embedding
        db = AsyncSurreal(self.db_url)  # type: ignore[no-untyped-call]
        await db.connect()  # type: ignore[no-untyped-call]
        await db.signin({"username": self.surrealdb_user, "password": self.surrealdb_pass})  # type: ignore[no-untyped-call]
        await db.use(self.surrealdb_namespace, self.surrealdb_database)  # type: ignore[no-untyped-call]

        # SurrealQL k-NN syntax: <k, COSINE|> $vector
        q = f"SELECT text FROM {table_name} WHERE embedding <|{k}, COSINE|> $vec;"

        try:
            res = await db.query(q, {"vec": qvec})  # type: ignore[no-untyped-call]
            self.logger.debug(
                f"[DEBUG] Raw SurrealDB result: {json.dumps(res, indent=2)}"
            )
        except Exception as e:
            self.logger.error(f"[ERROR] Exception while querying SurrealDB: {e}")
            return None
        finally:
            await db.close()  # type: ignore[no-untyped-call]

        # Ensure 'res' is a list of dicts containing 'text'
        if isinstance(res, list):
            return [row["text"] for row in res if isinstance(row, dict) and "text" in row]  # type: ignore
        elif "result" in res and isinstance(res["result"], list):
            return [row["text"] for row in res["result"] if isinstance(row, dict) and "text" in row]  # type: ignore
        else:
            self.logger.error(f"[ERROR] Unexpected result format from SurrealDB: {res}")
            return None

    async def rag_chat(
        self,
        question: str,
        max_tokens: int = 400,
        k: int = 4,
        table_name: str = "knowledge",
    ) -> str:
        """
        Perform a retrieval-augmented generation (RAG) chat with the OpenAI model.
        :param question: The question to ask the model.
        :param max_tokens: The maximum number of tokens to generate in the response (default: 400).
        :param k: The number of nearest neighbors to retrieve for context (default: 4).
        :param table_name: The name of the table to query for context (default: "knowledge").
        :return: str: The model's response to the question.
        """
        if not self.client:
            raise ValueError(
                "This function requires an OpenAI client to be initialized."
            )
        context = await self.get_context(question, k=k, table_name=table_name)

        if not context:
            return "I don't have enough information to answer that question."

        # Convert messages to proper ChatCompletionMessageParam format
        def to_message_param(role: str, content: str) -> ChatCompletionMessageParam:
            if role == "system":
                return cast(
                    ChatCompletionMessageParam, {"role": "system", "content": content}
                )
            elif role == "user":
                return cast(
                    ChatCompletionMessageParam, {"role": "user", "content": content}
                )
            else:
                raise ValueError(f"Unknown role: {role}")

        messages = [
            to_message_param("system", self.system_prompt),
            to_message_param(
                "system", "Context:\n" + "\n".join(f"- {c}" for c in context)
            ),
            to_message_param("user", question),
        ]

        answer = (
            (
                await self.client.chat.completions.create(
                    model=self.model, messages=messages, max_tokens=max_tokens
                )
            )
            .choices[0]
            .message.content
        )
        return answer if answer is not None else ""
