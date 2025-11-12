"""
Upload Route - Handle PDF file uploads and text extraction
Enhanced with comprehensive logging and DB verification
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import os
import sys
from datetime import datetime
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.database import Database
from utils.pdf_utils import extract_text_from_pdf, clean_text
from api.services.chunking_service import ChunkingService
from api.services.embedding_service import EmbeddingService
import config

logger = logging.getLogger(__name__)

router = APIRouter()
db = Database()
chunking_service = ChunkingService()
embedding_service = EmbeddingService()

# Initialize logging
logging.basicConfig(level=logging.DEBUG)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a PDF file
    
    Pipeline:
    1. Save uploaded file
    2. Extract text
    3. Clean text
    4. Chunk into segments
    5. Store raw text and segments in database (with commit verification)
    6. Create embeddings and store in FAISS/Pinecone
    7. Return file ID and processing status
    """
    try:
        # Step 1: Validate and save file
        logger.debug(f"upload: received file size={file.size if hasattr(file, 'size') else 'unknown'} filename={file.filename}")
        
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Create uploads directory if it doesn't exist
        os.makedirs(config.UPLOAD_DIR, exist_ok=True)
        
        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{timestamp}_{file.filename}"
        file_path = os.path.join(config.UPLOAD_DIR, file_name)
        
        content = await file.read()
        file_size = len(content)
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"upload: saved file to {file_path}, size={file_size} bytes")
        
        # Step 2: Extract text from PDF
        logger.debug(f"extract: starting text extraction from {file_name}")
        raw_text = extract_text_from_pdf(file_path)
        
        if not raw_text or len(raw_text.strip()) == 0:
            raise HTTPException(status_code=400, detail="No text extracted from PDF")
        
        logger.info(f"extract: extracted {len(raw_text)} characters from PDF")
        
        # Step 3: Clean text
        cleaned_text = clean_text(raw_text)
        logger.debug(f"extract: cleaned text, final length={len(cleaned_text)} characters")
        
        # Step 4: Store file in database
        logger.debug(f"db: inserting file record for {file_name}")
        file_id = db.add_file(
            file_name=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type="pdf",
            raw_text=cleaned_text
        )
        logger.info(f"db: file stored with id={file_id}")
        
        # Step 5: Chunk text into segments
        logger.debug(f"chunk: starting chunking for file_id={file_id}")
        segments = chunking_service.chunk_text(cleaned_text, file_id=file_id)
        logger.info(f"extract: produced {len(segments)} segments for doc_id={file_id}")
        
        # Step 6: Store segments in database with commit verification
        logger.debug(f"db: inserting {len(segments)} segments for file_id={file_id}")
        inserted_count = db.add_segments(file_id, segments)
        logger.info(f"db: inserted {inserted_count} segments, commit ok, doc_id={file_id}")
        
        # Step 7: Create embeddings for segments
        logger.debug(f"embeddings: creating embeddings for {len(segments)} segments, file_id={file_id}")
        segment_texts = [seg['text_content'] for seg in segments]
        segment_metadata = [
            {
                'file_id': file_id,
                'segment_id': seg['chunk_index'],
                'topic': seg.get('topic', ''),
                'label': seg.get('label', ''),
                'chunk_index': seg['chunk_index'],
                'page_number': seg.get('page_number', 0)
            }
            for seg in segments
        ]
        embedding_ids = [f"file_{file_id}_seg_{seg['chunk_index']}" for seg in segments]
        
        embedding_service.add_vectors(
            texts=segment_texts,
            metadata=segment_metadata,
            embedding_ids=embedding_ids,
            namespace="default"
        )
        logger.info(f"embeddings: upserted {len(segments)} vectors, file_id={file_id}")
        
        return JSONResponse({
            "status": "success",
            "file_id": file_id,
            "file_name": file.filename,
            "file_size": file_size,
            "text_length": len(cleaned_text),
            "num_segments": len(segments),
            "message": "File uploaded and processed successfully"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"upload: error processing file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/files/{file_id}")
async def get_file_info(file_id: int):
    """Get file information and processing status"""
    file_info = db.get_file(file_id)
    
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    segments = db.get_segments(file_id)
    
    return {
        "file": file_info,
        "num_segments": len(segments),
        "segments": segments[:5]  # Return first 5 segments as preview
    }


@router.get("/document/{file_id}")
async def get_document(file_id: int):
    """Get document with artifacts"""
    file_info = db.get_file(file_id)
    
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    segments = db.get_segments(file_id)
    artifacts = db.get_artifacts(file_id)
    
    return {
        "file": file_info,
        "num_segments": len(segments),
        "artifacts": artifacts
    }


@router.get("/files")
async def list_files():
    """List all uploaded files"""
    # This would require adding a method to Database class
    # For now, return a simple response
    return {"message": "List files endpoint - to be implemented"}
