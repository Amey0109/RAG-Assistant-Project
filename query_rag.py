import chromadb
import ollama
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


DB_PATH = "./chroma_db"
COLLECTION_NAME = "test_data"
MODEL_NAME = "all-mpnet-base-v2"
OLLAMA_MODEL = "llama3.2:3b"


def get_available_sources(collection):
    data = collection.get(include=["metadatas"])

    sources = []

    for metadata in data["metadatas"]:
        if metadata and "source" in metadata:
            sources.append(metadata["source"])

    return sorted(set(sources))


def detect_source_from_query(query, sources):
    query_lower = query.lower()

    for source in sources:
        source_lower = source.lower()

        if source_lower in query_lower:
            return source

        source_without_ext = source_lower.replace(".pdf", "")

        if source_without_ext in query_lower:
            return source

        words = (
            source_without_ext
            .replace("-", " ")
            .replace("_", " ")
            .replace(".", " ")
            .split()
        )

        for word in words:
            if len(word) > 3 and word in query_lower:
                return source

    return None


client = chromadb.PersistentClient(
    path=DB_PATH
)

sentence_transformer_ef = SentenceTransformerEmbeddingFunction(
    model_name=MODEL_NAME,
    device="cpu",
    normalize_embeddings=False
)

collection = client.get_collection(
    name=COLLECTION_NAME,
    embedding_function=sentence_transformer_ef
)

query = input("Ask Question: ")

sources = get_available_sources(collection)

source_filter = detect_source_from_query(query, sources)

if source_filter:
    print("Searching only in:", source_filter)

    results = collection.query(
        query_texts=[query],
        n_results=6,
        where={
            "source": source_filter
        },
        include=["documents", "metadatas", "distances"]
    )
    print("\nRetrieved Chunks:")

    for doc, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        print("\n--------------------")
        print("Distance:", distance)
        print("Metadata:", metadata)
        print("Chunk Preview:", doc[:500])
        print(f"Chunks results: {results['documents']}")

else:
    print("No specific PDF detected. Searching all documents.")

    results = collection.query(
    query_texts=[query],
    n_results=6,
    include=["documents", "metadatas", "distances"]
    )
    print("\nRetrieved Chunks:")

    for doc, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        print("\n--------------------")
        print("Distance:", distance)
        print("Metadata:", metadata)
        print("Chunk Preview:", doc[:500])
        print(f"Chunks results: {results['documents']}")

print("\nRetrieved Sources:")
for metadata in results["metadatas"][0]:
    print(metadata)


context_parts = []

for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
    source = metadata.get("source", "Unknown source")
    page = metadata.get("page_number", "Unknown page")
    chunk_index = metadata.get("chunk_index", "Unknown chunk")

    context_parts.append(
        f"""
[Source PDF: {source}]
[PDF Page: {page}]
[Chunk Index: {chunk_index}]

{doc}
""".strip()
    )

context = "\n\n--------------------\n\n".join(context_parts)


prompt = f"""
You are a strict RAG assistant.

Answer the question using ONLY the context below.

Rules:
1. Do not guess.
2. Do not use outside knowledge.
3. Use "PDF Page" only from the metadata.
4. Do not confuse clause numbers like 8, 9, 10 with PDF page numbers.
5. If the answer is not present in the context, say:
   "I could not find this information in the provided documents."
6. Always retrive all the required information like main points and all sections from context and give whole answer.
7. Dont give half answer to any query search for all similarity in context like if little bit matches the question context retrive it.

Context:
{context}

Question:
{query}

Answer:
"""

print("\nAI Response:")

stream = ollama.chat(
    model=OLLAMA_MODEL,
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],
    stream=True
)

for chunk in stream:
    content = chunk["message"]["content"]
    print(content, end="", flush=True)

print()