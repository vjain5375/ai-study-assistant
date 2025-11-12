"""
Helper Script: Generate Artifacts
Standalone script to generate flashcards/quiz/planner for a processed file
"""
import os
import sys
import argparse
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from api.database import Database
from api.services.embedding_service import EmbeddingService
from utils.llm_utils import call_llm, parse_json_response
from utils.prompts import FLASHCARD_PROMPT, QUIZ_PROMPT, PLANNER_PROMPT
from datetime import datetime
import config


def generate_flashcards(file_id: int, num_flashcards: int = 10, temperature: float = 0.3):
    """Generate flashcards for a file"""
    db = Database()
    embedding_service = EmbeddingService()
    
    # Get segments
    segments = db.get_segments(file_id)
    if not segments:
        print(f"❌ No segments found for file_id {file_id}")
        return None
    
    # Build context
    context_texts = [seg['text_content'] for seg in segments[:10]]
    context = "\n\n".join(context_texts)
    
    # Generate
    prompt = FLASHCARD_PROMPT.format(
        text=context[:4000],
        num_flashcards=num_flashcards
    )
    prompt += "\n\nIMPORTANT: Keep answers SHORT (1-2 sentences max)."
    
    print(f"🤖 Generating {num_flashcards} flashcards...")
    response = call_llm(prompt, provider="gemini", temperature=temperature)
    flashcards = parse_json_response(response)
    
    # Format
    if isinstance(flashcards, dict):
        flashcards = flashcards.get('flashcards', [flashcards])
    if not isinstance(flashcards, list):
        flashcards = []
    
    formatted = []
    for card in flashcards[:num_flashcards]:
        if isinstance(card, dict) and 'question' in card and 'answer' in card:
            formatted.append({
                "question": card['question'],
                "answer": card['answer'],
                "topic": card.get('topic', 'General')
            })
    
    # Save
    db.save_artifact(
        file_id=file_id,
        artifact_type="flashcards",
        artifact_data=formatted,
        metadata={"num_items": len(formatted), "temperature": temperature}
    )
    
    return formatted


def generate_quiz(file_id: int, num_questions: int = 5, temperature: float = 0.7):
    """Generate quiz questions for a file"""
    db = Database()
    
    # Get segments
    segments = db.get_segments(file_id)
    if not segments:
        print(f"❌ No segments found for file_id {file_id}")
        return None
    
    # Build context
    context_texts = [seg['text_content'] for seg in segments[:10]]
    context = "\n\n".join(context_texts)
    
    # Generate
    prompt = QUIZ_PROMPT.format(
        text=context[:4000],
        num_questions=num_questions
    )
    
    print(f"🤖 Generating {num_questions} quiz questions...")
    response = call_llm(prompt, provider="gemini", temperature=temperature)
    quizzes = parse_json_response(response)
    
    # Format
    if isinstance(quizzes, dict):
        quizzes = quizzes.get('questions', [quizzes])
    if not isinstance(quizzes, list):
        quizzes = []
    
    formatted = []
    for quiz in quizzes[:num_questions]:
        if isinstance(quiz, dict) and 'question' in quiz and 'options' in quiz:
            formatted.append({
                "question": quiz['question'],
                "options": quiz['options'],
                "correct_answer": quiz.get('correct_answer', 0),
                "explanation": quiz.get('explanation', ''),
                "difficulty": quiz.get('difficulty', 'Medium')
            })
    
    # Save
    db.save_artifact(
        file_id=file_id,
        artifact_type="quiz",
        artifact_data=formatted,
        metadata={"num_items": len(formatted), "temperature": temperature}
    )
    
    return formatted


def generate_planner(file_id: int, temperature: float = 0.7):
    """Generate revision plan for a file"""
    db = Database()
    
    # Get segments
    segments = db.get_segments(file_id)
    if not segments:
        print(f"❌ No segments found for file_id {file_id}")
        return None
    
    # Extract topics
    topics = list(set([seg.get('topic', 'General') for seg in segments if seg.get('topic')]))
    topics_text = ", ".join(topics[:20])
    
    # Generate
    prompt = PLANNER_PROMPT.format(
        topics=topics_text,
        current_date=datetime.now().strftime("%Y-%m-%d")
    )
    
    print(f"🤖 Generating revision plan...")
    response = call_llm(prompt, provider="gemini", temperature=temperature)
    plan = parse_json_response(response)
    
    if not isinstance(plan, dict):
        plan = {"topics": [], "total_topics": 0, "study_plan_duration": "14 days"}
    
    # Save
    db.save_artifact(
        file_id=file_id,
        artifact_type="planner",
        artifact_data=plan,
        metadata={"temperature": temperature}
    )
    
    return plan


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate artifacts for a processed file")
    parser.add_argument("file_id", type=int, help="File ID from database")
    parser.add_argument("--type", choices=["flashcards", "quiz", "planner"], 
                       required=True, help="Type of artifact to generate")
    parser.add_argument("--num", type=int, default=10, help="Number of items to generate")
    parser.add_argument("--temperature", type=float, default=None, 
                       help="Temperature (default: 0.3 for flashcards, 0.7 for others)")
    parser.add_argument("--output", help="Output JSON file path")
    
    args = parser.parse_args()
    
    # Set default temperature
    if args.temperature is None:
        args.temperature = 0.3 if args.type == "flashcards" else 0.7
    
    try:
        if args.type == "flashcards":
            result = generate_flashcards(args.file_id, args.num, args.temperature)
        elif args.type == "quiz":
            result = generate_quiz(args.file_id, args.num, args.temperature)
        elif args.type == "planner":
            result = generate_planner(args.file_id, args.temperature)
        
        if result:
            print(f"\n✅ Generated {len(result) if isinstance(result, list) else 1} items")
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"✅ Saved to {args.output}")
            else:
                print("\n" + json.dumps(result, indent=2))
        else:
            print("❌ Generation failed")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

