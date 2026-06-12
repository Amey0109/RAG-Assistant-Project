import time

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse

from app.auth.dependencies import get_current_user
from app.models.request_models import QueryRequest
from app.services.rag_service import prepare_rag_prompt, is_casual_chat
from app.services.ollama_service import call_ollama, call_ollama_sse

router = APIRouter(tags=["Query"])

CASUAL_PROMPT_TEMPLATE = """You are a friendly assistant for a local PDF document chat app.
The user is casually chatting — not asking about documents.
Reply naturally, warmly, and briefly.

User: {query}
Answer:"""


@router.post("/query")
def query_rag(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        total_start = time.perf_counter()

        if is_casual_chat(request.query):
            prompt = CASUAL_PROMPT_TEMPLATE.format(query=request.query)
            t2 = time.perf_counter()
            answer = call_ollama(prompt=prompt, stream=False)
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
        rag_data = prepare_rag_prompt(request.query, user_id=current_user["user_id"])
        rag_time = time.perf_counter() - t1

        t2 = time.perf_counter()
        answer = call_ollama(prompt=rag_data["prompt"], stream=False)
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
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/query/stream")
def query_rag_stream_get(
    query: str = Query(...),
    token: str = Query(...),        
):
    # manually verify token since SSE only sends cookies and no custom headers
    from app.services.auth_service import decode_token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    user_id = payload["sub"]
    try:
        if is_casual_chat(query):
            prompt = CASUAL_PROMPT_TEMPLATE.format(query=query)
            return StreamingResponse(
                call_ollama_sse(prompt=prompt),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )

        rag_data = prepare_rag_prompt(query, user_id=user_id)

        return StreamingResponse(
            call_ollama_sse(prompt=rag_data["prompt"]),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))