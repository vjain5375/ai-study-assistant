"""Chat/Doubt Agent - Answers questions about study material"""
from typing import List, Dict
from datetime import datetime
from utils.llm_utils import call_llm
from utils.prompts import CHAT_PROMPT
import config


class ChatAgent:
    """Agent responsible for answering questions about study material"""
    
    def __init__(self):
        self.conversation_history = []
    
    def answer_question(self, question: str, context: str, max_context_length: int = 3000) -> Dict:
        """
        Answer a student's question based on study material.
        
        Args:
            question: Student's question
            context: Relevant study material context
            max_context_length: Maximum length of context to use
            
        Returns:
            Answer dictionary
        """
        # Truncate context if too long
        if len(context) > max_context_length:
            context = context[:max_context_length] + "..."
        
        prompt = CHAT_PROMPT.format(
            context=context,
            question=question
        )
        
        try:
            answer = call_llm(prompt)
            
            # Store in conversation history
            self.conversation_history.append({
                "question": question,
                "answer": answer,
                "timestamp": str(datetime.now())
            })
            
            return {
                "answer": answer,
                "confidence": "high" if len(context) > 500 else "medium"
            }
        
        except Exception as e:
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}. Please try rephrasing your question.",
                "confidence": "low"
            }
    
    def find_relevant_context(self, question: str, chunks: List[str]) -> str:
        """
        Find the most relevant context chunks for a question.
        
        Args:
            question: Student's question
            chunks: List of text chunks
            
        Returns:
            Most relevant context string
        """
        # Simple keyword matching (can be enhanced with embeddings)
        question_lower = question.lower()
        question_words = set(question_lower.split())
        
        scored_chunks = []
        for chunk in chunks:
            chunk_lower = chunk.lower()
            # Count matching words
            score = sum(1 for word in question_words if word in chunk_lower)
            if score > 0:
                scored_chunks.append((score, chunk))
        
        # Sort by score and return top chunks
        scored_chunks.sort(reverse=True, key=lambda x: x[0])
        
        # Combine top 3 chunks
        relevant_context = "\n\n".join([chunk for _, chunk in scored_chunks[:3]])
        
        if not relevant_context:
            # Fallback: return first few chunks
            relevant_context = "\n\n".join(chunks[:2])
        
        return relevant_context
    
    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

