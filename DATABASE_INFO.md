# 💾 Database & Storage Information

## Current Storage System

### ✅ What's Being Used:

1. **JSON Files** (Primary Storage)
   - **Location**: `outputs/` folder
   - **Files**:
     - `flashcards.json` - Generated flashcards
     - `quizzes.json` - Quiz questions
     - `planner.json` - Revision plans
     - `study_data.json` - General study data (configured but not actively used)
   - **Format**: Simple JSON files
   - **Pros**: Easy to read, edit, share
   - **Cons**: Not suitable for large-scale or multi-user

2. **Streamlit Session State** (Runtime Storage)
   - **Purpose**: Stores data during active session
   - **Data**:
     - `processed_content` - Extracted PDF content
     - `flashcards` - Current flashcards
     - `quizzes` - Current quiz questions
     - `revision_plan` - Current revision plan
   - **Lifetime**: Only during app session (cleared on refresh)

3. **FAISS Index** (Vector Storage)
   - **Location**: `outputs/faiss_index.bin` and `outputs/faiss_metadata.pkl`
   - **Purpose**: Semantic search for chat agent
   - **Format**: Binary FAISS index + pickle metadata
   - **Size**: Depends on number of documents

4. **File System** (PDF Storage)
   - **Location**: `uploads/` folder
   - **Purpose**: Store uploaded PDF files permanently
   - **Format**: Original PDF files

### 📦 TinyDB (In Requirements But Not Used)

- **Status**: Listed in `requirements.txt` but **NOT actively used** in code
- **Purpose**: Was planned for persistent storage
- **Current**: Can be removed if not needed

## Storage Architecture

```
Project Root/
├── uploads/              # PDF files (permanent)
│   └── *.pdf
├── outputs/             # Generated content
│   ├── flashcards.json
│   ├── quizzes.json
│   ├── planner.json
│   ├── faiss_index.bin   # Vector index
│   └── faiss_metadata.pkl
└── study_data.json       # General data (configured)
```

## Current Limitations

1. **No Real Database**: Using JSON files only
2. **Session-Based**: Data lost on refresh (except saved JSON files)
3. **No User Management**: Single-user, no authentication
4. **No History**: Can't track progress over time

## Recommendations

### Option 1: Keep JSON (Current - Simple)
- ✅ Works for single-user, small-scale
- ✅ Easy to backup and share
- ❌ Not scalable

### Option 2: Use TinyDB (Lightweight)
- ✅ Better than JSON for queries
- ✅ Still file-based (no server needed)
- ✅ Can add later if needed

### Option 3: SQLite (Recommended for Production)
- ✅ Proper database with queries
- ✅ Still file-based (no server)
- ✅ Better for tracking progress

### Option 4: PostgreSQL/MySQL (For Multi-User)
- ✅ Full-featured database
- ✅ Multi-user support
- ❌ Requires database server

## Current Status: **JSON Files + Session State**

**No traditional database is being used right now.**

- Data is stored in JSON files
- Runtime data in Streamlit session state
- FAISS for vector embeddings

## Do You Need a Database?

**For your current use case (single user, study assistant):**
- ✅ JSON files are **sufficient**
- ✅ Simple and works well
- ✅ Easy to backup

**If you want to add:**
- User accounts → Need database
- Progress tracking → Need database
- Multi-user support → Need database
- History/analytics → Need database

**Current setup is fine for MVP/demo!** 🎯

