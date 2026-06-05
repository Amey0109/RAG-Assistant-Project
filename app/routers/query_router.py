import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.request_models import QueryRequest
from app.services.rag_service import prepare_rag_prompt
from app.services.ollama_service import call_ollama


router = APIRouter(
    tags=["Query"]
)


@router.post("/query")
def query_rag(request: QueryRequest):
    try:
        total_start = time.perf_counter()

        t1 = time.perf_counter()
        rag_data = prepare_rag_prompt(request.query)
        rag_time = time.perf_counter() - t1

        t2 = time.perf_counter()
        answer = call_ollama(
            prompt=rag_data["prompt"],
            stream=False
        )
        ollama_time = time.perf_counter() - t2

        total_time = time.perf_counter() - total_start

        return {
            "query": request.query,
            "detected_source": rag_data["source_filter"],
            "chunks_used": rag_data["chunks"],
            "answer": answer,
            "timing": {
                "rag_prepare_time_ms": round(rag_time * 1000, 2),
                "ollama_time_ms": round(ollama_time * 1000, 2),
                "total_time_ms": round(total_time * 1000, 2)
            }
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.post("/query/stream")
def query_rag_stream(request: QueryRequest):
    try:
        rag_data = prepare_rag_prompt(request.query)

        return StreamingResponse(
            call_ollama(
                prompt=rag_data["prompt"],
                stream=True
            ),
            media_type="text/plain"
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )