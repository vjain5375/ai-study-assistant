"""
Chunking and Labeling Service
Splits text into segments and labels them with topics
"""
from typing import List, Dict, Optional
import re
from utils.pdf_utils import split_into_chunks
import config


class ChunkingService:
    """Service for chunking text and labeling segments"""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize chunking service
        
        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP
    
    def chunk_text(self, text: str, file_id: int = None) -> List[Dict]:
        """
        Split text into chunks with metadata
        
        Args:
            text: Text to chunk
            file_id: Optional file ID for tracking
            
        Returns:
            List of chunk dictionaries with metadata
        """
        chunks = split_into_chunks(text, self.chunk_size, self.chunk_overlap)
        
        segments = []
        current_pos = 0
        
        for idx, chunk in enumerate(chunks):
            start_char = current_pos
            end_char = current_pos + len(chunk)
            
            # Extract potential topic/label from chunk
            label = self._extract_label(chunk)
            topic = self._extract_topic(chunk)
            
            segments.append({
                'chunk_index': idx,
                'text_content': chunk,
                'label': label,
                'topic': topic,
                'start_char': start_char,
                'end_char': end_char,
                'page_number': 0  # Will be updated if page info available
            })
            
            current_pos = end_char - self.chunk_overlap
        
        return segments
    
    def _extract_label(self, text: str) -> str:
        """
        Extract a label for the chunk (e.g., heading, paragraph, list)
        
        Args:
            text: Chunk text
            
        Returns:
            Label string
        """
        text_lower = text.lower().strip()
        
        # Check for headings (lines that are short and end with colon or are all caps)
        lines = text.split('\n')
        first_line = lines[0].strip() if lines else ""
        
        if len(first_line) < 100 and (first_line.endswith(':') or first_line.isupper()):
            return "heading"
        
        # Check for lists
        if re.match(r'^\s*[-*•]\s+', text) or re.match(r'^\s*\d+[.)]\s+', text):
            return "list"
        
        # Check for code blocks
        if '```' in text or 'def ' in text or 'class ' in text:
            return "code"
        
        # Default to paragraph
        return "paragraph"
    
    def _extract_topic(self, text: str) -> str:
        """
        Extract topic from chunk (simple keyword-based extraction)
        
        Args:
            text: Chunk text
            
        Returns:
            Topic string
        """
        # Look for common topic indicators
        lines = text.split('\n')
        first_line = lines[0].strip() if lines else ""
        
        # If first line looks like a heading, use it as topic
        if len(first_line) < 100 and (first_line.endswith(':') or first_line.isupper()):
            return first_line.replace(':', '').strip()
        
        # Extract keywords (simple approach - can be enhanced with NLP)
        keywords = ['introduction', 'conclusion', 'summary', 'example', 'definition', 
                   'theory', 'method', 'result', 'analysis', 'discussion']
        
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                return keyword.capitalize()
        
        return "General"
    
    def label_segments_with_llm(self, segments: List[Dict], llm_call_fn) -> List[Dict]:
        """
        Use LLM to label segments with topics (optional enhancement)
        
        Args:
            segments: List of segment dictionaries
            llm_call_fn: Function to call LLM
            
        Returns:
            List of segments with enhanced labels
        """
        # This is an optional enhancement - for now, return segments as-is
        # Can be implemented to use LLM for better topic extraction
        return segments

