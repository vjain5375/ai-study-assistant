"""Quick test to verify flashcards and quiz generation"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.flashcard import FlashcardAgent
from agents.quiz import QuizAgent

# Test text
test_text = """
Operating System (OS) is system software that manages computer hardware and software resources.
It provides common services for computer programs. The OS acts as an intermediary between programs and hardware.

Key functions of an OS include:
1. Process Management - Controls execution of processes
2. Memory Management - Manages computer memory
3. File System Management - Handles file operations
4. Device Management - Controls hardware devices
5. Security - Provides access control and protection

Types of Operating Systems:
- Batch OS: Processes jobs in batches
- Time-sharing OS: Multiple users can access simultaneously
- Real-time OS: Processes data without buffer delays
- Distributed OS: Manages resources across multiple machines
"""

print("="*60)
print("QUICK TEST: Flashcards and Quiz Generation")
print("="*60)

# Test Flashcards
print("\n1. Testing Flashcard Generation...")
try:
    flashcard_agent = FlashcardAgent()
    flashcards = flashcard_agent.generate_flashcards(test_text, num_flashcards=3)
    print(f"   SUCCESS! Generated {len(flashcards)} flashcards")
    for i, card in enumerate(flashcards[:2], 1):
        print(f"   Card {i}: Q: {card['question'][:50]}...")
except Exception as e:
    print(f"   ERROR: {str(e)}")

# Test Quiz
print("\n2. Testing Quiz Generation...")
try:
    quiz_agent = QuizAgent()
    questions = quiz_agent.generate_quiz(test_text, num_questions=2, difficulty="Medium")
    print(f"   SUCCESS! Generated {len(questions)} quiz questions")
    for i, q in enumerate(questions[:2], 1):
        print(f"   Q{i}: {q['question'][:50]}...")
except Exception as e:
    print(f"   ERROR: {str(e)}")

print("\n" + "="*60)
print("Test Complete!")
print("="*60)

