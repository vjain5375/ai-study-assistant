# Streamlit Cloud Secrets Setup Guide

## Your Gemini API Key

```
GEMINI_API_KEY = "AIzaSyCe-gyI4nY6DREJzH9HqJziURm7Pb5Nkd0"
```

## How to Add to Streamlit Cloud

### Step 1: Go to Streamlit Cloud
1. Visit: https://share.streamlit.io/
2. Sign in with your GitHub account
3. Find your app: **ai-study-assistant**

### Step 2: Open Settings
1. Click on your app
2. Click **"⚙️ Settings"** (gear icon in the top right)
3. Click **"Secrets"** in the left sidebar

### Step 3: Add the Secret
Copy and paste this into the secrets editor:

```toml
GEMINI_API_KEY = "AIzaSyCe-gyI4nY6DREJzH9HqJziURm7Pb5Nkd0"
```

### Step 4: Save
- Click **"Save"** button
- Streamlit will automatically redeploy your app

## For Local Development

Create a `.streamlit/secrets.toml` file (for local testing):

```toml
GEMINI_API_KEY = "AIzaSyCe-gyI4nY6DREJzH9HqJziURm7Pb5Nkd0"
```

**Note:** `.streamlit/secrets.toml` is already in `.gitignore`, so it won't be committed to GitHub.

## Verification

After adding the secret, your app will automatically reload and you should see:
- ✅ API configured and ready (in the sidebar)

## Security Notes

- ✅ Secrets are encrypted in Streamlit Cloud
- ✅ Never commit API keys to GitHub
- ✅ The `.env` file is also in `.gitignore` for local development

