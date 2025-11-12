# API Database Schema

## Tables

### 1. files
Stores uploaded PDF files and raw extracted text.

```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    file_type TEXT,
    raw_text TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    UNIQUE(file_path)
);
```

### 2. segments
Stores chunked and labeled text segments.

```sql
CREATE TABLE segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    text_content TEXT NOT NULL,
    label TEXT,
    topic TEXT,
    page_number INTEGER,
    start_char INTEGER,
    end_char INTEGER,
    embedding_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id),
    UNIQUE(file_id, chunk_index)
);
```

### 3. embeddings
Stores embedding vector metadata.

```sql
CREATE TABLE embeddings (
    id TEXT PRIMARY KEY,
    segment_id INTEGER NOT NULL,
    file_id INTEGER NOT NULL,
    embedding_type TEXT DEFAULT 'faiss',
    vector_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (segment_id) REFERENCES segments(id),
    FOREIGN KEY (file_id) REFERENCES files(id)
);
```

### 4. artifacts
Stores generated flashcards, quizzes, and revision plans.

```sql
CREATE TABLE artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    artifact_type TEXT NOT NULL,
    artifact_data TEXT NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id)
);
```

### 5. topics
Stores identified topics from documents.

```sql
CREATE TABLE topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER,
    topic_name TEXT NOT NULL,
    subtopics TEXT,
    key_concepts TEXT,
    FOREIGN KEY (file_id) REFERENCES files(id)
);
```

### 6. flashcards
Stores generated flashcards.

```sql
CREATE TABLE flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER,
    segment_id INTEGER,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    topic TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id),
    FOREIGN KEY (segment_id) REFERENCES segments(id)
);
```

### 7. quizzes
Stores generated quiz questions.

```sql
CREATE TABLE quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER,
    segment_id INTEGER,
    question TEXT NOT NULL,
    options TEXT NOT NULL,
    correct_answer INTEGER NOT NULL,
    explanation TEXT,
    difficulty TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id),
    FOREIGN KEY (segment_id) REFERENCES segments(id)
);
```

### 8. revision_plans
Stores revision plans.

```sql
CREATE TABLE revision_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER,
    topic_name TEXT NOT NULL,
    difficulty TEXT,
    importance TEXT,
    first_revision DATE,
    subsequent_revisions TEXT,
    estimated_study_time TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id)
);
```

