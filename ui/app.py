"""Streamlit UI for the Study Assistant"""
import streamlit as st
import json
import os
import glob
from datetime import datetime
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.reader import ReaderAgent
from agents.flashcard import FlashcardAgent
from agents.quiz import QuizAgent
from agents.planner import PlannerAgent
from agents.chat import ChatAgent
from utils.database import StudyDatabase
import config

# Page configuration
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'reader_agent' not in st.session_state:
    st.session_state.reader_agent = ReaderAgent()
if 'flashcard_agent' not in st.session_state:
    st.session_state.flashcard_agent = FlashcardAgent()
if 'quiz_agent' not in st.session_state:
    st.session_state.quiz_agent = QuizAgent()
if 'planner_agent' not in st.session_state:
    st.session_state.planner_agent = PlannerAgent()
if 'chat_agent' not in st.session_state:
    st.session_state.chat_agent = ChatAgent()
if 'processed_content' not in st.session_state:
    st.session_state.processed_content = None
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = []
if 'quizzes' not in st.session_state:
    st.session_state.quizzes = []
if 'revision_plan' not in st.session_state:
    st.session_state.revision_plan = {}
if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = {}
if 'quiz_results' not in st.session_state:
    st.session_state.quiz_results = {}
if 'current_file_id' not in st.session_state:
    st.session_state.current_file_id = None
if 'db' not in st.session_state:
    st.session_state.db = StudyDatabase()


def main():
    """Main application"""
    st.title("📚 AI Study Assistant")
    st.markdown("**Your intelligent study companion for automated flashcards, quizzes, and revision planning**")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Reload config to get latest .env values
        import importlib
        importlib.reload(config)
        
        # API Key - Load from environment only, no user input
        current_key = config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        
        # Check if key exists and show status
        if current_key:
            # Key exists in environment - show status only
            st.success("✅ API configured and ready")
            st.caption("Using server-configured Gemini API key.")
            api_key = current_key
        else:
            # No key configured - show error
            st.error("❌ API key not configured")
            st.caption("Please configure GEMINI_API_KEY in environment variables or .env file.")
            st.stop()  # Stop the app if no API key
            api_key = ""
        
        st.markdown("---")
        st.header("📖 Navigation")
        page = st.radio(
            "Choose a page",
            ["Upload & Process", "Flashcards", "Quizzes", "Revision Plan", "Ask Questions", "Dashboard"]
        )
    
    # Route to different pages
    if page == "Upload & Process":
        upload_page()
    elif page == "Flashcards":
        flashcards_page()
    elif page == "Quizzes":
        quizzes_page()
    elif page == "Revision Plan":
        planner_page()
    elif page == "Ask Questions":
        chat_page()
    elif page == "Dashboard":
        dashboard_page()


