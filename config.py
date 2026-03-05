import os
from dotenv import load_dotenv

load_dotenv()

# DANDI
DANDISET_ID: str = "000004"
DANDISET_VERSION: str = "0.220126.1852"

# PostgreSQL
PG_DSN: str = os.environ["PG_DSN"]

# Neo4j
NEO4J_URI: str = os.environ["NEO4J_URI"]
NEO4J_USER: str = os.environ["NEO4J_USER"]
NEO4J_PASS: str = os.environ["NEO4J_PASS"]