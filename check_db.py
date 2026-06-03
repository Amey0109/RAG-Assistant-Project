import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


DB_PATH = "./chroma_db"
COLLECTION_NAME = "test_data"


client = chromadb.PersistentClient(
    path=DB_PATH
)

sentence_transformer_ef = SentenceTransformerEmbeddingFunction(
    model_name="all-mpnet-base-v2",
    device="cpu",
    normalize_embeddings=False
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=sentence_transformer_ef
)

data = collection.get(
    include=["metadatas"]
)

sources = []

for metadata in data["metadatas"]:
    if metadata and "source" in metadata:
        sources.append(metadata["source"])

unique_sources = sorted(set(sources))

print("\nPDFs stored in ChromaDB:")

if unique_sources:
    for source in unique_sources:
        print("-", source)
else:
    print("No PDFs found in DB.")

print("\nTotal chunks in DB:", collection.count())