def upload_page():
    """File upload and processing page"""
    st.header("📄 Upload Study Material")
    
    # Show saved files section first
    import config
    if os.path.exists(config.UPLOAD_DIR):
        pdf_files = glob.glob(os.path.join(config.UPLOAD_DIR, "*.pdf"))
        if pdf_files:
            st.subheader("📁 Saved Files")
            cols = st.columns([3, 1])
            with cols[0]:
                selected_file = st.selectbox(
                    "Select a saved file to process:",
                    options=["-- Upload New File --"] + [os.path.basename(f) for f in sorted(pdf_files, key=os.path.getmtime, reverse=True)],
                    key="saved_file_selector"
                )
            with cols[1]:
                if selected_file and selected_file != "-- Upload New File --":
                    if st.button("🔄 Process Selected File", type="primary"):
                        file_path = os.path.join(config.UPLOAD_DIR, selected_file)
                        if os.path.exists(file_path):
                            with st.spinner("Processing saved file..."):
                                try:
                                    # Create a file-like object from saved file
                                    class SavedFile:
                                        def __init__(self, path):
                                            self.name = os.path.basename(path)
                                            self.path = path
                                        def getbuffer(self):
                                            with open(self.path, 'rb') as f:
                                                return f.read()
                                    
                                    saved_file_obj = SavedFile(file_path)
                                    content = st.session_state.reader_agent.process_file(saved_file_obj)
                                    st.session_state.processed_content = content
                                    
                                    # Save/update file in database
                                    file_size = os.path.getsize(file_path)
                                    file_id = st.session_state.db.add_file(
                                        selected_file,
                                        file_path,
                                        file_size
                                    )
                                    st.session_state.current_file_id = file_id
                                    
                                    # Save topics to database
                                    if content.get('topics'):
                                        st.session_state.db.add_topics(file_id, content.get('topics', []))
                                    
                                    st.success(f"✅ File '{selected_file}' processed successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error processing file: {str(e)}")
            
            # Show file list
            with st.expander("📋 View All Saved Files", expanded=False):
                for pdf_file in sorted(pdf_files, key=os.path.getmtime, reverse=True):
                    file_name = os.path.basename(pdf_file)
                    file_size = os.path.getsize(pdf_file) / 1024
                    mod_time = datetime.fromtimestamp(os.path.getmtime(pdf_file))
                    st.caption(f"📄 {file_name} ({file_size:.2f} KB) - Saved: {mod_time.strftime('%Y-%m-%d %H:%M')}")
    
    st.markdown("---")
    st.subheader("📤 Upload New File")
    
    uploaded_file = st.file_uploader(
        "Upload your PDF notes, slides, or study material",
        type=['pdf'],
        help="Supported formats: PDF"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Show file info
        file_size = len(uploaded_file.getbuffer())
        st.caption(f"File size: {file_size / 1024:.2f} KB")
        
        if st.button("🚀 Process File", type="primary"):
            with st.spinner("Processing your study material..."):
                try:
                    # Process file with Reader Agent
                    content = st.session_state.reader_agent.process_file(uploaded_file)
                    st.session_state.processed_content = content
                    
                    # Save file to database
                    import config as cfg
                    file_path = os.path.join(cfg.UPLOAD_DIR, uploaded_file.name)
                    # Check if file exists (it should after processing)
                    if not os.path.exists(file_path):
                        # Find the actual saved file path
                        saved_files = glob.glob(os.path.join(cfg.UPLOAD_DIR, uploaded_file.name.replace('.pdf', '*.pdf')))
                        if saved_files:
                            file_path = saved_files[0]
                    
                    if os.path.exists(file_path):
                        file_id = st.session_state.db.add_file(
                            uploaded_file.name,
                            file_path,
                            file_size
                        )
                        st.session_state.current_file_id = file_id
                        
                        # Save topics to database
                        if content.get('topics'):
                            st.session_state.db.add_topics(file_id, content.get('topics', []))
                    
                    st.success("✅ File processed successfully!")
                    
                    # Display extracted information
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Topics Found", len(content.get('topics', [])))
                    with col2:
                        st.metric("Text Chunks", content.get('num_chunks', 0))
                    with col3:
                        st.metric("File Size", f"{content.get('file_size', 0) // 1000} KB")
                    
                    # Show extracted text
                    st.subheader("📄 Extracted Text")
                    raw_text = content.get('raw_text', '')
                    if raw_text:
                        # Show first 2000 characters with option to see more
                        text_preview = raw_text[:2000] if len(raw_text) > 2000 else raw_text
                        with st.expander("📖 View Extracted Text", expanded=False):
                            st.text_area(
                                "Extracted Content:",
                                value=raw_text,
                                height=400,
                                disabled=True,
                                label_visibility="collapsed"
                            )
                            st.caption(f"Total characters: {len(raw_text):,}")
                    else:
                        st.warning("⚠️ No text extracted from the file.")
                    
                    # Show identified topics
                    if content.get('topics'):
                        st.subheader("📋 Identified Topics")
                        for i, topic in enumerate(content['topics'][:10], 1):
                            with st.expander(f"Topic {i}: {topic.get('topic', 'Unknown')}"):
                                if topic.get('subtopics'):
                                    st.write("**Subtopics:**", ", ".join(topic['subtopics'][:5]))
                                if topic.get('key_concepts'):
                                    st.write("**Key Concepts:**", ", ".join(topic['key_concepts'][:5]))
                    
                    # Show text chunks info
                    chunks = content.get('chunks', [])
                    if chunks:
                        st.subheader("📚 Text Chunks")
                        st.info(f"Document split into {len(chunks)} chunks for processing.")
                        with st.expander("View Chunk Details", expanded=False):
                            for i, chunk in enumerate(chunks[:5], 1):  # Show first 5 chunks
                                st.markdown(f"**Chunk {i}** ({len(chunk)} characters):")
                                st.text(chunk[:300] + "..." if len(chunk) > 300 else chunk)
                                st.markdown("---")
                            if len(chunks) > 5:
                                st.caption(f"... and {len(chunks) - 5} more chunks")
                    
                    # Show saved file location
                    saved_file_path = os.path.join(config.UPLOAD_DIR, uploaded_file.name)
                    if not os.path.exists(saved_file_path):
                        # Check if file was saved with timestamp
                        pattern = os.path.join(config.UPLOAD_DIR, f"{os.path.splitext(uploaded_file.name)[0]}*.pdf")
                        matches = glob.glob(pattern)
                        if matches:
                            saved_file_path = matches[-1]
                    
                    if os.path.exists(saved_file_path):
                        st.success(f"💾 File saved successfully to: `{saved_file_path}`")
                        st.info("💡 You can now navigate to Flashcards or Quizzes pages. The file is saved and can be reprocessed anytime!")
                    
                    # Store file info in session state
                    st.session_state.last_processed_file = {
                        "name": uploaded_file.name,
                        "path": saved_file_path if os.path.exists(saved_file_path) else None,
                        "processed": True
                    }
                    
                    # Auto-generate flashcards and quizzes
                    st.info("💡 Tip: Navigate to Flashcards and Quizzes pages to generate study materials!")
                
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")
                    st.info("Make sure you have set your API keys in Streamlit Cloud Secrets or .env file.")
    
    else:
        # Show status if content is already processed
        if st.session_state.processed_content is not None:
            st.success("✅ You have processed content available!")
            st.info("💡 You can generate flashcards and quizzes. Or upload a new file to process.")
            
            # Show current processed file info
            current_file = st.session_state.processed_content.get('file_name', 'Unknown')
            st.caption(f"📄 Currently processed: {current_file}")
            
            if st.button("🔄 Clear Processed Content"):
                st.session_state.processed_content = None
                st.session_state.flashcards = []
                st.session_state.quizzes = []
                st.rerun()
        else:
            st.info("👆 Please upload a PDF file or select a saved file to get started")


def flashcards_page():
    """Flashcards page"""
    st.header("🃏 Flashcards")
    
    # Add upload option here too
    if st.session_state.processed_content is None:
        st.warning("⚠️ No file processed yet. Upload and process a file below.")
        
        st.subheader("📤 Upload & Process File")
        uploaded_file = st.file_uploader(
            "Upload your PDF to generate flashcards",
            type=['pdf'],
            key="flashcard_uploader",
            help="Upload a PDF file to process"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            file_size = len(uploaded_file.getbuffer())
            st.caption(f"File size: {file_size / 1024:.2f} KB")
            
            if st.button("🚀 Process File", type="primary", key="process_flashcard"):
                with st.spinner("Processing your study material..."):
                    try:
                        content = st.session_state.reader_agent.process_file(uploaded_file)
                        st.session_state.processed_content = content
                        
                        # Save file to database
                        import config as cfg
                        file_path = os.path.join(cfg.UPLOAD_DIR, uploaded_file.name)
                        if not os.path.exists(file_path):
                            saved_files = glob.glob(os.path.join(cfg.UPLOAD_DIR, uploaded_file.name.replace('.pdf', '*.pdf')))
                            if saved_files:
                                file_path = saved_files[0]
                        
                        if os.path.exists(file_path):
                            file_id = st.session_state.db.add_file(
                                uploaded_file.name,
                                file_path,
                                file_size
                            )
                            st.session_state.current_file_id = file_id
                            if content.get('topics'):
                                st.session_state.db.add_topics(file_id, content.get('topics', []))
                        
                        st.success("✅ File processed successfully! Now you can generate flashcards.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error processing file: {str(e)}")
            return
    
    # Show current file info if processed
    if st.session_state.processed_content:
        current_file = st.session_state.processed_content.get('file_name', 'Unknown')
        chunks = st.session_state.processed_content.get('chunks', [])
        num_chunks_available = len(chunks)
        
        # Show file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 File", current_file)
        with col2:
            st.metric("📦 Chunks", num_chunks_available)
        with col3:
            total_chars = sum(len(chunk) for chunk in chunks) if chunks else 0
            st.metric("📝 Total Text", f"{total_chars:,} chars")
        
        # Debug: Show chunk details
        if chunks:
            with st.expander("🔍 Debug: View Chunk Details", expanded=False):
                for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                    st.markdown(f"**Chunk {i+1}:** ({len(chunk)} characters)")
                    st.text(chunk[:200] + "..." if len(chunk) > 200 else chunk)
                    st.markdown("---")
        
        # Option to load existing flashcards from database
        if st.session_state.current_file_id:
            existing_flashcards = st.session_state.flashcard_agent.load_flashcards(st.session_state.current_file_id)
            if existing_flashcards and len(existing_flashcards) > 0:
                if st.button("📥 Load Existing Flashcards from Database", key="load_flashcards"):
                    st.session_state.flashcards = existing_flashcards
                    st.success(f"✅ Loaded {len(existing_flashcards)} flashcards from database!")
                    st.rerun()
    
    # Generate flashcards
    if st.button("✨ Generate Flashcards", type="primary"):
        try:
            # Check if processed content exists
            if st.session_state.processed_content is None:
                st.error("❌ No file processed yet! Please upload and process a file first.")
                return
            
            chunks = st.session_state.processed_content.get('chunks', [])
            if not chunks or len(chunks) == 0:
                st.error("❌ No content chunks available. The PDF might be empty or not properly extracted.")
                st.info("💡 Try uploading the file again or check if the PDF has readable text.")
                return
            
            # Show chunk preview for debugging
            with st.expander("🔍 Preview: First Chunk Content", expanded=False):
                if chunks:
                    preview = chunks[0][:500] if len(chunks[0]) > 500 else chunks[0]
                    st.text(preview)
                    st.caption(f"Chunk length: {len(chunks[0])} characters")
            
            with st.spinner("Generating flashcards... This may take 30-60 seconds..."):
                # Limit to first 5 chunks to avoid timeout
                num_chunks = min(5, len(chunks))
                st.info(f"🔄 Processing {num_chunks} chunks (out of {len(chunks)} total)...")
                
                # Verify chunks have content
                valid_chunks = [chunk for chunk in chunks[:num_chunks] if chunk and len(chunk.strip()) > 50]
                if not valid_chunks:
                    st.error("❌ All chunks are too short or empty. Cannot generate flashcards.")
                    return
                
                st.info(f"✅ Found {len(valid_chunks)} valid chunks with content")
                
                # Store last error for debugging
                last_error = None
                last_response = None
                
                try:
                    flashcards = st.session_state.flashcard_agent.generate_from_chunks(valid_chunks, max_chunks=5)
                    
                    if flashcards and len(flashcards) > 0:
                        st.session_state.flashcards = flashcards
                        # Save to database with file_id
                        st.session_state.flashcard_agent.save_flashcards(flashcards, st.session_state.current_file_id)
                        st.success(f"✅ Generated {len(flashcards)} flashcards from PDF: **{current_file}**!")
                        st.rerun()
                    else:
                        st.error("❌ No flashcards were generated. The LLM might not have returned valid flashcards.")
                        st.info("💡 Possible reasons:")
                        st.info("   • The LLM response was not in the expected JSON format")
                        st.info("   • The content might need clearer structure")
                        st.info("   • Try again - sometimes the API needs a retry")
                except Exception as gen_error:
                    last_error = str(gen_error)
                    st.error(f"❌ Error generating flashcards: {last_error}")
                    
                    # Try to extract response from error message
                    if "LLM response" in last_error or "response" in last_error.lower():
                        # Try to find response in error
                        import re
                        response_match = re.search(r'response.*?:(.*?)(?:\.\.\.|$)', last_error, re.IGNORECASE)
                        if response_match:
                            last_response = response_match.group(1).strip()
                
                # Show technical details if error occurred
                if last_error or (not flashcards or len(flashcards) == 0):
                    with st.expander("🔍 Technical Debug Info", expanded=True):
                        st.warning("⚠️ Check the console/terminal for detailed error logs")
                        st.code("Look for messages starting with: 📥, 📊, ✅, ❌, ⚠️")
                        st.markdown("---")
                        st.markdown("**To debug:**")
                        st.markdown("1. Open the terminal/console where Streamlit is running")
                        st.markdown("2. Look for lines starting with `📥 LLM Response`")
                        st.markdown("3. Check if the response is valid JSON")
                        st.markdown("4. Share the error logs if the issue persists")
                        
                        if last_error:
                            st.markdown("---")
                            st.markdown("**Last Error:**")
                            st.code(last_error[:500])
                        
                        if last_response:
                            st.markdown("---")
                            st.markdown("**LLM Response Preview:**")
                            st.code(last_response[:1000])
                        
                        # Try to show a retry button
                        if st.button("🔄 Retry Flashcard Generation", type="secondary"):
                            st.rerun()
                        
                        # Add fallback option
                        st.markdown("---")
                        st.markdown("**Alternative:** Try using Gemini instead of Groq")
                        if st.button("🔄 Try with Gemini API", type="secondary", key="retry_gemini"):
                            # Temporarily change provider
                            try:
                                # Create a new flashcard agent instance for this attempt
                                from agents.flashcard import FlashcardAgent
                                temp_agent = FlashcardAgent()
                                # Modify to use Gemini
                                flashcards = temp_agent.generate_from_chunks(valid_chunks, max_chunks=3)
                                if flashcards and len(flashcards) > 0:
                                    st.session_state.flashcards = flashcards
                                    st.session_state.flashcard_agent.save_flashcards(flashcards, st.session_state.current_file_id)
                                    st.success(f"✅ Generated {len(flashcards)} flashcards using Gemini!")
                                    st.rerun()
                                else:
                                    st.error("❌ Gemini also failed to generate flashcards")
                            except Exception as gemini_error:
                                st.error(f"❌ Gemini error: {str(gemini_error)}")
        except TimeoutError as e:
            st.error(f"⏱️ {str(e)}")
            st.info("💡 Try processing a smaller PDF or wait a moment and try again.")
        except ValueError as e:
            error_msg = str(e)
            if "API key" in error_msg or "key" in error_msg.lower() or "GROQ" in error_msg:
                st.error(f"🔑 {error_msg}")
                st.info("💡 Please check your Groq API key in Streamlit Cloud Secrets or .env file.")
            else:
                st.error(f"❌ {error_msg}")
                st.info("💡 The AI model may have returned an invalid response. Try again.")
        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ Error generating flashcards: {error_msg}")
            st.info("💡 Please check:")
            st.info("   • Your Groq API key is configured correctly (for flashcards)")
            st.info("   • You have internet connection")
            st.info("   • Try again with a smaller PDF")
            if "GROQ" in error_msg.upper() or "groq" in error_msg.lower():
                st.warning("⚠️ Flashcard generation uses Groq API. Make sure GROQ_API_KEY is set!")
            # Show full error in expander for debugging
            with st.expander("🔍 Technical Details"):
                st.code(str(e))
    
    # Display flashcards
    if st.session_state.flashcards:
        st.subheader(f"📚 Your Flashcards ({len(st.session_state.flashcards)} total)")
        
        # Flashcard display mode
        display_mode = st.radio("Display Mode", ["All Cards", "Study Mode"], horizontal=True)
        
        if display_mode == "Study Mode":
            # Interactive study mode
            if 'current_card' not in st.session_state:
                st.session_state.current_card = 0
            
            card = st.session_state.flashcards[st.session_state.current_card]
            
            st.markdown("---")
            st.markdown(f"### Card {st.session_state.current_card + 1} of {len(st.session_state.flashcards)}")
            
            # Sticky note style in study mode
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, #ffd89b 0%, #ffecd2 100%);
                    padding: 20px;
                    border-radius: 10px;
                    border-left: 5px solid #ff6b6b;
                    box-shadow: 0 3px 6px rgba(0,0,0,0.15);
                    margin: 20px 0;
                ">
                    <h3 style="color: #333; margin-top: 0;">📌 {card['question']}</h3>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            if st.button("👁️ Show Answer", type="primary"):
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
                        padding: 20px;
                        border-radius: 10px;
                        border-left: 5px solid #4ecdc4;
                        box-shadow: 0 3px 6px rgba(0,0,0,0.15);
                        margin: 20px 0;
                    ">
                        <h4 style="color: #333; margin-top: 0;">💡 Answer:</h4>
                        <p style="color: #555; font-size: 1.1em;">{card['answer']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Previous") and st.session_state.current_card > 0:
                    st.session_state.current_card -= 1
                    st.rerun()
            with col2:
                if st.button("➡️ Next") and st.session_state.current_card < len(st.session_state.flashcards) - 1:
                    st.session_state.current_card += 1
                    st.rerun()
        
        else:
            # Show all flashcards in sticky note style
            cols = st.columns(2)  # 2 columns for sticky note layout
            for i, card in enumerate(st.session_state.flashcards):
                col_idx = i % 2
                with cols[col_idx]:
                    # Sticky note style card
                    st.markdown(
                        f"""
                        <div style="
                            background: linear-gradient(135deg, #ffd89b 0%, #ffecd2 100%);
                            padding: 15px;
                            border-radius: 8px;
                            border-left: 4px solid #ff6b6b;
                            margin-bottom: 15px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            min-height: 120px;
                        ">
                            <h4 style="color: #333; margin-top: 0;">📌 {card['question']}</h4>
                            <p style="color: #555; font-size: 0.95em; margin-bottom: 0;">{card['answer']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if 'topic' in card:
                        st.caption(f"🏷️ {card['topic']}")
        
        # Download option
        st.download_button(
            label="📥 Download Flashcards (JSON)",
            data=json.dumps(st.session_state.flashcards, indent=2),
            file_name="flashcards.json",
            mime="application/json"
        )
    else:
        st.info("👆 Click 'Generate Flashcards' to create flashcards from your study material")


def quizzes_page():
    """Quizzes page"""
    st.header("📝 Quizzes")
    
    # Add upload option here too
    if st.session_state.processed_content is None:
        st.warning("⚠️ No file processed yet. Upload and process a file below.")
        
        st.subheader("📤 Upload & Process File")
        uploaded_file = st.file_uploader(
            "Upload your PDF to generate quiz",
            type=['pdf'],
            key="quiz_uploader",
            help="Upload a PDF file to process"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            file_size = len(uploaded_file.getbuffer())
            st.caption(f"File size: {file_size / 1024:.2f} KB")
            
            if st.button("🚀 Process File", type="primary", key="process_quiz"):
                with st.spinner("Processing your study material..."):
                    try:
                        content = st.session_state.reader_agent.process_file(uploaded_file)
                        st.session_state.processed_content = content
                        
                        # Save file to database
                        import config as cfg
                        file_path = os.path.join(cfg.UPLOAD_DIR, uploaded_file.name)
                        if not os.path.exists(file_path):
                            saved_files = glob.glob(os.path.join(cfg.UPLOAD_DIR, uploaded_file.name.replace('.pdf', '*.pdf')))
                            if saved_files:
                                file_path = saved_files[0]
                        
                        if os.path.exists(file_path):
                            file_id = st.session_state.db.add_file(
                                uploaded_file.name,
                                file_path,
                                file_size
                            )
                            st.session_state.current_file_id = file_id
                            if content.get('topics'):
                                st.session_state.db.add_topics(file_id, content.get('topics', []))
                        
                        st.success("✅ File processed successfully! Now you can generate quiz.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error processing file: {str(e)}")
            return
    
    # Quiz generation options
    col1, col2 = st.columns(2)
    with col1:
        difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"], index=1)
    with col2:
        num_questions = st.slider("Number of Questions", 3, 15, 5)
    
    # Generate quiz
    if st.button("✨ Generate Quiz", type="primary"):
        try:
            with st.spinner("Generating quiz questions... This may take 30-60 seconds..."):
                chunks = st.session_state.processed_content.get('chunks', [])
                if chunks:
                    # Limit to first 3 chunks to avoid timeout
                    num_chunks = min(3, len(chunks))
                    st.info(f"Processing {num_chunks} chunks (out of {len(chunks)} total)...")
                    
                    questions = st.session_state.quiz_agent.generate_from_chunks(
                        chunks, 
                        difficulty=difficulty,
                        max_chunks=3
                    )
                    
                    st.session_state.quizzes = questions[:num_questions]
                    st.session_state.quiz_agent.save_quiz(st.session_state.quizzes, st.session_state.current_file_id)
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_results = {}
                    st.success(f"✅ Generated {len(st.session_state.quizzes)} quiz questions!")
                    st.rerun()
                else:
                    st.error("No content chunks available. Please process a file first.")
        except TimeoutError as e:
            st.error(f"⏱️ {str(e)}")
            st.info("💡 Try processing a smaller PDF or wait a moment and try again.")
        except ValueError as e:
            error_msg = str(e)
            if "API key" in error_msg or "key" in error_msg.lower() or "DEEPSEEK" in error_msg:
                st.error(f"🔑 {error_msg}")
                st.info("💡 Please check your DeepSeek API key in Streamlit Cloud Secrets or .env file.")
            else:
                st.error(f"❌ {error_msg}")
                st.info("💡 The AI model may have returned an invalid response. Try again.")
        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ Error generating quiz: {error_msg}")
            st.info("💡 Please check:")
            st.info("   • Your DeepSeek API key is configured correctly (for quizzes)")
            st.info("   • You have internet connection")
            st.info("   • Try again with a smaller PDF")
            if "DEEPSEEK" in error_msg.upper() or "deepseek" in error_msg.lower():
                st.warning("⚠️ Quiz generation uses DeepSeek API. Make sure DEEPSEEK_API_KEY is set!")
            # Show full error in expander for debugging
            with st.expander("🔍 Technical Details"):
                st.code(str(e))
    
    # Display quiz
    if st.session_state.quizzes:
        st.subheader(f"📋 Quiz ({len(st.session_state.quizzes)} questions)")
        
        # Take quiz
        for i, question in enumerate(st.session_state.quizzes):
            st.markdown("---")
            st.markdown(f"**Question {i+1}:** {question['question']}")
            
            # Options
            options = question['options']
            selected = st.radio(
                f"Select your answer:",
                options,
                key=f"quiz_q_{i}",
                index=st.session_state.quiz_answers.get(i, None)
            )
            
            if selected:
                st.session_state.quiz_answers[i] = options.index(selected)
            
            # Show result if answered
            if i in st.session_state.quiz_answers:
                selected_idx = st.session_state.quiz_answers[i]
                result = st.session_state.quiz_agent.evaluate_answer(question, selected_idx)
                st.session_state.quiz_results[i] = result
                
                if result['is_correct']:
                    st.success(f"✅ Correct! {result.get('explanation', '')}")
                else:
                    correct_option = options[result['correct_answer']]
                    st.error(f"❌ Incorrect. Correct answer: **{correct_option}**")
                    if result.get('explanation'):
                        st.info(f"💡 {result['explanation']}")
        
        # Quiz summary
        if len(st.session_state.quiz_results) == len(st.session_state.quizzes):
            st.markdown("---")
            st.subheader("📊 Quiz Results")
            
            correct = sum(1 for r in st.session_state.quiz_results.values() if r['is_correct'])
            total = len(st.session_state.quiz_results)
            score = (correct / total * 100) if total > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Score", f"{score:.1f}%")
            with col2:
                st.metric("Correct", f"{correct}/{total}")
            with col3:
                st.metric("Accuracy", f"{(correct/total*100):.1f}%")
            
            # Performance message
            if score >= 80:
                st.success("🎉 Excellent work! You have a strong understanding of the material.")
            elif score >= 60:
                st.info("👍 Good job! Consider reviewing the topics you missed.")
            else:
                st.warning("📚 Keep studying! Review the material and try again.")
        
        # Download option
        st.download_button(
            label="📥 Download Quiz (JSON)",
            data=json.dumps(st.session_state.quizzes, indent=2),
            file_name="quiz.json",
            mime="application/json"
        )
    else:
        st.info("👆 Click 'Generate Quiz' to create a quiz from your study material")


def planner_page():
    """Revision planner page"""
    st.header("📅 Revision Plan")
    
    if st.session_state.processed_content is None:
        st.warning("⚠️ Please upload and process a file first in the 'Upload & Process' page.")
        return
    
    # Generate revision plan
    if st.button("✨ Generate Revision Plan", type="primary"):
        with st.spinner("Creating your personalized revision plan..."):
            topics = st.session_state.processed_content.get('topics', [])
            if topics:
                plan = st.session_state.planner_agent.create_revision_plan(topics)
                st.session_state.revision_plan = plan
                st.session_state.planner_agent.save_plan(plan, st.session_state.current_file_id)
                st.success("✅ Revision plan created successfully!")
                st.rerun()
            else:
                st.error("No topics found. Please process a file with identifiable topics.")
    
    # Display revision plan
    if st.session_state.revision_plan:
        plan = st.session_state.revision_plan
        
        # Summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Topics", plan.get('total_topics', 0))
        with col2:
            st.metric("Plan Duration", plan.get('study_plan_duration', 'N/A'))
        
        # Upcoming revisions
        st.subheader("📆 Upcoming Revisions (Next 7 Days)")
        upcoming = st.session_state.planner_agent.get_upcoming_revisions(plan, days_ahead=7)
        
        if upcoming:
            for task in upcoming:
                with st.expander(f"📌 {task['topic']} - {task['date']}"):
                    st.write(f"**Type:** {task['type']}")
                    st.write(f"**Estimated Time:** {task['estimated_time']}")
        else:
            st.info("No revisions scheduled for the next 7 days.")
        
        # Full plan
        st.subheader("📋 Complete Revision Schedule")
        for topic_plan in plan.get('topics', []):
            with st.expander(f"📚 {topic_plan.get('topic_name', 'Unknown Topic')}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Difficulty:** {topic_plan.get('difficulty', 'N/A')}")
                with col2:
                    st.write(f"**Importance:** {topic_plan.get('importance', 'N/A')}")
                with col3:
                    st.write(f"**Study Time:** {topic_plan.get('estimated_study_time', 'N/A')}")
                
                st.write(f"**First Revision:** {topic_plan.get('first_revision', 'N/A')}")
                st.write(f"**Subsequent Revisions:** {', '.join(topic_plan.get('subsequent_revisions', []))}")
        
        # Download option
        st.download_button(
            label="📥 Download Plan (JSON)",
            data=json.dumps(plan, indent=2),
            file_name="revision_plan.json",
            mime="application/json"
        )
    else:
        st.info("👆 Click 'Generate Revision Plan' to create a personalized study schedule")


def chat_page():
    """Chat/Doubt page"""
    st.header("💬 Ask Questions")
    
    if st.session_state.processed_content is None:
        st.warning("⚠️ Please upload and process a file first in the 'Upload & Process' page.")
        return
    
    # Chat interface
    st.markdown("Ask questions about your study material and get instant answers!")
    
    # Question input
    question = st.text_input("Enter your question:", placeholder="e.g., What is the main concept discussed in chapter 1?")
    
    if st.button("🔍 Ask", type="primary") and question:
        with st.spinner("Thinking..."):
            # Find relevant context
            chunks = st.session_state.processed_content.get('chunks', [])
            context = st.session_state.chat_agent.find_relevant_context(question, chunks)
            
            # Get answer
            result = st.session_state.chat_agent.answer_question(question, context, st.session_state.current_file_id)
            
            # Display answer
            st.markdown("### 💡 Answer")
            st.markdown(result['answer'])
            st.caption(f"Confidence: {result.get('confidence', 'medium').title()}")
    
    # Conversation history
    history = st.session_state.chat_agent.get_conversation_history()
    if history:
        st.markdown("---")
        st.subheader("📜 Conversation History")
        for i, entry in enumerate(reversed(history[-5:]), 1):  # Show last 5
            with st.expander(f"Q{i}: {entry['question'][:50]}..."):
                st.write(f"**Question:** {entry['question']}")
                st.write(f"**Answer:** {entry['answer']}")
        
        if st.button("🗑️ Clear History"):
            st.session_state.chat_agent.clear_history()
            st.rerun()


def dashboard_page():
    """Dashboard with analytics"""
    st.header("📊 Dashboard")
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        topics_count = len(st.session_state.processed_content.get('topics', [])) if st.session_state.processed_content else 0
        st.metric("Topics", topics_count)
    
    with col2:
        flashcards_count = len(st.session_state.flashcards)
        st.metric("Flashcards", flashcards_count)
    
    with col3:
        quizzes_count = len(st.session_state.quizzes)
        st.metric("Quiz Questions", quizzes_count)
    
    with col4:
        plan_topics = st.session_state.revision_plan.get('total_topics', 0) if st.session_state.revision_plan else 0
        st.metric("Planned Topics", plan_topics)
    
    # Quiz performance
    if st.session_state.quiz_results:
        st.subheader("📈 Quiz Performance")
        correct = sum(1 for r in st.session_state.quiz_results.values() if r['is_correct'])
        total = len(st.session_state.quiz_results)
        accuracy = (correct / total * 100) if total > 0 else 0
        
        st.progress(accuracy / 100)
        st.caption(f"Overall Accuracy: {accuracy:.1f}% ({correct}/{total} correct)")
    
    # Study progress
    st.subheader("📚 Study Progress")
    if st.session_state.processed_content:
        st.success("✅ Study material processed and ready")
    else:
        st.warning("⚠️ No study material uploaded yet")
    
    if st.session_state.flashcards:
        st.success(f"✅ {len(st.session_state.flashcards)} flashcards generated")
    else:
        st.info("💡 Generate flashcards to start studying")
    
    if st.session_state.quizzes:
        st.success(f"✅ {len(st.session_state.quizzes)} quiz questions ready")
    else:
        st.info("💡 Generate quizzes to test your knowledge")
    
    if st.session_state.revision_plan:
        st.success("✅ Revision plan created")
    else:
        st.info("💡 Create a revision plan to stay organized")


if __name__ == "__main__":
    main()

