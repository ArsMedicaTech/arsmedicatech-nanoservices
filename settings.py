""""""

import os
from os.path import dirname, join

from dotenv import load_dotenv

from amt_nano.logger import Logger

dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

logger = Logger()


SURREALDB_NAMESPACE = os.environ.get("SURREALDB_NAMESPACE")
SURREALDB_DATABASE = os.environ.get("SURREALDB_DATABASE")
SURREALDB_USER = os.environ.get("SURREALDB_USER")
SURREALDB_PASS = os.environ.get("SURREALDB_PASS")

SURREALDB_PROTOCOL = os.environ.get("SURREALDB_PROTOCOL", "ws")
SURREALDB_HOST = os.environ.get("SURREALDB_HOST", "localhost")
SURREALDB_PORT = os.environ.get("SURREALDB_PORT", 8700)

SURREALDB_URL = f"{SURREALDB_PROTOCOL}://{SURREALDB_HOST}:{SURREALDB_PORT}"

SURREALDB_ICD_DB = os.environ.get("SURREALDB_ICD_DB", "diagnosis")


REDIS_HOST = os.environ.get("SURREALDB_ICD_DB", "diagnosis")
REDIS_PORT = int(os.environ.get("SURREALDB_ICD_DB", 0))
NOTIFICATIONS_CHANNEL = int(os.environ.get("SURREALDB_ICD_DB", "diagnosis"))

BUCKET_NAME = os.environ.get("SURREALDB_ICD_DB", "diagnosis")
TEXTRACT_AWS_ACCESS_KEY_ID = os.environ.get("SURREALDB_ICD_DB", "diagnosis")
TEXTRACT_AWS_SECRET_ACCESS_KEY = os.environ.get("SURREALDB_ICD_DB", "diagnosis")

UMLS_API_KEY = os.environ.get("SURREALDB_ICD_DB", "diagnosis")
ENCRYPTION_KEY = os.environ.get("SURREALDB_ICD_DB", "diagnosis")

print("SUREALDB_NAMESPACE:", SURREALDB_NAMESPACE)
print("SURREALDB_DATABASE:", SURREALDB_DATABASE)
print("SURREALDB_URL:", SURREALDB_URL)
print("SURREALDB_USER:", SURREALDB_USER)
print("SURREALDB_PASS:", SURREALDB_PASS)


GRPC_URL = os.environ.get("GRPC_URL", "localhost:50051")
