"""Flashcard Agent - Generates Q/A flashcards from study material"""
from typing import List, Dict, Optional
from utils.llm_utils import call_llm, parse_json_response
from utils.prompts import FLASHCARD_PROMPT
from utils.database import StudyDatabase
import config
import json
import os


class FlashcardAgent:
    """Agent responsible for generating flashcards"""
    
    def __init__(self):
        self.max_flashcards = config.MAX_FLASHCARDS_PER_TOPIC
        self.db = StudyDatabase()
    
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
        
        # Add instruction for short sticky-note style
        prompt += "\n\nIMPORTANT: Keep answers SHORT (1-2 sentences max). Think sticky notes, not essays! Focus on key points only."
        
        try:
            # Flashcard agent uses Groq LLaMA 3.1 70B
            response = call_llm(prompt, provider="groq")
            
            # Debug: Print response for troubleshooting
            if not response or len(response.strip()) == 0:
                raise ValueError("Empty response from LLM")
            
            print(f"📥 LLM Response length: {len(response)} characters")
            print(f"📥 LLM Response preview: {response[:200]}...")
            print(f"📥 LLM Full Response: {response}")
            
            flashcards = parse_json_response(response)
            
            print(f"📊 Parsed flashcards: {len(flashcards) if isinstance(flashcards, list) else 'Not a list'}")
            print(f"📊 Parsed type: {type(flashcards)}")
            
            # Ensure it's a list
            if isinstance(flashcards, dict):
                # If it's a dict with a 'flashcards' key, extract that
                if 'flashcards' in flashcards:
                    flashcards = flashcards['flashcards']
                elif 'questions' in flashcards:
                    flashcards = flashcards['questions']
                else:
                    flashcards = [flashcards]
            
            # If still not a list, try to extract from response
            if not isinstance(flashcards, list):
                print("⚠️ Response is not a list, trying to extract JSON array...")
                print(f"⚠️ Current flashcards type: {type(flashcards)}")
                print(f"⚠️ Current flashcards value: {flashcards}")
                
                # Try to find array in response text
                import re
                
                # First, try to find a JSON array
                json_match = re.search(r'\[[\s\S]*?\]', response, re.DOTALL)
                if json_match:
                    try:
                        extracted = json.loads(json_match.group())
                        if isinstance(extracted, list):
                            flashcards = extracted
                            print(f"✅ Extracted {len(flashcards)} flashcards from JSON array")
                    except Exception as parse_error:
                        print(f"❌ Failed to parse JSON array: {str(parse_error)}")
                        print(f"❌ Matched text: {json_match.group()[:200]}...")
                
                # If still not a list, try to find individual objects
                if not isinstance(flashcards, list):
                    try:
                        # Look for objects with question/answer
                        obj_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*"question"(?:[^{}]|(?:\{[^{}]*\}))*"answer"(?:[^{}]|(?:\{[^{}]*\}))*\}'
                        obj_matches = re.findall(obj_pattern, response, re.DOTALL)
                        if obj_matches:
                            flashcards = []
                            for match in obj_matches:
                                try:
                                    parsed_obj = json.loads(match)
                                    if isinstance(parsed_obj, dict) and 'question' in parsed_obj and 'answer' in parsed_obj:
                                        flashcards.append(parsed_obj)
                                except:
                                    pass
                            if flashcards:
                                print(f"✅ Extracted {len(flashcards)} flashcards from individual objects")
                    except Exception as obj_error:
                        print(f"❌ Failed to extract objects: {str(obj_error)}")
            
            # Validate flashcards
            validated_flashcards = []
            if isinstance(flashcards, list):
                for card in flashcards:
                    if isinstance(card, dict):
                        # Check for question/answer in various formats
                        question = card.get('question') or card.get('q') or card.get('Question')
                        answer = card.get('answer') or card.get('a') or card.get('Answer')
                        
                        if question and answer:
                            validated_flashcards.append({
                                "question": str(question).strip(),
                                "answer": str(answer).strip(),
                                "topic": card.get('topic', card.get('Topic', 'General'))
                            })
            
            if not validated_flashcards:
                # Last resort: try to extract Q/A pairs from text
                print(f"❌ No validated flashcards. Raw response: {response}")
                print(f"❌ Parsed flashcards type: {type(flashcards)}, value: {flashcards}")
                raise ValueError(f"No valid flashcards generated. LLM response length: {len(response)} chars. Preview: {response[:500]}...")
            
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
        
        if not chunks:
            raise ValueError("No chunks provided for flashcard generation")
        
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
                    print(f"Skipping chunk {i}: too short ({len(chunk.strip())} chars)")
                    continue
                
                # Debug: Print chunk info
                print(f"Processing chunk {i+1}/{len(chunks_to_process)}: {len(chunk)} characters")
                print(f"Chunk preview: {chunk[:100]}...")
                
                try:
                    flashcards = self.generate_flashcards(chunk, num_flashcards=3)
                    
                    if flashcards and len(flashcards) > 0:
                        print(f"✅ Generated {len(flashcards)} flashcards from chunk {i+1}")
                        for card in flashcards:
                            card['chunk_id'] = i
                        all_flashcards.extend(flashcards)
                    else:
                        print(f"⚠️ No flashcards from chunk {i+1}, trying with fewer cards...")
                        # Try with a simpler prompt if first attempt failed
                        try:
                            flashcards = self.generate_flashcards(chunk, num_flashcards=2)
                            if flashcards and len(flashcards) > 0:
                                print(f"✅ Generated {len(flashcards)} flashcards from chunk {i+1} (retry)")
                                for card in flashcards:
                                    card['chunk_id'] = i
                                all_flashcards.extend(flashcards)
                            else:
                                print(f"❌ Still no flashcards from chunk {i+1} after retry")
                        except Exception as retry_error:
                            print(f"❌ Retry failed for chunk {i+1}: {str(retry_error)}")
                except Exception as gen_error:
                    print(f"❌ Error generating flashcards from chunk {i+1}: {str(gen_error)}")
                    # Try one more time with a very simple request
                    try:
                        flashcards = self.generate_flashcards(chunk, num_flashcards=1)
                        if flashcards and len(flashcards) > 0:
                            print(f"✅ Generated {len(flashcards)} flashcard from chunk {i+1} (final retry)")
                            for card in flashcards:
                                card['chunk_id'] = i
                            all_flashcards.extend(flashcards)
                    except:
                        pass
                        
            except Exception as e:
                error_msg = str(e)
                # Don't silently fail - log the error
                import sys
                print(f"Error processing chunk {i}: {error_msg}", file=sys.stderr)
                # Continue with next chunk
                continue
        
        if not all_flashcards:
            raise ValueError(f"Failed to generate flashcards from {len(chunks_to_process)} chunks. The content might be too short or the API returned invalid responses.")
        
        return all_flashcards
    
    def save_flashcards(self, flashcards: List[Dict], file_id: Optional[int] = None, filename: str = "flashcards.json"):
        """
        Save flashcards to database and JSON file (for backup).
        
        Args:
            flashcards: List of flashcards
            file_id: Database file ID (optional)
            filename: Output filename for JSON backup
        """
        # Save to SQLite database if file_id provided
        if file_id:
            self.db.save_flashcards(file_id, flashcards)
        
        # Also save to JSON for backup/compatibility
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
        
        filepath = os.path.join("outputs", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(flashcards, f, indent=2, ensure_ascii=False)
    
    def load_flashcards(self, file_id: Optional[int] = None, filename: str = "flashcards.json") -> List[Dict]:
        """
        Load flashcards from database or JSON file.
        
        Args:
            file_id: Database file ID (optional, if provided loads from DB)
            filename: Input filename for JSON fallback
            
        Returns:
            List of flashcards
        """
        # Try database first if file_id provided
        if file_id:
            db_flashcards = self.db.get_flashcards(file_id)
            if db_flashcards:
                return db_flashcards
        
        # Fallback to JSON
        filepath = os.path.join("outputs", filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

