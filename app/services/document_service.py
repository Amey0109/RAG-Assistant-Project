from typing import Dict, Any, List

from fastapi import UploadFile, HTTPException

from app.database.chroma_client import get_collection
from app.services.pdf_service import build_chunks_from_uploaded_pdf


def validate_pdf_file(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")


def add_uploaded_pdf_to_chromadb(
    file: UploadFile,
    user_id: str,
    replace_existing_source: bool = True
) -> Dict[str, Any]:
    validate_pdf_file(file)

    source_name = file.filename
    all_chunks, metadatas, ids = build_chunks_from_uploaded_pdf(
        file=file,
        source_name=source_name
    )

    collection = get_collection(user_id)
    deleted_old_chunks = 0

    if replace_existing_source:
        existing = collection.get(where={"source": source_name}, include=["metadatas"])
        if existing["ids"]:
            deleted_old_chunks = len(existing["ids"])
            collection.delete(ids=existing["ids"])

    collection.add(documents=all_chunks, metadatas=metadatas, ids=ids)

    return {
        "source": source_name,
        "chunks_inserted": len(all_chunks),
        "old_chunks_deleted": deleted_old_chunks,
        "total_chunks_in_collection": collection.count(),
        "first_chunk_preview": all_chunks[0],
        "first_chunk_metadata": metadatas[0]
    }


def get_available_sources(user_id: str) -> List[str]:
    collection = get_collection(user_id)
    data = collection.get(include=["metadatas"])
    sources = []
    for metadata in data["metadatas"]:
        if metadata and "source" in metadata:
            sources.append(metadata["source"])
    return sorted(set(sources))


def check_document_exists(user_id: str, source_name: str):
    collection = get_collection(user_id)
    result = collection.get(where={"source": source_name}, include=["metadatas"])
    return {
        "source": source_name,
        "exists": bool(result["ids"]),
        "chunks_found": len(result["ids"])
    }


def delete_document_by_source(user_id: str, source_name: str):
    collection = get_collection(user_id)
    existing = collection.get(where={"source": source_name}, include=["metadatas"])

    if not existing["ids"]:
        return {
            "message": "No chunks found for this source.",
            "source": source_name,
            "deleted_chunks": 0,
            "total_chunks_left": collection.count()
        }

    deleted_count = len(existing["ids"])
    collection.delete(ids=existing["ids"])

    return {
        "message": "Document deleted successfully.",
        "source": source_name,
        "deleted_chunks": deleted_count,
        "total_chunks_left": collection.count()
    }