# Security Guide

## API Key Protection

### ✅ Current Security Measures

1. **Environment Variables**: API keys are loaded from environment variables, never hardcoded
2. **Git Ignore**: `.env` file is excluded from Git (in `.gitignore`)
3. **UI Masking**: API keys are not displayed in the UI - only status is shown
4. **Streamlit Secrets**: For deployed apps, use Streamlit Cloud secrets (encrypted)

### 🔒 How to Secure Your API Key

#### For Local Development:
1. Create a `.env` file in the project root
2. Add: `OPENAI_API_KEY=your_key_here`
3. The `.env` file is already in `.gitignore` - it will NOT be committed

#### For Streamlit Cloud Deployment:
1. Go to your app settings on Streamlit Cloud
2. Click "Secrets"
3. Add:
   ```
   OPENAI_API_KEY=your_key_here
   ```
4. The key is encrypted and only accessible to your app

#### For Public Use:
- Users can enter their own API key in the sidebar
- No keys are stored or transmitted
- Each user uses their own OpenAI account

### ⚠️ Important Notes

- **Never commit** `.env` files to Git
- **Never share** your API key publicly
- **Never hardcode** API keys in source code
- **Rotate keys** if you suspect they've been exposed
- **Monitor usage** on OpenAI dashboard

### 🛡️ What's Protected

- ✅ `.env` file (local only, not in Git)
- ✅ Streamlit secrets (encrypted in cloud)
- ✅ API key input (password type, not displayed)
- ✅ Environment variables (not logged)

### 🚨 If Your Key is Exposed

1. **Immediately revoke** the key on OpenAI dashboard
2. **Generate a new key**
3. **Update** your `.env` file or Streamlit secrets
4. **Check usage** for any unauthorized access

