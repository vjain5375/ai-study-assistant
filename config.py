"""Configuration settings for the Study Assistant"""
import os
from dotenv import load_dotenv

load_dotenv()

# Try to load Streamlit secrets (for Streamlit Cloud)
try:
    import streamlit as st
    _streamlit_available = True
except ImportError:
    _streamlit_available = False

def get_secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit secrets or environment variables"""
    # Try Streamlit secrets first (for Streamlit Cloud)
    if _streamlit_available:
        try:
            # Check if we're in a Streamlit context
            if hasattr(st, 'secrets'):
                value = st.secrets.get(key, None)
                if value:
                    return value
        except Exception:
            pass
    
    # Fallback to environment variables
    return os.getenv(key, default)

# API Configuration
# Load from Streamlit secrets (Cloud) or environment variables (local)
# Priority: Streamlit secrets > Environment variables > .env file
GEMINI_API_KEY = get_secret("GEMINI_API_KEY", "")
GROQ_API_KEY = get_secret("GROQ_API_KEY", "")
DEEPSEEK_API_KEY = get_secret("DEEPSEEK_API_KEY", "")
# Keep OpenAI for backward compatibility (optional)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_LOCAL_MODEL = os.getenv("LOCAL_MODEL", "False").lower() == "true"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Security: Never log or expose the API key
if GEMINI_API_KEY:
    # Mask the key for any logging (only show first 7 and last 4 chars)
    _masked_key = f"{GEMINI_API_KEY[:7]}...{GEMINI_API_KEY[-4:]}" if len(GEMINI_API_KEY) > 11 else "***"
    # Don't actually log it, just have the variable available if needed for debugging

# Model Configuration - Multi-Provider Setup
# Provider-specific models
GEMINI_MODEL = "gemini-1.5-flash"  # Fast and efficient for Reader
GROQ_MODEL = "llama-3.1-70b-versatile"  # Groq LLaMA 3.1 70B for Flashcard & Planner
# Alternative Groq models: llama-3.1-8b-instant, llama-3.3-70b-versatile, mixtral-8x7b-32768
DEEPSEEK_MODEL = "DeepSeek-R1-distill-LLaMA"  # Default DeepSeek model (R1 distill)
# Alternative DeepSeek models: deepseek-chat, deepseek-reasoner

# Embedding Configuration
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"  # bge-large for FAISS embeddings
EMBEDDING_DIMENSION = 1024  # bge-large dimension

# File Paths
OUTPUT_DIR = "outputs"
UPLOAD_DIR = "uploads"
DB_PATH = "study_data.db"  # SQLite database

# Agent Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_FLASHCARDS_PER_TOPIC = 10
MAX_QUIZ_QUESTIONS_PER_TOPIC = 5

# Revision Planner Configuration
DEFAULT_REVISION_INTERVALS = [1, 3, 7, 14]  # Days between revisions

