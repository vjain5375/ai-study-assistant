# 📚 AI Study Assistant - Multi-Agent System

An intelligent study companion that automatically generates flashcards, quizzes, and revision plans from your study materials using a multi-agent AI architecture.

## 🎯 Features

### Core Agents

1. **Reader Agent** 📄
   - Extracts text from PDFs, slides, and handwritten notes
   - Segments material into topics, subtopics, and key concepts
   - Cleans and structures content for processing

2. **Flashcard Agent** 🃏
   - Automatically generates Q/A flashcards from study material
   - Creates concise, effective study cards
   - Supports manual editing and organization

3. **Quiz Agent** 📝
   - Generates multiple-choice questions with varying difficulty
   - Tracks student performance and accuracy
   - Provides explanations for correct answers

4. **Planner Agent** 📅
   - Creates personalized revision schedules
   - Uses spaced repetition intervals (1, 3, 7, 14 days)
   - Tracks upcoming revisions and study goals

5. **Chat/Doubt Agent** 💬
   - Answers contextual questions about uploaded material
   - Provides explanations with references
   - Maintains conversation history

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (or configure for local models)

### Installation

1. **Clone or download this repository**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   # Copy the example env file
   cp .env.example .env
   
   # Edit .env and add your OpenAI API key
   OPENAI_API_KEY=your_api_key_here
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```
   
   Or directly:
   ```bash
   streamlit run ui/app.py
   ```

5. **Open your browser:**
   - The app will automatically open at `http://localhost:8501`
   - If not, navigate to the URL shown in the terminal

## 📖 Usage Guide

### Step 1: Upload Study Material
1. Navigate to the "Upload & Process" page
2. Upload a PDF file containing your study notes
3. Click "Process File" to extract and analyze content
4. View identified topics and key concepts

### Step 2: Generate Flashcards
1. Go to the "Flashcards" page
2. Click "Generate Flashcards"
3. Study in "Study Mode" for interactive learning
4. Review all cards or download as JSON

### Step 3: Take Quizzes
1. Visit the "Quizzes" page
2. Select difficulty level (Easy/Medium/Hard)
3. Choose number of questions
4. Click "Generate Quiz" and answer questions
5. View your score and explanations

### Step 4: Create Revision Plan
1. Open the "Revision Plan" page
2. Click "Generate Revision Plan"
3. View upcoming revisions for the next 7 days
4. Track your complete study schedule

### Step 5: Ask Questions
1. Go to "Ask Questions" page
2. Type your question about the study material
3. Get instant answers with context
4. Review conversation history

### Step 6: Monitor Progress
1. Check the "Dashboard" for statistics
2. View quiz performance and accuracy
3. Track study progress across all modules

## 🏗️ Architecture

### System Design

```
┌─────────────────────────────────────────┐
│         Streamlit UI (Frontend)         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Central Controller / Main App      │
└─────────────────┬───────────────────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
┌─────▼─────┐ ┌──▼───┐ ┌─────▼─────┐
│  Reader   │ │Flash │ │   Quiz    │
│  Agent    │ │card  │ │  Agent    │
└───────────┘ │Agent │ └───────────┘
              └──┬───┘
      ┌──────────┼──────────┐
      │          │          │
┌─────▼─────┐ ┌─▼──────┐ ┌─▼────────┐
│  Planner  │ │  Chat  │ │  Utils   │
│  Agent    │ │ Agent  │ │ (LLM,    │
└───────────┘ └────────┘ │  PDF)    │
                         └──────────┘
```

### Agent Communication Flow

1. **Reader Agent** → Extracts and structures content
2. **Flashcard Agent** → Creates flashcards from processed content
3. **Quiz Agent** → Generates quizzes from same content
4. **Planner Agent** → Builds schedule from identified topics
5. **Chat Agent** → Answers questions using extracted context

All agents share context through the processed content stored in session state.

## 📁 Project Structure

```
study_agent/
│
├── agents/              # Agent implementations
│   ├── reader.py       # PDF reading and extraction
│   ├── flashcard.py    # Flashcard generation
│   ├── quiz.py         # Quiz generation
│   ├── planner.py      # Revision planning
│   └── chat.py         # Q&A agent
│
├── utils/              # Utility functions
│   ├── pdf_utils.py    # PDF processing
│   ├── prompts.py      # LLM prompts
│   └── llm_utils.py    # LLM interface
│
├── ui/                 # Frontend
│   └── app.py          # Streamlit application
│
├── outputs/            # Generated content (auto-created)
│   ├── flashcards.json
│   ├── quizzes.json
│   └── planner.json
│
├── config.py           # Configuration settings
├── main.py             # Entry point
├── requirements.txt    # Dependencies
├── .env.example        # Environment template
└── README.md           # This file
```

## ⚙️ Configuration

Edit `config.py` to customize:

- **Model Settings**: Change default LLM model
- **Chunk Size**: Adjust text chunking parameters
- **Flashcard/Quiz Limits**: Set maximum items per topic
- **Revision Intervals**: Modify spaced repetition schedule

## 🔧 Advanced Features

### Using Local Models

To use local models (e.g., Ollama) instead of OpenAI:

1. Install Ollama and run a model locally
2. Set in `.env`:
   ```
   LOCAL_MODEL=True
   OLLAMA_BASE_URL=http://localhost:11434
   ```

### Custom Prompts

Edit `utils/prompts.py` to customize agent behavior:
- Adjust flashcard question styles
- Modify quiz difficulty
- Change revision planning logic

## 📊 Output Files

All generated content is saved in the `outputs/` directory:

- `flashcards.json`: Generated flashcards
- `quizzes.json`: Quiz questions and answers
- `planner.json`: Revision schedule

## 🐛 Troubleshooting

### Common Issues

1. **"OpenAI API Key not set"**
   - Make sure you've created a `.env` file with your API key
   - Check that the key is correctly formatted

2. **PDF extraction errors**
   - Ensure PDFs are not password-protected
   - Try with a different PDF file

3. **JSON parsing errors**
   - The LLM might return malformed JSON
   - Try regenerating flashcards/quizzes
   - Check your API key has sufficient credits

4. **Import errors**
   - Run `pip install -r requirements.txt` again
   - Ensure you're using Python 3.8+

## 🎓 Example Workflow

1. **Student uploads** "Operating Systems Notes.pdf"
2. **Reader Agent** extracts text and identifies 5 topics
3. **Flashcard Agent** generates 25 flashcards automatically
4. **Quiz Agent** creates 10 MCQs with medium difficulty
5. **Planner Agent** schedules revisions over 14 days
6. **Student studies** using flashcards and quizzes
7. **Chat Agent** answers: "What is process scheduling?"
8. **Dashboard** shows 85% quiz accuracy

## 🚧 Future Enhancements

- [ ] Support for handwritten notes (OCR)
- [ ] Voice mode for flashcards
- [ ] Collaborative sharing features
- [ ] Performance analytics dashboard
- [ ] Offline mode with local models
- [ ] Multi-language support
- [ ] Integration with calendar apps

## 📝 License

This project is open source and available for educational purposes.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📧 Support

For issues or questions, please check the troubleshooting section or create an issue in the repository.

---

**Built with ❤️ for students who want to study smarter, not harder.**

