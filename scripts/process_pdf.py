"""
Helper Script: Process PDF Pipeline
Standalone script to process a PDF through the complete pipeline
"""
import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from api.database import Database, init_db
from utils.pdf_utils import extract_text_from_pdf, clean_text
from api.services.chunking_service import ChunkingService
from api.services.embedding_service import EmbeddingService
import config


def process_pdf(pdf_path: str, file_name: str = None):
    """
    Process a PDF file through the complete pipeline:
    1. Extract text
    2. Clean text
    3. Chunk into segments
    4. Store in database
    5. Create embeddings
    
    Args:
        pdf_path: Path to PDF file
        file_name: Optional file name (defaults to PDF filename)
    """
    print("=" * 60)
    print("PDF Processing Pipeline")
    print("=" * 60)
    
    # Initialize services
    init_db()
    db = Database()
    chunking_service = ChunkingService()
    embedding_service = EmbeddingService()
    
    # Extract file name
    if not file_name:
        file_name = os.path.basename(pdf_path)
    
    # Step 1: Extract text
    print(f"\n📄 Step 1: Extracting text from {file_name}...")
    raw_text = extract_text_from_pdf(pdf_path)
    print(f"   ✅ Extracted {len(raw_text)} characters")
    
    # Step 2: Clean text
    print(f"\n🧹 Step 2: Cleaning text...")
    cleaned_text = clean_text(raw_text)
    print(f"   ✅ Cleaned text: {len(cleaned_text)} characters")
    
    # Step 3: Store file in database
    print(f"\n💾 Step 3: Storing file in database...")
    file_size = os.path.getsize(pdf_path)
    file_id = db.add_file(
        file_name=file_name,
        file_path=pdf_path,
        file_size=file_size,
        file_type="pdf",
        raw_text=cleaned_text
    )
    print(f"   ✅ File stored with ID: {file_id}")
    
    # Step 4: Chunk text
    print(f"\n✂️ Step 4: Chunking text into segments...")
    segments = chunking_service.chunk_text(cleaned_text, file_id=file_id)
    print(f"   ✅ Created {len(segments)} segments")
    
    # Step 5: Store segments
    print(f"\n💾 Step 5: Storing segments in database...")
    db.add_segments(file_id, segments)
    print(f"   ✅ Segments stored")
    
    # Step 6: Create embeddings
    print(f"\n🔢 Step 6: Creating embeddings...")
    segment_texts = [seg['text_content'] for seg in segments]
    segment_metadata = [
        {
            'file_id': file_id,
            'segment_id': seg['chunk_index'],
            'topic': seg['topic'],
            'label': seg['label']
        }
        for seg in segments
    ]
    embedding_ids = [f"file_{file_id}_seg_{seg['chunk_index']}" for seg in segments]
    
    embedding_service.add_vectors(
        texts=segment_texts,
        metadata=segment_metadata,
        embedding_ids=embedding_ids
    )
    print(f"   ✅ Embeddings created and stored")
    
    print("\n" + "=" * 60)
    print("✅ Processing Complete!")
    print("=" * 60)
    print(f"File ID: {file_id}")
    print(f"Segments: {len(segments)}")
    print(f"Database: {config.DB_PATH}")
    
    return file_id, segments


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a PDF file through the pipeline")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--name", help="Optional file name")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"❌ Error: File not found: {args.pdf_path}")
        sys.exit(1)
    
    try:
        file_id, segments = process_pdf(args.pdf_path, args.name)
        print(f"\n✅ Success! File ID: {file_id}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

