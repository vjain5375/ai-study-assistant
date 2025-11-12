"""Streamlit Cloud entry point - redirects to main app"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main app
from ui.app import main

if __name__ == "__main__":
    main()

