"""PDF text extraction utilities"""
import fitz  # PyMuPDF
import os
from typing import List, Tuple


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as a string
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text += page.get_text()
            text += "\n\n"  # Add spacing between pages
        
        doc.close()
        return text.encode('utf-8', errors='ignore').decode('utf-8')
    
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def extract_text_from_uploaded_file(uploaded_file) -> str:
    """
    Extract text from an uploaded file object (Streamlit).
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Extracted text as a string
    """
    # Save uploaded file temporarily
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    
    temp_path = os.path.join("uploads", uploaded_file.name)
    
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    try:
        text = extract_text_from_pdf(temp_path)
        return text
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


def clean_text(text: str) -> str:
    """
    Clean extracted text by removing excessive whitespace.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    # Remove excessive newlines
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 3:  # Ignore very short lines
            cleaned_lines.append(line)
    
    return '\n\n'.join(cleaned_lines)


def split_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into smaller chunks for processing.
    
    Args:
        text: Text to split
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at paragraph boundary
        if end < len(text):
            # Look for paragraph break near the end
            paragraph_break = text.rfind('\n\n', start, end)
            if paragraph_break > start:
                end = paragraph_break + 2
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks

