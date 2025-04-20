import pdfplumber
import json
import os
import re
from pathlib import Path

SPEC_DIR = Path('..') / 'spec'
OUTPUT_FILE = Path('..') / 'data' / 'raw' / 'spec_chunks.json'


def extract_chunks_from_pdf(pdf_path):
    """Extracts text chunks from a PDF file."""
    chunks = []
    chunk_id_counter = 0
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Processing {Path(pdf_path).name}...")
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                text = page.extract_text(x_tolerance=2, y_tolerance=2) # Adjust tolerance as needed
                if not text:
                    continue
                
                # Split text into paragraphs
                paragraphs = re.split(r'\n\s*\n', text)
                
                for para in paragraphs:
                    para = para.strip()
                    if len(para) < 20:  # Skip very short paragraphs
                        continue
                    
                    # Create a chunk
                    chunk = {
                        "id": f"chunk_{chunk_id_counter}",
                        "text": para,
                        "source_pdf": Path(pdf_path).name,
                        "page": page_num,
                        "text_preview": para[:100] + "..." if len(para) > 100 else para
                    }
                    chunks.append(chunk)
                    chunk_id_counter += 1
        
        print(f"Extracted {len(chunks)} chunks from {Path(pdf_path).name}.")
        return chunks
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
        return []


def main():
    """Main function to extract text from PDFs."""
    if not SPEC_DIR.exists():
        print(f"Error: Specification directory '{SPEC_DIR}' not found.")
        return
    
    all_chunks = []
    
    # Process each PDF in the spec directory
    for filename in os.listdir(SPEC_DIR):
        if filename.lower().endswith('.pdf'):
            pdf_path = SPEC_DIR / filename
            chunks = extract_chunks_from_pdf(pdf_path)
            all_chunks.extend(chunks)
    
    if not all_chunks:
        print("No chunks extracted from PDFs.")
        return
    
    # Ensure output directory exists
    output_dir = OUTPUT_FILE.parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save chunks to JSON file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved {len(all_chunks)} chunks to {OUTPUT_FILE}.")
    except Exception as e:
        print(f"Error saving chunks to JSON: {e}")


if __name__ == "__main__":
    main()
