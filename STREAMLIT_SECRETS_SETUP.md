# 🔐 Streamlit Cloud Secrets Setup Guide

## Quick Answer: **I'll guide you, but you need to add them in Streamlit Cloud UI**

I can't directly access your Streamlit Cloud account, but I'll show you exactly what to do!

## 📋 What You Need to Do

### Step 1: Go to Streamlit Cloud
1. Visit: https://share.streamlit.io/
2. Sign in with your GitHub account
3. Find your app or create a new one

### Step 2: Add Secrets
1. Click on your app
2. Click **"⚙️ Settings"** (gear icon)
3. Click **"Secrets"** in the left sidebar
4. You'll see a text editor

### Step 3: Copy This Template

Copy and paste this into the secrets editor (replace with your actual keys):

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
GROQ_API_KEY = "your_groq_api_key_here"
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"
```

### Step 4: Save
- Click **"Save"** button
- Streamlit will automatically redeploy your app

## ✅ That's It!

Your app will now have access to all three API keys, just like your local `.env` file!

## 🎯 Visual Guide

```
Streamlit Cloud Dashboard
├── Your App
│   ├── ⚙️ Settings
│   │   ├── General
│   │   ├── Secrets  ← Click here!
│   │   └── Advanced
│   └── ...
```

## 🔍 How It Works

The `config.py` file automatically loads from:
1. **Local**: `.env` file (for development)
2. **Cloud**: Streamlit Cloud Secrets (for deployment)

No code changes needed! The same code works everywhere.

## 🚨 Important Notes

- ✅ Secrets are **encrypted** and **secure**
- ✅ Only you (and collaborators) can see them
- ✅ They're **never** exposed in the app URL or logs
- ✅ They work exactly like your local `.env` file

## 📸 What It Looks Like

In Streamlit Cloud Secrets editor, you'll see:

```
┌─────────────────────────────────────┐
│ Secrets                             │
├─────────────────────────────────────┤
│                                     │
│ GEMINI_API_KEY = "your_key_here"   │
│ GROQ_API_KEY = "your_key_here"     │
│ DEEPSEEK_API_KEY = "your_key_here" │
│                                     │
│ [Save] [Cancel]                     │
└─────────────────────────────────────┘
```

## 🎉 After Setup

Once you save the secrets:
- ✅ App will automatically redeploy
- ✅ All three providers will work
- ✅ No code changes needed
- ✅ Your keys are secure!

## ❓ Need Help?

If you get stuck:
1. Check `DEPLOYMENT.md` for detailed instructions
2. Make sure all three keys are added
3. Verify no extra spaces or typos
4. Check app logs in Streamlit Cloud dashboard

