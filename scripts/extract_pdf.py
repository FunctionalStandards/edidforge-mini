import pdfplumber
import json
import os
import re

SPEC_DIR = os.path.join('..', 'spec')
OUTPUT_FILE = os.path.join('..', 'data', 'raw', 'spec_chunks.json')


def extract_chunks_from_pdf(pdf_path):
    """Extracts text chunks from a PDF file."""
    chunks = []
    chunk_id_counter = 0
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Processing {os.path.basename(pdf_path)}...")
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                text = page.extract_text(x_tolerance=2, y_tolerance=2) # Adjust tolerance as needed
                if not text:
                    continue

                # Simple chunking: Split by double newlines (paragraphs) or potential section headers
                # More sophisticated chunking (e.g., identifying tables, headers) would go here.
                raw_chunks = re.split(r'\n\s*\n+', text.strip()) # Split by paragraphs

                for raw_chunk in raw_chunks:
                    clean_chunk = raw_chunk.strip()
                    if not clean_chunk: # Skip empty chunks
                        continue

                    # Basic type detection (can be improved)
                    chunk_type = "paragraph"
                    # Simple heuristic for section headers (e.g., '1. Introduction', '2.2.1 Detail Timing')
                    if re.match(r'^(\d+(\.\d+)*)\s+.*', clean_chunk) or len(clean_chunk.split()) < 10 and clean_chunk.isupper():
                        chunk_type = "heading"
                        # Attempt to extract section number (crude)
                        section_match = re.match(r'^(\d+(\.\d+)*)', clean_chunk)
                        section = section_match.group(1) if section_match else None
                    else:
                        section = None # TODO: Inherit from last heading

                    chunks.append({
                        "id": f"chunk_{chunk_id_counter}",
                        "source_pdf": os.path.basename(pdf_path),
                        "page": page_num,
                        "section": section, # Needs improvement
                        "type": chunk_type,
                        "text": clean_chunk
                    })
                    chunk_id_counter += 1
        print(f"Extracted {len(chunks)} chunks from {os.path.basename(pdf_path)}.")
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
    return chunks

def main():
    """Main function to process all PDFs in the spec directory."""
    all_chunks = []
    if not os.path.exists(SPEC_DIR):
        print(f"Error: Directory '{SPEC_DIR}' not found.")
        return

    for filename in os.listdir(SPEC_DIR):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(SPEC_DIR, filename)
            pdf_chunks = extract_chunks_from_pdf(pdf_path)
            all_chunks.extend(pdf_chunks)

    if not all_chunks:
        print("No chunks extracted. Exiting.")
        return

    # Sort chunks for consistency (optional)
    all_chunks.sort(key=lambda x: (x['source_pdf'], x['page'], int(x['id'].split('_')[1])))

    # Re-assign IDs sequentially after sorting across all files
    for i, chunk in enumerate(all_chunks):
        chunk['id'] = f"chunk_{i}"

    print(f"\nTotal chunks extracted from all PDFs: {len(all_chunks)}")

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved chunks to {OUTPUT_FILE}")
    except IOError as e:
        print(f"Error writing to {OUTPUT_FILE}: {e}")

if __name__ == "__main__":
    main()
