"""
Document Processing & Retrieval System - FastAPI Backend
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
import uvicorn

from api.search_routes import router as search_router
from api.pdf_routes import router as pdf_router
from api.metadata_routes import router as metadata_router

app = FastAPI(
    title="Document Retrieval System",
    description="Full-text search over OCR-processed books with PDF page rendering",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router, prefix="/api/search", tags=["Search"])
app.include_router(pdf_router, prefix="/api/pdf", tags=["PDF"])
app.include_router(metadata_router, prefix="/api/metadata", tags=["Metadata"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Document Retrieval System is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
