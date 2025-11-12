# 🏗️ System Architecture Documentation

## Overview

The AI Study Assistant is built using a **multi-agent architecture** where specialized agents work together to provide comprehensive study support. Each agent has a specific role and communicates through a centralized knowledge base.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                        │
│  (Upload, Flashcards, Quizzes, Planner, Chat, Dashboard)    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              Central Controller / Session State              │
│         (Manages agent coordination & data flow)             │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐   ┌────────▼────────┐  ┌─────▼──────┐
│ Reader Agent │   │ Flashcard Agent │  │ Quiz Agent │
│              │   │                 │  │            │
│ - PDF Extract│   │ - Q/A Generation│  │ - MCQ Gen  │
│ - Text Clean │   │ - Topic Mapping │  │ - Scoring  │
│ - Topic ID   │   │ - JSON Export   │  │ - Feedback │
└───────┬──────┘   └─────────────────┘  └─────┬──────┘
        │                                      │
        │         ┌──────────────┐            │
        └────────►│  Knowledge   │◄───────────┘
                  │    Memory     │
                  │  (Processed   │
                  │   Content)    │
                  └───────┬───────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼──────┐  ┌───────▼──────┐  ┌──────▼──────┐
│Planner Agent │  │  Chat Agent  │  │   Utils     │
│              │  │              │  │             │
│ - Scheduling │  │ - Q&A        │  │ - LLM Calls │
│ - Spaced Rep │  │ - Context    │  │ - PDF Proc  │
│ - Reminders  │  │ - History    │  │ - Prompts   │
└──────────────┘  └──────────────┘  └─────────────┘
```

## Agent Design

### 1. Reader Agent (`agents/reader.py`)

**Purpose**: Extract and structure content from study materials

**Responsibilities**:
- PDF text extraction using PyMuPDF
- Text cleaning and normalization
- Chunking for efficient processing
- Topic identification and segmentation

**Input**: PDF file (uploaded)
**Output**: Structured content dictionary with:
- Raw text
- Text chunks
- Identified topics
- Metadata

**Key Methods**:
- `process_file()`: Main processing pipeline
- `_identify_topics()`: Topic extraction using LLM
- `_simple_topic_extraction()`: Fallback topic extraction

### 2. Flashcard Agent (`agents/flashcard.py`)

**Purpose**: Generate Q/A flashcards automatically

**Responsibilities**:
- Create concise question-answer pairs
- Map flashcards to topics
- Support batch generation from chunks
- Export/import functionality

**Input**: Text chunks or full text
**Output**: List of flashcard dictionaries

**Key Methods**:
- `generate_flashcards()`: Generate from single text
- `generate_from_chunks()`: Generate from multiple chunks
- `save_flashcards()` / `load_flashcards()`: Persistence

**LLM Prompt Strategy**:
- Focuses on understanding over memorization
- Limits answer length (2-3 sentences)
- Ensures distinct concepts per card

### 3. Quiz Agent (`agents/quiz.py`)

**Purpose**: Generate adaptive multiple-choice quizzes

**Responsibilities**:
- Create MCQs with 4 options
- Support difficulty levels (Easy/Medium/Hard)
- Evaluate student answers
- Provide explanations

**Input**: Text chunks, difficulty level, question count
**Output**: List of quiz question dictionaries

**Key Methods**:
- `generate_quiz()`: Generate questions
- `evaluate_answer()`: Score student responses
- `generate_from_chunks()`: Batch generation

**Adaptive Features**:
- Adjusts question complexity based on difficulty
- Tracks accuracy for future adjustments
- Provides detailed feedback

### 4. Planner Agent (`agents/planner.py`)

**Purpose**: Create personalized revision schedules

**Responsibilities**:
- Analyze topics and estimate difficulty
- Create spaced repetition schedule
- Track upcoming revisions
- Generate study timelines

**Input**: List of topics, current date
**Output**: Revision plan dictionary

**Key Methods**:
- `create_revision_plan()`: Main planning function
- `get_upcoming_revisions()`: Get next N days' tasks
- `_validate_topic_plan()`: Ensure valid dates

**Spaced Repetition Algorithm**:
- First revision: 1 day after study
- Subsequent: 3, 7, 14 days
- Adjusts based on topic difficulty

### 5. Chat/Doubt Agent (`agents/chat.py`)

**Purpose**: Answer contextual questions about study material

**Responsibilities**:
- Find relevant context for questions
- Generate accurate answers
- Maintain conversation history
- Provide confidence levels

**Input**: Question string, text chunks
**Output**: Answer dictionary with confidence

**Key Methods**:
- `answer_question()`: Main Q&A function
- `find_relevant_context()`: Context retrieval
- `get_conversation_history()`: History access

**Context Retrieval Strategy**:
- Keyword matching (simple)
- Can be enhanced with embeddings
- Returns top 3 relevant chunks

## Data Flow

### Processing Pipeline

1. **Upload Phase**
   ```
   User uploads PDF → Reader Agent processes → Content stored in session
   ```

2. **Generation Phase**
   ```
   User requests flashcards → Flashcard Agent uses processed content → 
   Generates flashcards → Saves to outputs/
   ```

3. **Interaction Phase**
   ```
   User asks question → Chat Agent finds context → 
   Generates answer → Updates history
   ```

### Knowledge Memory Module

All agents share access to:
- **Processed Content**: Extracted text, chunks, topics
- **Generated Content**: Flashcards, quizzes, plans
- **User State**: Quiz answers, progress, preferences

Stored in Streamlit session state for the duration of the session.

## Technology Stack

### Backend
- **Python 3.8+**: Core language
- **FastAPI/Streamlit**: Web framework (Streamlit chosen for simplicity)
- **LangChain**: Agent orchestration and LLM integration
- **PyMuPDF**: PDF processing
- **OpenAI API**: LLM provider (configurable for local models)

### Frontend
- **Streamlit**: Interactive web UI
- **No separate frontend needed**: Streamlit handles everything

### Storage
- **JSON files**: For outputs (flashcards, quizzes, plans)
- **Session State**: For runtime data
- **TinyDB**: Optional for persistent storage

### AI/ML
- **OpenAI GPT-3.5/4**: Primary LLM
- **LangChain**: Prompt management and chain building
- **FAISS**: Optional for semantic search (future enhancement)

## Inter-Agent Communication

### Communication Patterns

1. **Sequential Flow** (Reader → Others)
   - Reader Agent processes first
   - Other agents use Reader's output

2. **Parallel Generation** (Flashcard + Quiz)
   - Both can generate simultaneously
   - Share same input (processed content)

3. **Feedback Loop** (Quiz → Planner)
   - Quiz results can inform planner
   - Adjust revision schedule based on performance

### Shared Context

All agents access:
```python
st.session_state.processed_content  # Reader output
st.session_state.flashcards         # Flashcard output
st.session_state.quizzes            # Quiz output
st.session_state.revision_plan      # Planner output
```

## Error Handling

### Robustness Strategies

1. **LLM Failures**: Fallback to simple extraction methods
2. **JSON Parsing**: Multiple parsing attempts with error recovery
3. **PDF Errors**: Clear error messages with troubleshooting tips
4. **API Issues**: Graceful degradation with informative messages

## Scalability Considerations

### Current Limitations
- Single-file processing
- Session-based storage (not persistent across sessions)
- No user authentication
- Limited to PDF format

### Future Enhancements
- Multi-file support
- Database integration
- User accounts and progress tracking
- Support for images, handwritten notes
- Distributed agent processing

## Security & Privacy

### Current Implementation
- API keys stored in environment variables
- No data sent to external services except OpenAI
- Files processed locally
- No persistent user data storage

### Recommendations
- Encrypt sensitive data
- Add user authentication
- Implement rate limiting
- Add data retention policies

## Performance Optimization

### Current Optimizations
- Text chunking to manage token limits
- Caching of processed content
- Lazy loading of agents
- Efficient JSON storage

### Future Optimizations
- Vector embeddings for faster context retrieval
- Batch processing for multiple files
- Async agent execution
- Caching LLM responses

## Testing Strategy

### Recommended Tests
1. **Unit Tests**: Each agent independently
2. **Integration Tests**: Agent communication
3. **End-to-End Tests**: Full user workflows
4. **Performance Tests**: Large PDF processing

## Deployment

### Local Development
```bash
streamlit run ui/app.py
```

### Production Considerations
- Use Streamlit Cloud or similar
- Set up environment variables securely
- Implement proper logging
- Add monitoring and analytics

---

**Last Updated**: Initial Architecture Documentation
**Version**: 1.0

