""""""

import os
from os.path import dirname, join

from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)


GRPC_URL = os.environ.get("GRPC_URL", "localhost:50051")
