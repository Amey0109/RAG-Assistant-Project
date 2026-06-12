import os
import os

DB_PATH = "./data/chroma_db"
USERS_FILE_PATH = "./data/users.json"

COLLECTION_NAME = "test_data"
EMBEDDING_MODEL_NAME = "all-mpnet-base-v2"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
N_RESULTS = 4

JWT_SECRET = os.getenv("JWT_SECRET", "fallback-secret-for-local-dev")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24