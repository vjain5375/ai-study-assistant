"""Quick test to verify LLM calls are working"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from utils.llm_utils import call_llm
import config

def test_llm_calls():
    """Test if LLM calls are working"""
    print("="*60)
    print("Testing LLM Calls")
    print("="*60)
    
    # Check API keys
    print("\nAPI Key Status:")
    print(f"   GEMINI_API_KEY: {'Set' if config.GEMINI_API_KEY else 'Missing'}")
    print(f"   GROQ_API_KEY: {'Set' if config.GROQ_API_KEY else 'Missing'}")
    print(f"   DEEPSEEK_API_KEY: {'Set' if config.DEEPSEEK_API_KEY else 'Missing'}")
    
    # Test prompt
    test_prompt = """Create 2 short flashcards from this text:
    
Operating systems manage computer resources. They provide interfaces between hardware and software.

Return ONLY a JSON array:
[{"question": "What is X?", "answer": "X is Y."}]
"""
    
    # Test Gemini
    print("\n" + "="*60)
    print("Testing Gemini...")
    print("="*60)
    try:
        response = call_llm(test_prompt, provider="gemini")
        print(f"Gemini Success!")
        print(f"   Response length: {len(response)} characters")
        print(f"   Response preview: {response[:200]}...")
    except Exception as e:
        print(f"Gemini Failed: {str(e)}")
    
    # Test Groq
    print("\n" + "="*60)
    print("Testing Groq...")
    print("="*60)
    try:
        response = call_llm(test_prompt, provider="groq")
        print(f"Groq Success!")
        print(f"   Response length: {len(response)} characters")
        print(f"   Response preview: {response[:200]}...")
    except Exception as e:
        print(f"Groq Failed: {str(e)}")
    
    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)

if __name__ == "__main__":
    test_llm_calls()

