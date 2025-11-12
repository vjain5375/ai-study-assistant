"""Flashcard Agent - Generates Q/A flashcards from study material"""
from typing import List, Dict
from utils.llm_utils import call_llm, parse_json_response
from utils.prompts import FLASHCARD_PROMPT
import config
import json
import os


class FlashcardAgent:
    """Agent responsible for generating flashcards"""
    
    def __init__(self):
        self.max_flashcards = config.MAX_FLASHCARDS_PER_TOPIC
    
    def generate_flashcards(self, text: str, num_flashcards: int = None) -> List[Dict]:
        """
        Generate flashcards from study material.
        
        Args:
            text: Study material text
            num_flashcards: Number of flashcards to generate
            
        Returns:
            List of flashcard dictionaries
        """
        if num_flashcards is None:
            num_flashcards = min(self.max_flashcards, max(5, len(text) // 500))
        
        prompt = FLASHCARD_PROMPT.format(
            text=text[:4000],  # Limit text length
            num_flashcards=num_flashcards
        )
        
        try:
            # Flashcard agent uses Groq LLaMA 3.1 70B
            response = call_llm(prompt, provider="groq")
            
            # Debug: Print response for troubleshooting
            if not response or len(response.strip()) == 0:
                raise ValueError("Empty response from LLM")
            
            flashcards = parse_json_response(response)
            
            # Ensure it's a list
            if isinstance(flashcards, dict):
                flashcards = [flashcards]
            
            # Validate flashcards
            validated_flashcards = []
            for card in flashcards:
                if isinstance(card, dict) and 'question' in card and 'answer' in card:
                    validated_flashcards.append({
                        "question": card['question'],
                        "answer": card['answer'],
                        "topic": card.get('topic', 'General')
                    })
            
            if not validated_flashcards:
                raise ValueError("No valid flashcards generated from response")
            
            return validated_flashcards
        
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating flashcards: {error_msg}")
            # Re-raise with more context
            raise Exception(f"Failed to generate flashcards: {error_msg}")
    
    def generate_from_chunks(self, chunks: List[str], max_chunks: int = 5) -> List[Dict]:
        """
        Generate flashcards from multiple text chunks.
        
        Args:
            chunks: List of text chunks
            max_chunks: Maximum number of chunks to process (to avoid timeouts)
            
        Returns:
            Combined list of flashcards
        """
        all_flashcards = []
        
        # Limit chunks to avoid timeout
        chunks_to_process = chunks[:max_chunks]
        
        for i, chunk in enumerate(chunks_to_process):
            try:
                flashcards = self.generate_flashcards(chunk, num_flashcards=3)
                for card in flashcards:
                    card['chunk_id'] = i
                all_flashcards.extend(flashcards)
            except Exception as e:
                print(f"Error processing chunk {i}: {str(e)}")
                continue  # Skip this chunk and continue
        
        return all_flashcards
    
    def save_flashcards(self, flashcards: List[Dict], filename: str = "flashcards.json"):
        """
        Save flashcards to JSON file.
        
        Args:
            flashcards: List of flashcards
            filename: Output filename
        """
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
        
        filepath = os.path.join("outputs", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(flashcards, f, indent=2, ensure_ascii=False)
    
    def load_flashcards(self, filename: str = "flashcards.json") -> List[Dict]:
        """
        Load flashcards from JSON file.
        
        Args:
            filename: Input filename
            
        Returns:
            List of flashcards
        """
        filepath = os.path.join("outputs", filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

