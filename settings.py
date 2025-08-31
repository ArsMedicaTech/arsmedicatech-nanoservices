""""""

import os
from os.path import dirname, join

from dotenv import load_dotenv

from amt_nano.logger import Logger

dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

logger = Logger()


GRPC_URL = os.environ.get("GRPC_URL", "localhost:50051")
