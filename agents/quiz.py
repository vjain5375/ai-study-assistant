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
            # Quiz agent uses DeepSeek V3/R1 (fallback to Groq if DeepSeek fails)
            try:
                response = call_llm(prompt, provider="deepseek")
            except Exception as deepseek_error:
                error_str = str(deepseek_error)
                if "balance" in error_str.lower() or "insufficient" in error_str.lower() or "402" in error_str:
                    # Fallback to Groq
                    response = call_llm(prompt, provider="groq")
                else:
                    raise
            
            # Debug: Check response
            if not response or len(response.strip()) == 0:
                raise ValueError("Empty response from LLM")
            
            questions = parse_json_response(response)
            
            # Ensure it's a list
            if isinstance(questions, dict):
                # If it's a dict with a 'questions' key, extract that
                if 'questions' in questions:
                    questions = questions['questions']
                elif 'quiz' in questions:
                    questions = questions['quiz']
                else:
                    questions = [questions]
            
            # If still not a list, try to extract from response
            if not isinstance(questions, list):
                # Try to find array in response text
                import re
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    try:
                        questions = json.loads(json_match.group())
                    except:
                        pass
            
            # Validate and format questions
            validated_questions = []
            if isinstance(questions, list):
                for q in questions:
                    if isinstance(q, dict):
                        # Check for question in various formats
                        question_text = q.get('question') or q.get('q') or q.get('Question')
                        options = q.get('options') or q.get('Options') or q.get('choices')
                        
                        if question_text and options and isinstance(options, list) and len(options) >= 2:
                            # Ensure correct_answer is an integer
                            correct_idx = q.get('correct_answer', q.get('correctAnswer', q.get('answer', 0)))
                            if isinstance(correct_idx, str):
                                # Try to convert
                                try:
                                    correct_idx = int(correct_idx)
                                except:
                                    # Try to find index of correct answer in options
                                    correct_idx = 0
                                    for idx, opt in enumerate(options):
                                        if opt == correct_idx or str(opt).lower() == str(correct_idx).lower():
                                            correct_idx = idx
                                            break
                            
                            validated_questions.append({
                                "question": str(question_text).strip(),
                                "options": [str(opt).strip() for opt in options[:4]],  # Ensure exactly 4 options
                                "correct_answer": min(correct_idx, len(options[:4]) - 1),  # Ensure valid index
                                "explanation": str(q.get('explanation', q.get('Explanation', ''))).strip(),
                                "difficulty": difficulty
                            })
            
            if not validated_questions:
                # Last resort: try to extract from text
                raise ValueError(f"No valid questions generated. LLM response: {response[:200]}...")
            
            return validated_questions
        
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating quiz: {error_msg}")
            # Re-raise with more context
            raise Exception(f"Failed to generate quiz: {error_msg}")
    
    def generate_from_chunks(self, chunks: List[str], difficulty: str = "Medium", max_chunks: int = 3) -> List[Dict]:
        """
        Generate quiz questions from multiple text chunks.
        
        Args:
            chunks: List of text chunks
            difficulty: Difficulty level
            max_chunks: Maximum number of chunks to process (to avoid timeouts)
            
        Returns:
            Combined list of quiz questions
        """
        all_questions = []
        
        if not chunks:
            raise ValueError("No chunks provided for quiz generation")
        
        # Filter out empty or very short chunks
        valid_chunks = [chunk for chunk in chunks if chunk and len(chunk.strip()) > 100]
        
        if not valid_chunks:
            raise ValueError("No valid chunks found. Chunks must be at least 100 characters long.")
        
        # Limit chunks to avoid timeout
        chunks_to_process = valid_chunks[:max_chunks]
        
        for i, chunk in enumerate(chunks_to_process):
            try:
                # Ensure chunk has enough content
                if len(chunk.strip()) < 100:
                    continue
                    
                questions = self.generate_quiz(chunk, num_questions=2, difficulty=difficulty)
                
                if questions and len(questions) > 0:
                    for q in questions:
                        q['chunk_id'] = i
                    all_questions.extend(questions)
                else:
                    # Try with a simpler prompt if first attempt failed
                    try:
                        questions = self.generate_quiz(chunk, num_questions=1, difficulty=difficulty)
                        if questions:
                            for q in questions:
                                q['chunk_id'] = i
                            all_questions.extend(questions)
                    except:
                        pass
                        
            except Exception as e:
                error_msg = str(e)
                # Don't silently fail - log the error
                import sys
                print(f"Error processing chunk {i}: {error_msg}", file=sys.stderr)
                # Continue with next chunk
                continue
        
        if not all_questions:
            raise ValueError(f"Failed to generate quiz questions from {len(chunks_to_process)} chunks. The content might be too short or the API returned invalid responses.")
        
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

