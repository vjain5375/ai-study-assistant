"""Configuration settings for the Study Assistant"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
# Load from environment - never hardcode keys here
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_LOCAL_MODEL = os.getenv("LOCAL_MODEL", "False").lower() == "true"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Security: Never log or expose the API key
if OPENAI_API_KEY:
    # Mask the key for any logging (only show first 7 and last 4 chars)
    _masked_key = f"{OPENAI_API_KEY[:7]}...{OPENAI_API_KEY[-4:]}" if len(OPENAI_API_KEY) > 11 else "***"
    # Don't actually log it, just have the variable available if needed for debugging

# Model Configuration
DEFAULT_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "text-embedding-3-small"

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

