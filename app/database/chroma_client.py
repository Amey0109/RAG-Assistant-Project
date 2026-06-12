import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.config import DB_PATH, EMBEDDING_MODEL_NAME


sentence_transformer_ef = SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL_NAME,
    device="cpu",
    normalize_embeddings=True
)


def get_collection(user_id: str):
    client = chromadb.PersistentClient(
        path=f"{DB_PATH}/{user_id}"
    )

    return client.get_or_create_collection(
        name=f"user_{user_id}",
        embedding_function=sentence_transformer_ef
    )