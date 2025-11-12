"""Quiz Agent - Generates multiple-choice quizzes from study material"""
from typing import List, Dict
from utils.llm_utils import call_llm, parse_json_response
from utils.prompts import QUIZ_PROMPT
import config
import json
import os


class QuizAgent:
    """Agent responsible for generating quizzes"""
    
    def __init__(self):
        self.max_questions = config.MAX_QUIZ_QUESTIONS_PER_TOPIC
    
    def generate_quiz(self, text: str, num_questions: int = None, difficulty: str = "Medium") -> List[Dict]:
        """
        Generate quiz questions from study material.
        
        Args:
            text: Study material text
            num_questions: Number of questions to generate
            difficulty: Difficulty level (Easy, Medium, Hard)
            
        Returns:
            List of quiz question dictionaries
        """
        if num_questions is None:
            num_questions = min(self.max_questions, max(3, len(text) // 800))
        
        prompt = QUIZ_PROMPT.format(
            text=text[:4000],  # Limit text length
            num_questions=num_questions
        )
        
        # Add difficulty instruction
        prompt += f"\n\nDifficulty Level: {difficulty}. Adjust question complexity accordingly."
        
        try:
            response = call_llm(prompt)
            questions = parse_json_response(response)
            
            # Ensure it's a list
            if isinstance(questions, dict):
                questions = [questions]
            
            # Validate and format questions
            validated_questions = []
            for q in questions:
                if isinstance(q, dict) and 'question' in q and 'options' in q:
                    # Ensure correct_answer is an integer
                    correct_idx = q.get('correct_answer', 0)
                    if isinstance(correct_idx, str):
                        # Try to convert
                        try:
                            correct_idx = int(correct_idx)
                        except:
                            correct_idx = 0
                    
                    validated_questions.append({
                        "question": q['question'],
                        "options": q['options'][:4],  # Ensure exactly 4 options
                        "correct_answer": correct_idx,
                        "explanation": q.get('explanation', ''),
                        "difficulty": difficulty
                    })
            
            return validated_questions
        
        except Exception as e:
            print(f"Error generating quiz: {str(e)}")
            return []
    
    def generate_from_chunks(self, chunks: List[str], difficulty: str = "Medium") -> List[Dict]:
        """
        Generate quiz questions from multiple text chunks.
        
        Args:
            chunks: List of text chunks
            difficulty: Difficulty level
            
        Returns:
            Combined list of quiz questions
        """
        all_questions = []
        
        for i, chunk in enumerate(chunks):
            questions = self.generate_quiz(chunk, num_questions=2, difficulty=difficulty)
            for q in questions:
                q['chunk_id'] = i
            all_questions.extend(questions)
        
        return all_questions
    
    def evaluate_answer(self, question: Dict, selected_answer: int) -> Dict:
        """
        Evaluate a student's answer to a quiz question.
        
        Args:
            question: Quiz question dictionary
            selected_answer: Index of selected answer
            
        Returns:
            Evaluation result dictionary
        """
        is_correct = selected_answer == question['correct_answer']
        
        return {
            "is_correct": is_correct,
            "correct_answer": question['correct_answer'],
            "selected_answer": selected_answer,
            "explanation": question.get('explanation', '')
        }
    
    def save_quiz(self, questions: List[Dict], filename: str = "quizzes.json"):
        """
        Save quiz questions to JSON file.
        
        Args:
            questions: List of quiz questions
            filename: Output filename
        """
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
        
        filepath = os.path.join("outputs", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
    
    def load_quiz(self, filename: str = "quizzes.json") -> List[Dict]:
        """
        Load quiz questions from JSON file.
        
        Args:
            filename: Input filename
            
        Returns:
            List of quiz questions
        """
        filepath = os.path.join("outputs", filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

