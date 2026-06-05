import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.config import DB_PATH, COLLECTION_NAME, EMBEDDING_MODEL_NAME


client = chromadb.PersistentClient(
    path=DB_PATH
)

sentence_transformer_ef = SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL_NAME,
    device="cpu",
    normalize_embeddings=True
)

collection_instance = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=sentence_transformer_ef
)


def get_collection():
    return collection_instance