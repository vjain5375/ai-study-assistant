# Streamlit Cloud Deployment Guide

## Deployment Configuration

### Required Settings for Streamlit Cloud:

1. **Repository**: `vjain5375/ai-study-assistant` ✅

2. **Branch**: `main` ✅

3. **Main file path**: `ui/app.py` ⚠️ (NOT `foo/bar/streamlit_app.py`)

4. **App URL** (optional): Leave empty or choose a custom name like `ai-study-assistant`

### Environment Variables

You'll need to add your OpenAI API key as a secret in Streamlit Cloud:

1. Go to "Advanced settings" in the deployment form
2. Click "Secrets"
3. Add:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
   **⚠️ Replace `your_api_key_here` with your actual OpenAI API key**
   
   Get your API key from: https://platform.openai.com/api-keys

### Important Notes:

- The main file path must be `ui/app.py` (not the default `foo/bar/streamlit_app.py`)
- Make sure the branch is set to `main` (not `master`)
- Your API key will be stored securely in Streamlit Cloud secrets
- The app will be publicly accessible once deployed
- **NEVER commit API keys to Git!** Always use Streamlit Secrets.

### After Deployment:

1. The app will be available at: `https://YOUR-APP-NAME.streamlit.app`
2. You can share this URL with others
3. Updates to your GitHub repo will automatically redeploy the app

### Security Reminder:

- ✅ API keys should ONLY be in Streamlit Cloud Secrets
- ✅ Never hardcode keys in source code
- ✅ Never commit `.env` files (already in `.gitignore`)
- ✅ Rotate keys if they've been exposed
