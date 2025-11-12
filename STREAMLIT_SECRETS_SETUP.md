# 🔐 Streamlit Cloud Secrets Setup

## Your Gemini API Key

```
AIzaSyCe-gyI4nY6DREJzH9HqJziURm7Pb5Nkd0
```

## 📋 Step-by-Step Instructions

### For Streamlit Cloud (Production)

1. **Go to Streamlit Cloud Dashboard**
   - Visit: https://share.streamlit.io/
   - Sign in with your GitHub account
   - Find your app: **ai-study-assistant**

2. **Open Settings**
   - Click on your app
   - Click **"⚙️ Settings"** (gear icon)
   - Click **"Secrets"** in the left sidebar

3. **Add the Secret**
   Copy and paste this EXACT format into the secrets editor:

   ```toml
   GEMINI_API_KEY = "AIzaSyCe-gyI4nY6DREJzH9HqJziURm7Pb5Nkd0"
   ```

4. **Save**
   - Click **"Save"** button
   - Streamlit will automatically redeploy your app
   - Wait 1-2 minutes for deployment

5. **Verify**
   - Open your app: https://your-app-name.streamlit.app
   - Check sidebar - should show: ✅ **API configured and ready**

### For Local Development

Create `.streamlit/secrets.toml` file (this file is gitignored):

```toml
GEMINI_API_KEY = "AIzaSyCe-gyI4nY6DREJzH9HqJziURm7Pb5Nkd0"
```

Or use `.env` file (also gitignored):

```env
GEMINI_API_KEY=AIzaSyCe-gyI4nY6DREJzH9HqJziURm7Pb5Nkd0
```

## ✅ Verification

After adding the secret:

1. **Streamlit Cloud**: App will auto-redeploy, check sidebar status
2. **Local**: Restart Streamlit app, check sidebar status

## 🔒 Security

- ✅ Secrets are encrypted in Streamlit Cloud
- ✅ `.streamlit/secrets.toml` is in `.gitignore` (won't be committed)
- ✅ `.env` file is in `.gitignore` (won't be committed)
- ✅ Never commit API keys to GitHub

## 📝 Notes

- The code automatically checks:
  1. Streamlit secrets (for Cloud)
  2. Environment variables
  3. `.env` file (for local)

- Priority order ensures it works everywhere!

