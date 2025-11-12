# 🔑 API Keys & Models Explained

## ✅ What You Have (API Keys - Cloud Services)

These 3 API keys are **sufficient for all LLM agents**:

1. **Gemini API Key** → Reader Agent
2. **Groq API Key** → Flashcard & Planner Agents  
3. **DeepSeek API Key** → Quiz & Chat Agents

**No additional API keys needed for LLM functionality!**

## 📦 What Gets Downloaded (Hugging Face Models - Free)

The **bge-large embedding model** is used for **FAISS semantic search** (Chat Agent):

- **Model**: `BAAI/bge-large-en-v1.5` (~1.3GB)
- **Source**: Hugging Face (free, no API key needed)
- **Purpose**: Converts text to vectors for semantic search
- **When**: Automatically downloaded on first run via `sentence-transformers`

### Do You Need a Hugging Face Account?

**NO!** You don't need:
- ❌ Hugging Face API key
- ❌ Hugging Face account
- ❌ Manual model download

The model downloads automatically when you run:
```powershell
pip install -r requirements.txt
```

Then on first use, `sentence-transformers` downloads it from Hugging Face automatically.

## 🔄 Fallback Option

If the large model fails to download, the code automatically falls back to:
- **Fallback Model**: `all-MiniLM-L6-v2` (~80MB, much smaller)
- **Works the same way**, just slightly less accurate embeddings

## 📊 Summary

| Component | Type | Required? | Source |
|-----------|------|-----------|--------|
| Gemini API | Cloud API | ✅ Yes | Google (your API key) |
| Groq API | Cloud API | ✅ Yes | Groq (your API key) |
| DeepSeek API | Cloud API | ✅ Yes | DeepSeek (your API key) |
| bge-large Model | Local Model | ⚠️ Optional | Hugging Face (auto-download, free) |

## 🎯 Bottom Line

**Your 3 API keys are sufficient!**

The Hugging Face model is:
- ✅ Free (no cost)
- ✅ Automatic (downloads itself)
- ✅ Optional (has fallback)
- ✅ No account needed

Just run `pip install -r requirements.txt` and everything will work!

## 🚀 Alternative: Skip Embeddings (Simpler Setup)

If you want to avoid downloading the large model, we can modify the Chat Agent to use simple keyword matching instead of FAISS. This would:
- ✅ Work with just your 3 API keys
- ✅ No model downloads needed
- ⚠️ Less accurate semantic search (but still functional)

Would you like me to add this option?

