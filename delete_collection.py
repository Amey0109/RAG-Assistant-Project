import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


# Creating chroma client and inserting these chunks into chroma collection(DB)
client = chromadb.PersistentClient(
    path="./chroma_db"
)


client.delete_collection("test_data")
