from fastapi import APIRouter, UploadFile, File, HTTPException, Query

from app.database.chroma_client import get_collection
from app.services.document_service import (
    add_uploaded_pdf_to_chromadb,
    get_available_sources,
    check_document_exists,
    delete_document_by_source
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    replace_existing_source: bool = Query(default=True)
):
    try:
        result = add_uploaded_pdf_to_chromadb(
            file=file,
            replace_existing_source=replace_existing_source
        )

        return {
            "message": "PDF uploaded and embedded successfully.",
            "data": result
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.get("")
def list_documents():
    try:
        collection = get_collection()

        sources = get_available_sources()

        return {
            "documents": sources,
            "total_documents": len(sources),
            "total_chunks": collection.count()
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.get("/check")
def check_document(
    source_name: str = Query(...)
):
    try:
        return check_document_exists(source_name)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.delete("")
def delete_document(
    source_name: str = Query(...)
):
    try:
        return delete_document_by_source(source_name)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )