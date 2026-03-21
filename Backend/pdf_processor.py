"""
PDF Processing Module
Handles PDF text extraction, chunking, and metadata extraction
"""

import os
import uuid
import PyPDF2
from typing import List, Dict, Optional

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a PDF file
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as a single string
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[Dict]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Full text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Number of overlapping characters between chunks
        
    Returns:
        List of chunk dictionaries with text and metadata
    """
    chunks = []
    start = 0
    chunk_id = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end].strip()
        
        if chunk_text:
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "char_start": start,
                "char_end": min(end, len(text)),
                "chunk_length": len(chunk_text)
            })
            chunk_id += 1
        
        start += chunk_size - overlap
    
    return chunks

def process_pdf_file(pdf_path: str, filename: str) -> Optional[Dict]:
    """
    Complete PDF processing pipeline
    
    Args:
        pdf_path: Path to the PDF file
        filename: Original filename
        
    Returns:
        Dictionary containing title, chunks, and metadata
    """
    # Extract text
    full_text = extract_text_from_pdf(pdf_path)
    
    if not full_text:
        print(f"No text extracted from {filename}")
        return None
    
    # Create chunks
    chunks = chunk_text(full_text, chunk_size=1000, overlap=100)
    
    # Generate unique number for this PDF
    pdf_id = str(uuid.uuid4())[:8]  # Short unique ID
    
    # Add metadata to each chunk
    for chunk in chunks:
        chunk['number'] = pdf_id  # Unique identifier
        chunk['title'] = filename.replace('.pdf', '')
        chunk['source_type'] = 'pdf'  # Differentiate from videos
        chunk['page_estimate'] = chunk['char_start'] // 3000  # Rough page number
    
    return {
        "title": filename.replace('.pdf', ''),
        "chunks": chunks,
        "pdf_id": pdf_id,
        "total_chunks": len(chunks),
        "total_chars": len(full_text)
    }

def save_pdf_json(data: Dict, output_dir: str = "jsons") -> str:
    """
    Save processed PDF data to JSON file
    
    Args:
        data: Processed PDF data dictionary
        output_dir: Directory to save JSON files
        
    Returns:
        Path to saved JSON file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{data['pdf_id']}_{data['title']}.json"
    filepath = os.path.join(output_dir, filename)
    
    import json
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved PDF chunks to: {filepath}")
    return filepath