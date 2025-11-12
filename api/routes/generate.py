"""
Generate Route - RAG-based flashcard/quiz/planner generation
Enhanced with proper RAG context retrieval and LLM output validation
"""
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Literal
import os
import sys
import json
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.database import Database
from api.services.embedding_service import EmbeddingService
from utils.llm_utils import call_llm, parse_json_response
from utils.prompts import FLASHCARD_PROMPT, QUIZ_PROMPT, PLANNER_PROMPT
import config
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()
db = Database()
embedding_service = EmbeddingService()


class GenerateRequest(BaseModel):
    """Request model for generation endpoint"""
    file_id: int
    artifact_type: Literal["flashcards", "quiz", "planner"]
    num_items: Optional[int] = None
    topic_filter: Optional[str] = None
    temperature: Optional[float] = None


@router.post("/generate")
async def generate_artifacts(request: GenerateRequest):
    """
    Generate flashcards, quizzes, or revision plans using RAG
    
    Pipeline:
    1. Verify file and segments exist
    2. Retrieve relevant segments using semantic search (RAG)
    3. Build context from retrieved segment texts
    4. Use LLM with RAG prompt to generate artifacts
    5. Parse and validate JSON response
    6. Store artifacts in database with commit verification
    7. Return structured JSON
    """
    try:
        # Step 1: Validate file exists
        logger.debug(f"generate: starting generation for file_id={request.file_id}, type={request.artifact_type}")
        file_info = db.get_file(request.file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Step 2: Get segments for the file
        segments = db.get_segments(request.file_id)
        if not segments:
            raise HTTPException(status_code=400, detail="No segments found for this file. Please upload and process the file first.")
        
        logger.debug(f"generate: found {len(segments)} segments for file_id={request.file_id}")
        
        # Step 3: Determine temperature (deterministic for flashcards)
        temperature = request.temperature
        if temperature is None:
            if request.artifact_type == "flashcards":
                temperature = 0.0  # Fully deterministic for flashcards
            else:
                temperature = 0.7
        
        # Step 4: Retrieve context using RAG
        logger.debug(f"retrieval: retrieving context for file_id={request.file_id}, topic_filter={request.topic_filter}")
        retrieved_segments = embedding_service.retrieve_context(
            file_id=request.file_id,
            query=request.topic_filter,
            top_k=6,
            namespace="default"
        )
        
        if not retrieved_segments:
            # Fallback to direct segment access
            logger.warning(f"retrieval: no segments retrieved, using direct access")
            retrieved_segments = [
                {
                    'text': seg['text_content'],
                    'segment_id': seg.get('id'),
                    'chunk_index': seg.get('chunk_index', 0),
                    'topic': seg.get('topic', '')
                }
                for seg in segments[:6]
            ]
        
        logger.info(f"retrieval: top_k=6 returned {len(retrieved_segments)} segments for file_id={request.file_id}")
        
        # Step 5: Build context text from retrieved segments
        context_parts = []
        for seg in retrieved_segments:
            text = seg.get('text', '')
            chunk_idx = seg.get('chunk_index', 0)
            topic = seg.get('topic', 'General')
            # Truncate each segment to avoid token limits
            truncated_text = text[:2000] if len(text) > 2000 else text
            context_parts.append(f"PAGE {seg.get('page_number', 0)} SEG {chunk_idx} [{topic}]: {truncated_text}")
        
        context = "\n\n".join(context_parts)
        logger.debug(f"llm: constructed context with {len(context)} characters from {len(retrieved_segments)} segments")
        
        # Step 6: Generate artifacts based on type
        if request.artifact_type == "flashcards":
            result = _generate_flashcards(
                context=context,
                num_flashcards=request.num_items or 10,
                temperature=temperature,
                file_id=request.file_id
            )
        elif request.artifact_type == "quiz":
            result = _generate_quiz(
                context=context,
                num_questions=request.num_items or 5,
                temperature=temperature,
                file_id=request.file_id
            )
        elif request.artifact_type == "planner":
            result = _generate_planner(
                segments=segments,
                temperature=temperature,
                file_id=request.file_id
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid artifact_type")
        
        # Step 7: Store artifacts in database with commit verification
        logger.debug(f"db: saving artifact for file_id={request.file_id}, type={request.artifact_type}")
        artifact_id = db.save_artifact(
            file_id=request.file_id,
            artifact_type=request.artifact_type,
            artifact_data=result,
            metadata={
                "num_items": request.num_items,
                "topic_filter": request.topic_filter,
                "temperature": temperature,
                "generated_at": datetime.now().isoformat(),
                "num_segments_used": len(retrieved_segments)
            }
        )
        logger.info(f"db: artifact saved with id={artifact_id}, file_id={request.file_id}")
        
        return JSONResponse({
            "status": "success",
            "file_id": request.file_id,
            "artifact_id": artifact_id,
            "artifact_type": request.artifact_type,
            "data": result,
            "metadata": {
                "num_items": len(result) if isinstance(result, list) else 1,
                "temperature": temperature,
                "segments_used": len(retrieved_segments)
            }
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"generate: error generating artifacts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating artifacts: {str(e)}")


def _generate_flashcards(context: str, num_flashcards: int, temperature: float, file_id: int) -> List[Dict]:
    """Generate flashcards using LLM with JSON validation and retry"""
    logger.debug(f"llm: generating {num_flashcards} flashcards, temperature={temperature}, context_length={len(context)}")
    
    # Build prompt with explicit JSON-only instruction
    prompt = f"""You are an educational assistant. Use only the CONTEXT below. Respond with VALID JSON ONLY.

Context:
{context[:4000]}

Instructions: Create exactly {num_flashcards} flashcards in this JSON format:
[{{"id": "", "topic": "", "question": "", "answer": "", "difficulty": "", "source": {{"doc_id": {file_id}, "segment_id": ""}}}}]

CRITICAL: Return ONLY a valid JSON array. No markdown, no code blocks, no explanations. Start with [ and end with ]."""
    
    # Add deterministic instruction
    prompt += "\n\nIMPORTANT: Keep answers SHORT (1-2 sentences max). Focus on key points only."
    
    try:
        # First attempt
        logger.debug(f"llm: calling LLM with prompt length={len(prompt)} characters")
        response = call_llm(prompt, provider="gemini", temperature=temperature)
        logger.debug(f"llm: prompt length={len(prompt)} tokens (approx); response length={len(response)} characters")
        
        # Parse JSON
        flashcards = parse_json_response(response)
        
        # Validate format
        if isinstance(flashcards, dict):
            if 'flashcards' in flashcards:
                flashcards = flashcards['flashcards']
            else:
                flashcards = [flashcards]
        
        if not isinstance(flashcards, list):
            raise ValueError("Response is not a JSON array")
        
        # Format and validate
        formatted_flashcards = []
        for card in flashcards[:num_flashcards]:
            if isinstance(card, dict) and 'question' in card and 'answer' in card:
                formatted_flashcards.append({
                    "id": card.get('id', f"fc_{len(formatted_flashcards)}"),
                    "question": card['question'],
                    "answer": card['answer'],
                    "topic": card.get('topic', 'General'),
                    "difficulty": card.get('difficulty', 'Medium'),
                    "source": card.get('source', {'doc_id': file_id})
                })
        
        logger.info(f"llm: successfully generated {len(formatted_flashcards)} flashcards")
        return formatted_flashcards
        
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"llm: invalid JSON on first attempt, raw output: {response[:500]}")
        
        # Retry with temperature=0.0 and stricter instruction
        logger.debug("llm: retrying with temperature=0.0")
        retry_prompt = prompt + "\n\nRespond with JSON only (no commentary, no markdown)."
        response = call_llm(retry_prompt, provider="gemini", temperature=0.0)
        
        try:
            flashcards = parse_json_response(response)
            if isinstance(flashcards, dict):
                flashcards = flashcards.get('flashcards', [flashcards])
            if not isinstance(flashcards, list):
                raise ValueError("Retry response is not a JSON array")
            
            formatted_flashcards = []
            for card in flashcards[:num_flashcards]:
                if isinstance(card, dict) and 'question' in card and 'answer' in card:
                    formatted_flashcards.append({
                        "id": card.get('id', f"fc_{len(formatted_flashcards)}"),
                        "question": card['question'],
                        "answer": card['answer'],
                        "topic": card.get('topic', 'General'),
                        "difficulty": card.get('difficulty', 'Medium'),
                        "source": card.get('source', {'doc_id': file_id})
                    })
            
            logger.info(f"llm: successfully generated {len(formatted_flashcards)} flashcards on retry")
            return formatted_flashcards
            
        except Exception as retry_error:
            logger.error(f"llm: retry also failed: {str(retry_error)}, raw output: {response[:500]}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate valid JSON. LLM output: {response[:200]}"
            )


def _generate_quiz(context: str, num_questions: int, temperature: float, file_id: int) -> List[Dict]:
    """Generate quiz questions using LLM with JSON validation"""
    logger.debug(f"llm: generating {num_questions} quiz questions, temperature={temperature}")
    
    prompt = f"""You are an educational assistant. Use only the CONTEXT below. Respond with VALID JSON ONLY.

Context:
{context[:4000]}

Instructions: Create exactly {num_questions} multiple-choice questions in this JSON format:
[{{"id": "", "question": "", "options": ["A", "B", "C", "D"], "correct_answer": 0, "explanation": "", "difficulty": ""}}]

CRITICAL: Return ONLY a valid JSON array. No markdown, no code blocks."""
    
    try:
        response = call_llm(prompt, provider="gemini", temperature=temperature)
        quizzes = parse_json_response(response)
        
        if isinstance(quizzes, dict):
            quizzes = quizzes.get('questions', [quizzes])
        if not isinstance(quizzes, list):
            raise ValueError("Response is not a JSON array")
        
        formatted_quizzes = []
        for quiz in quizzes[:num_questions]:
            if isinstance(quiz, dict) and 'question' in quiz and 'options' in quiz:
                formatted_quizzes.append({
                    "id": quiz.get('id', f"qz_{len(formatted_quizzes)}"),
                    "question": quiz['question'],
                    "options": quiz['options'],
                    "correct_answer": quiz.get('correct_answer', 0),
                    "explanation": quiz.get('explanation', ''),
                    "difficulty": quiz.get('difficulty', 'Medium'),
                    "source": {'doc_id': file_id}
                })
        
        logger.info(f"llm: successfully generated {len(formatted_quizzes)} quiz questions")
        return formatted_quizzes
        
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"llm: invalid JSON for quiz, raw output: {response[:500]}")
        # Retry with temperature=0.0
        response = call_llm(prompt + "\n\nRespond with JSON only.", provider="gemini", temperature=0.0)
        quizzes = parse_json_response(response)
        if isinstance(quizzes, dict):
            quizzes = quizzes.get('questions', [quizzes])
        if not isinstance(quizzes, list):
            raise HTTPException(status_code=500, detail=f"Failed to generate valid quiz JSON: {str(e)}")
        
        formatted_quizzes = []
        for quiz in quizzes[:num_questions]:
            if isinstance(quiz, dict) and 'question' in quiz and 'options' in quiz:
                formatted_quizzes.append({
                    "id": quiz.get('id', f"qz_{len(formatted_quizzes)}"),
                    "question": quiz['question'],
                    "options": quiz['options'],
                    "correct_answer": quiz.get('correct_answer', 0),
                    "explanation": quiz.get('explanation', ''),
                    "difficulty": quiz.get('difficulty', 'Medium'),
                    "source": {'doc_id': file_id}
                })
        
        return formatted_quizzes


def _generate_planner(segments: List[Dict], temperature: float, file_id: int) -> Dict:
    """Generate revision plan using LLM"""
    # Extract topics from segments
    topics = list(set([seg.get('topic', 'General') for seg in segments if seg.get('topic')]))
    topics_text = ", ".join(topics[:20])  # Limit topics
    
    prompt = PLANNER_PROMPT.format(
        topics=topics_text,
        current_date=datetime.now().strftime("%Y-%m-%d")
    )
    
    response = call_llm(prompt, provider="gemini", temperature=temperature)
    plan = parse_json_response(response)
    
    # Ensure it's a dict
    if not isinstance(plan, dict):
        plan = {"topics": [], "total_topics": 0, "study_plan_duration": "14 days"}
    
    return plan
