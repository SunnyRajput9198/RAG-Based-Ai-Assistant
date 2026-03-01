"""
PDF Processing Script
Main entry point for processing PDF files
Usage: python process_pdf.py <pdf_file_path>
"""

import sys
import os
from pdf_processor import process_pdf_file, save_pdf_json
from sentence_transformers import SentenceTransformer
import joblib
import pandas as pd

# Load embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def process_and_save_pdf(pdf_path: str) -> dict:
    """
    Process a PDF file and add it to the embeddings database
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with processing results
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found - {pdf_path}")
        return {"success": False, "error": "File not found"}
    
    # Get filename
    filename = os.path.basename(pdf_path)
    print(f"\n📄 Processing PDF: {filename}")
    
    # Extract and chunk
    result = process_pdf_file(pdf_path, filename)
    
    if not result:
        return {"success": False, "error": "Text extraction failed"}
    
    print(f"✅ Extracted {result['total_chunks']} chunks ({result['total_chars']} chars)")
    
    # Save to JSON
    json_path = save_pdf_json(result)
    
    # Create embeddings
    print("🔄 Creating embeddings...")
    texts = [chunk['text'] for chunk in result['chunks']]
    embeddings = embedding_model.encode(texts, show_progress_bar=True)
    
    # Add embeddings to chunks
    for i, chunk in enumerate(result['chunks']):
        chunk['embedding'] = embeddings[i].tolist()
    
    # Load existing data or create new
    if os.path.exists("data.embeddings.joblib"):
        existing_df = joblib.load("data.embeddings.joblib")
        print(f"📊 Existing data: {len(existing_df)} chunks")
        
        # Check if PDF already processed
        if result['pdf_id'] in existing_df['number'].values:
            print(f"⚠️  PDF already processed: {result['title']}")
            return {
                "success": False, 
                "error": "PDF already exists in database",
                "title": result['title']
            }
        
        # Append new chunks
        new_df = pd.DataFrame(result['chunks'])
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        print("📊 Creating new embeddings database")
        combined_df = pd.DataFrame(result['chunks'])
    
    # Save updated database
    joblib.dump(combined_df, "data.embeddings.joblib")
    print(f"💾 Saved! Total chunks: {len(combined_df)}")
    
    return {
        "success": True,
        "title": result['title'],
        "pdf_id": result['pdf_id'],
        "chunks": result['total_chunks'],
        "total_items": len(combined_df)
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_pdf.py <pdf_file_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    result = process_and_save_pdf(pdf_path)
    
    if result['success']:
        print(f"\n✅ SUCCESS!")
        print(f"   Title: {result['title']}")
        print(f"   PDF ID: {result['pdf_id']}")
        print(f"   Chunks: {result['chunks']}")
    else:
        print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")