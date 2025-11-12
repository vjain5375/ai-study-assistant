"""Configuration settings for the Study Assistant"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
# Load from environment - never hardcode keys here
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
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
DEEPSEEK_MODEL = "deepseek-chat"  # Default DeepSeek model
# Alternative DeepSeek models: deepseek-chat, deepseek-reasoner, DeepSeek-R1-distill-LLaMA

# Embedding Configuration
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"  # bge-large for FAISS embeddings
EMBEDDING_DIMENSION = 1024  # bge-large dimension

# File Paths
OUTPUT_DIR = "outputs"
UPLOAD_DIR = "uploads"
DB_PATH = "study_data.json"

# Agent Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_FLASHCARDS_PER_TOPIC = 10
MAX_QUIZ_QUESTIONS_PER_TOPIC = 5

# Revision Planner Configuration
DEFAULT_REVISION_INTERVALS = [1, 3, 7, 14]  # Days between revisions

