"""Quick test script to verify all APIs are working"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("Testing API Keys...\n")

# Test Gemini
print("1. Testing Gemini API Key...")
gemini_key = os.getenv("GEMINI_API_KEY", "")
if gemini_key:
    print(f"   OK Gemini key found: {gemini_key[:10]}...{gemini_key[-4:]}")
else:
    print("   ERROR Gemini key NOT found!")

# Test Groq
print("\n2. Testing Groq API Key...")
groq_key = os.getenv("GROQ_API_KEY", "")
if groq_key:
    print(f"   OK Groq key found: {groq_key[:10]}...{groq_key[-4:]}")
else:
    print("   ERROR Groq key NOT found!")

# Test DeepSeek
print("\n3. Testing DeepSeek API Key...")
deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
if deepseek_key:
    print(f"   OK DeepSeek key found: {deepseek_key[:10]}...{deepseek_key[-4:]}")
else:
    print("   ERROR DeepSeek key NOT found!")

# Test actual API calls
print("\n" + "="*50)
print("Testing Actual API Calls...\n")

# Test Groq
if groq_key:
    print("Testing Groq API...")
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage
        
        models_to_try = ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
        groq_works = False
        
        for model in models_to_try:
            try:
                llm = ChatGroq(model=model, groq_api_key=groq_key, temperature=0.7)
                response = llm.invoke([HumanMessage(content="Say 'Hello' in one word")])
                print(f"   OK Groq works with model: {model}")
                print(f"   Response: {response.content[:50]}")
                groq_works = True
                break
            except Exception as e:
                print(f"   WARNING Model {model} failed: {str(e)[:100]}")
                continue
        
        if not groq_works:
            print("   ERROR Groq API failed with all models!")
    except Exception as e:
        print(f"   ERROR Groq test failed: {str(e)}")

# Test DeepSeek
if deepseek_key:
    print("\nTesting DeepSeek API...")
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
        
        llm = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=deepseek_key,
            base_url="https://api.deepseek.com/v1",
            temperature=0.7
        )
        response = llm.invoke([HumanMessage(content="Say 'Hello' in one word")])
        print(f"   OK DeepSeek works!")
        print(f"   Response: {response.content[:50]}")
    except Exception as e:
        print(f"   ERROR DeepSeek test failed: {str(e)}")

print("\n" + "="*50)
print("Test Complete!")

