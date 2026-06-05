from typing import Optional, List, Dict, Any

from app.config import N_RESULTS
from app.database.chroma_client import get_collection
from app.services.document_service import get_available_sources


def detect_source_from_query(query: str, sources: List[str]) -> Optional[str]:
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


def retrieve_chunks(query: str, source_filter: Optional[str], n_results: int = N_RESULTS):
    collection = get_collection()

    if source_filter:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where={
                "source": source_filter
            },
            include=["documents", "metadatas", "distances"]
        )
    else:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    chunks = []

    for doc, metadata, distance in zip(documents, metadatas, distances):
        chunks.append(
            {
                "document": doc,
                "metadata": metadata,
                "distance": distance,
                "preview": doc[:500]
            }
        )

    return chunks


def build_context_from_chunks(chunks: List[Dict[str, Any]]) -> str:
    context_parts = []

    for chunk in chunks:
        doc = chunk["document"]
        metadata = chunk["metadata"]

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

    return "\n\n--------------------\n\n".join(context_parts)


def build_prompt(query: str, context: str) -> str:
    return f"""
You are a helpful document question-answering assistant.

Use the provided context to answer the user's question.

Important rules:
1. Use only information from the context.
2. Do not use outside knowledge.
3. Do not invent facts.
4. If the context contains relevant information, answer using that information.
5. If the context contains partial information, answer with the partial information and say that no more details were found.
6. Only say "I could not find this information in the provided documents." when there is no relevant information at all in the context.
7. Mention source PDF and PDF page if available in the metadata.

Context:
{context}

Question:
{query}

Answer:
"""


def prepare_rag_prompt(query: str):
    sources = get_available_sources()

    source_filter = detect_source_from_query(
        query=query,
        sources=sources
    )

    chunks = retrieve_chunks(
        query=query,
        source_filter=source_filter,
        n_results=N_RESULTS
    )

    context = build_context_from_chunks(chunks)

    prompt = build_prompt(
        query=query,
        context=context
    )

    return {
        "source_filter": source_filter,
        "chunks": chunks,
        "context": context,
        "prompt": prompt
    }