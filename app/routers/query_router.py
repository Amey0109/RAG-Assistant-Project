import json
import time

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.models.request_models import QueryRequest
from app.services.rag_service import is_casual_chat, prepare_rag_prompt
from app.services.ollama_service import call_ollama, call_ollama_sse


router = APIRouter(
    tags=["Query"]
)


@router.post("/query")
def query_rag(request: QueryRequest):
    try:
        total_start = time.perf_counter()

        if is_casual_chat(request.query):
            casual_prompt = f"""You are a friendly assistant for a local PDF document chat app.
            The user is casually chatting — not asking about documents.
            Reply naturally, warmly, and briefly.

            User: {request.query}
            Answer:"""
            t2 = time.perf_counter()
            answer = call_ollama(prompt=casual_prompt, stream=False)
            ollama_time = time.perf_counter() - t2
            total_time = time.perf_counter() - total_start

            return {
                "query": request.query,
                "detected_source": None,
                "chunks_used": [],
                "answer": answer,
                "timing": {
                    "rag_prepare_time_ms": 0,
                    "ollama_time_ms": round(ollama_time * 1000, 2),
                    "total_time_ms": round(total_time * 1000, 2)
                }
            }

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


@router.get("/query/stream")
def query_rag_stream_get(query: str = Query(...)):
    try:
        if is_casual_chat(query):
            casual_prompt = f"""You are a friendly assistant for a local PDF document chat app.
            The user is casually chatting — not asking about documents.
            Reply naturally, warmly, and briefly.

            User: {query}
            Answer:"""
            return StreamingResponse(
                call_ollama_sse(prompt=casual_prompt),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )

        
        rag_data = prepare_rag_prompt(query)

        return StreamingResponse(
            call_ollama_sse(
                prompt=rag_data["prompt"]
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )