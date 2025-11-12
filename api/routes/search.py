"""
Search Route - Semantic search over document segments
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.services.embedding_service import EmbeddingService
from api.database import Database

router = APIRouter()
embedding_service = EmbeddingService()
db = Database()


@router.get("/search")
async def semantic_search(
    query: str = Query(..., description="Search query"),
    file_id: Optional[int] = Query(None, description="Filter by file ID"),
    k: int = Query(5, description="Number of results to return", ge=1, le=20)
):
    """
    Perform semantic search over document segments
    
    Args:
        query: Search query text
        file_id: Optional file ID to filter results
        k: Number of results to return
        
    Returns:
        List of relevant segments with similarity scores
    """
    try:
        # Perform semantic search
        results = embedding_service.search(query=query, k=k)
        
        # Format results
        formatted_results = []
        for text, distance, metadata in results:
            result_item = {
                "text": text,
                "similarity_score": 1.0 / (1.0 + distance),  # Convert distance to similarity
                "metadata": metadata
            }
            
            # Add file info if available
            if 'file_id' in metadata:
                file_info = db.get_file(metadata['file_id'])
                if file_info:
                    result_item['file'] = {
                        "id": file_info['id'],
                        "file_name": file_info['file_name']
                    }
            
            formatted_results.append(result_item)
        
        # Filter by file_id if provided
        if file_id:
            formatted_results = [
                r for r in formatted_results
                if r.get('metadata', {}).get('file_id') == file_id
            ]
        
        return JSONResponse({
            "status": "success",
            "query": query,
            "num_results": len(formatted_results),
            "results": formatted_results
        })
    
    except Exception as e:
        print(f"❌ Error in semantic search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

