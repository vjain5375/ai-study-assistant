# FastAPI Backend Deployment Guide

## Overview

This FastAPI backend implements a complete pipeline for PDF processing, RAG-based content generation, and vector search.

## Architecture

```
Upload PDF → Extract Text → Chunk & Label → Store in SQL → Create Embeddings → FAISS/Pinecone
                                                                                    ↓
                                                                    Generate (Flashcards/Quiz/Planner)
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key_here
# Optional: Pinecone
PINECONE_API_KEY=your_pinecone_key_here
```

### 3. Initialize Database

The database will be auto-initialized on first run, or manually:

```python
from api.database import init_db
init_db()
```

### 4. Run the API Server

```bash
# Development
python api/main.py

# Or using uvicorn directly
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Upload PDF

```bash
POST /api/v1/upload
Content-Type: multipart/form-data

# Response
{
  "status": "success",
  "file_id": 1,
  "file_name": "document.pdf",
  "num_segments": 15,
  "message": "File uploaded and processed successfully"
}
```

### Generate Artifacts

```bash
POST /api/v1/generate
Content-Type: application/json

{
  "file_id": 1,
  "artifact_type": "flashcards",  # or "quiz" or "planner"
  "num_items": 10,
  "topic_filter": "machine learning",  # optional
  "temperature": 0.3  # optional, default: 0.3 for flashcards, 0.7 for others
}

# Response
{
  "status": "success",
  "file_id": 1,
  "artifact_type": "flashcards",
  "data": [...],
  "metadata": {...}
}
```

### Semantic Search

```bash
GET /api/v1/search?query=machine+learning&file_id=1&k=5

# Response
{
  "status": "success",
  "query": "machine learning",
  "num_results": 5,
  "results": [...]
}
```

## Helper Scripts

### Process PDF

```bash
python scripts/process_pdf.py path/to/document.pdf
```

### Generate Artifacts

```bash
# Generate flashcards
python scripts/generate_artifacts.py 1 --type flashcards --num 10

# Generate quiz
python scripts/generate_artifacts.py 1 --type quiz --num 5

# Generate planner
python scripts/generate_artifacts.py 1 --type planner
```

## Testing

Run end-to-end tests:

```bash
pytest tests/test_pipeline.py -v
```

## Database Schema

### Files Table
- `id`: Primary key
- `file_name`: Original filename
- `file_path`: Storage path
- `raw_text`: Extracted text
- `uploaded_at`, `processed_at`: Timestamps

### Segments Table
- `id`: Primary key
- `file_id`: Foreign key to files
- `chunk_index`: Segment index
- `text_content`: Chunk text
- `label`: Segment label (heading, paragraph, etc.)
- `topic`: Extracted topic
- `embedding_id`: Reference to embedding

### Embeddings Table
- `id`: Primary key (embedding ID)
- `segment_id`: Foreign key to segments
- `file_id`: Foreign key to files
- `embedding_type`: 'faiss' or 'pinecone'
- `vector_index`: Index in vector store

### Artifacts Table
- `id`: Primary key
- `file_id`: Foreign key to files
- `artifact_type`: 'flashcards', 'quiz', or 'planner'
- `artifact_data`: JSON data
- `metadata`: JSON metadata

## Production Deployment

### Using Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Using Gunicorn

```bash
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Variables

- `GEMINI_API_KEY`: Required for LLM generation
- `PINECONE_API_KEY`: Optional, for Pinecone vector store
- `DB_PATH`: Database path (default: `study_data.db`)

### Scaling Considerations

- Use PostgreSQL instead of SQLite for production
- Use Pinecone or managed FAISS for vector storage
- Add Redis for caching
- Use Celery for async task processing

## Monitoring

- Health check: `GET /health`
- API metrics: Add Prometheus middleware
- Logging: Configure Python logging

## Security

- Add authentication (JWT tokens)
- Rate limiting
- Input validation
- CORS configuration for production
- API key rotation

