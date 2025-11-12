# Streamlit Cloud Deployment Guide

## 🚀 Deployment Configuration

### Required Settings for Streamlit Cloud:

1. **Repository**: `vjain5375/ai-study-assistant` ✅

2. **Branch**: `main` ✅

3. **Main file path**: `ui/app.py` ⚠️ (NOT `foo/bar/streamlit_app.py`)

4. **App URL** (optional): Leave empty or choose a custom name like `ai-study-assistant`

## 🔑 Setting Up API Keys in Streamlit Cloud Secrets

### Step-by-Step Instructions:

1. **Go to Streamlit Cloud**: https://share.streamlit.io/
2. **Click "New app"** or select your existing app
3. **Click "Advanced settings"** in the deployment form
4. **Click "Secrets"** tab
5. **Add all three API keys** in the following format:

```toml
# Multi-Provider API Keys for AI Study Assistant

# Google Gemini API Key (Required for Reader Agent)
GEMINI_API_KEY = "your_gemini_api_key_here"

# Groq API Key (Required for Flashcard & Planner Agents)
GROQ_API_KEY = "your_groq_api_key_here"

# DeepSeek API Key (Required for Quiz & Chat Agents)
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"
```

**⚠️ Important**: 
- Replace the values above with your actual API keys
- Use quotes around the API key values
- Each key should be on its own line

### Alternative: Using Streamlit Secrets UI

If you prefer the UI method:

1. In Streamlit Cloud, go to your app settings
2. Navigate to "Secrets" section
3. Add each key-value pair:
   - Key: `GEMINI_API_KEY` → Value: `your_gemini_key`
   - Key: `GROQ_API_KEY` → Value: `your_groq_key`
   - Key: `DEEPSEEK_API_KEY` → Value: `your_deepseek_key`

## 📋 Complete Secrets File Format

Copy and paste this into Streamlit Cloud Secrets (replace with your actual keys):

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
GROQ_API_KEY = "your_groq_api_key_here"
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"
```

## ✅ Verification

After adding secrets, the app will:
- ✅ Automatically load API keys from Streamlit Cloud secrets
- ✅ Work exactly like your local `.env` file
- ✅ Keep your keys secure (not visible in code)

## 🔒 Important Security Notes:

- ✅ **API keys should ONLY be in Streamlit Cloud Secrets**
- ✅ Never hardcode keys in source code
- ✅ Never commit `.env` files (already in `.gitignore`)
- ✅ Streamlit Cloud secrets are encrypted and secure
- ✅ Only you (and collaborators you add) can see the secrets
- ✅ Rotate keys if they've been exposed

## 📝 After Deployment:

1. The app will be available at: `https://YOUR-APP-NAME.streamlit.app`
2. You can share this URL with others
3. Updates to your GitHub repo will automatically redeploy the app
4. All three providers (Gemini, Groq, DeepSeek) will work seamlessly

## 🐛 Troubleshooting:

### If an agent fails:
- Check that all three API keys are set in Streamlit Cloud Secrets
- Verify the keys are correct (no extra spaces, quotes are correct)
- Check the app logs in Streamlit Cloud dashboard

### If deployment fails:
- Make sure `ui/app.py` is set as the main file path
- Verify branch is `main`
- Check that `requirements.txt` is in the root directory
