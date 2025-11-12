"""Reader Agent - Extracts and structures content from study materials"""
from typing import Dict, List
from utils.pdf_utils import extract_text_from_uploaded_file, clean_text, split_into_chunks
from utils.llm_utils import call_llm, parse_json_response
import config


class ReaderAgent:
    """Agent responsible for reading and extracting content from study materials"""
    
    def __init__(self):
        self.chunk_size = config.CHUNK_SIZE
        self.chunk_overlap = config.CHUNK_OVERLAP
    
    def process_file(self, uploaded_file) -> Dict:
        """
        Process uploaded file and extract structured content.
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Dictionary with extracted content and metadata
        """
        # Extract raw text
        raw_text = extract_text_from_uploaded_file(uploaded_file)
        
        # Clean text
        cleaned_text = clean_text(raw_text)
        
        # Split into chunks
        chunks = split_into_chunks(
            cleaned_text,
            chunk_size=self.chunk_size,
            overlap=self.chunk_overlap
        )
        
        # Identify topics
        topics = self._identify_topics(cleaned_text)
        
        return {
            "raw_text": cleaned_text,
            "chunks": chunks,
            "topics": topics,
            "num_chunks": len(chunks),
            "file_name": uploaded_file.name,
            "file_size": len(cleaned_text)
        }
    
    def _identify_topics(self, text: str) -> List[Dict]:
        """
        Identify main topics from the text.
        
        Args:
            text: Cleaned text content
            
        Returns:
            List of identified topics
        """
        prompt = f"""Analyze the following study material and identify the main topics and subtopics.

Study Material:
{text[:3000]}  # Limit to first 3000 chars for topic identification

Return a JSON array of topics in this format:
[
  {{
    "topic": "Topic Name",
    "subtopics": ["Subtopic 1", "Subtopic 2"],
    "key_concepts": ["Concept 1", "Concept 2"]
  }}
]

Only return the JSON array."""
        
        try:
            response = call_llm(prompt)
            topics = parse_json_response(response)
            return topics if isinstance(topics, list) else []
        except Exception as e:
            # Fallback: simple topic extraction
            return self._simple_topic_extraction(text)
    
    def _simple_topic_extraction(self, text: str) -> List[Dict]:
        """Fallback method for topic extraction"""
        # Look for headings (lines in ALL CAPS or with numbers)
        lines = text.split('\n')
        topics = []
        
        for line in lines[:50]:  # Check first 50 lines
            line = line.strip()
            if len(line) > 5 and len(line) < 100:
                # Check if it looks like a heading
                if (line.isupper() or 
                    line.startswith(('Chapter', 'Unit', 'Section', 'Topic')) or
                    any(char.isdigit() for char in line[:5])):
                    topics.append({
                        "topic": line,
                        "subtopics": [],
                        "key_concepts": []
                    })
        
        return topics[:10]  # Limit to 10 topics

