from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.timing_middleware import add_timing_middleware
from app.routers.document_router import router as document_router
from app.routers.query_router import router as query_router


app = FastAPI(
    title="Local PDF RAG Assistant API",
    description="FastAPI backend for PDF upload, ChromaDB embeddings, and Ollama-based RAG answers.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "null"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_timing_middleware(app)

app.include_router(document_router)
app.include_router(query_router)



@app.get("/")
def home():
    return {
        "message": "Local PDF RAG Assistant API is running.",
        "swagger_docs": "/docs",
        "redoc": "/redoc"
    }