"""
FastAPI Backend for AI Study Assistant
Main entry point for the API server
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes import upload, generate, search
from api.database import init_db
from config import DB_PATH

# Initialize FastAPI app
app = FastAPI(
    title="AI Study Assistant API",
    description="Backend API for PDF processing, RAG-based flashcard/quiz generation",
    version="1.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(generate.router, prefix="/api/v1", tags=["generate"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("✅ Database initialized")
    print(f"✅ API server ready at http://localhost:8000")
    print(f"📚 API docs available at http://localhost:8000/docs")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Study Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if os.path.exists(DB_PATH) else "not found"
    }


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

