import json
import os
import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv
import time
from pathlib import Path

# --- Configuration ---
CHUNK_FILE = Path('..') / 'data' / 'raw' / 'spec_chunks.json'
OUTPUT_INDEX_FILE = Path('..') / 'data' / 'processed' / 'faiss_index.bin'
OUTPUT_METADATA_FILE = Path('..') / 'data' / 'processed' / 'chunk_metadata.json'
EMBEDDING_MODEL = 'text-embedding-3-small'
# ---------------------

def load_api_key():
    """Loads OpenAI API key from .env file."""
    load_dotenv() # Load environment variables from .env file
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file or environment variables.")
    return api_key

def load_json_file(file_path, description):
    """Load JSON data from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {description}: {e}")
        return None

def save_json_file(data, file_path, description):
    """Save JSON data to file."""
    try:
        # Create directory if it doesn't exist
        output_dir = Path(file_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved {description} to {file_path}")
        return True
    except Exception as e:
        print(f"Error saving {description}: {e}")
        return False

def get_embeddings(client, texts, model=EMBEDDING_MODEL, batch_size=100):
    """Generates embeddings for a list of texts using OpenAI API with batching."""
    all_embeddings = []
    total_texts = len(texts)
    for i in range(0, total_texts, batch_size):
        batch_texts = texts[i:i + batch_size]
        print(f"Embedding batch {i // batch_size + 1}/{(total_texts + batch_size - 1) // batch_size} (texts {i + 1}-{min(i + batch_size, total_texts)} of {total_texts})")
        try:
            response = client.embeddings.create(input=batch_texts, model=model)
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            time.sleep(0.5) # Add a small delay to avoid hitting rate limits too hard
        except Exception as e:
            print(f"Error getting embeddings for batch starting at index {i}: {e}")
            # Decide how to handle errors: stop, skip batch, fill with zeros?
            # For now, let's stop.
            raise
    return all_embeddings

def main():
    """Main function to load chunks, generate embeddings, and store them."""
    try:
        api_key = load_api_key()
    except ValueError as e:
        print(e)
        return

    client = OpenAI(api_key=api_key)

    chunks = load_json_file(CHUNK_FILE, 'chunk file')
    if not chunks:
        return

    print(f"Loaded {len(chunks)} chunks from {CHUNK_FILE}.")

    # Prepare texts and corresponding metadata
    texts_to_embed = [chunk.get('text', '') for chunk in chunks]
    metadata = [
        {
            "id": chunk.get('id'),
            "source_pdf": chunk.get('source_pdf'),
            "page": chunk.get('page'),
            "section": chunk.get('section'),
            "type": chunk.get('type'),
            "text_preview": chunk.get('text', '')[:100] + '...' # Short preview
        }
        for chunk in chunks
    ]

    print(f"Generating embeddings using '{EMBEDDING_MODEL}'...")
    try:
        embeddings = get_embeddings(client, texts_to_embed)
    except Exception:
        print("Failed to generate embeddings. Exiting.")
        return

    if not embeddings or len(embeddings) != len(chunks):
        print("Error: Number of embeddings does not match number of chunks.")
        return

    embeddings_np = np.array(embeddings).astype('float32')
    dimension = embeddings_np.shape[1]
    print(f"Generated {len(embeddings_np)} embeddings with dimension {dimension}.")

    # Build FAISS index
    index = faiss.IndexFlatL2(dimension) # Using L2 distance
    index.add(embeddings_np)
    print(f"FAISS index built. Total vectors in index: {index.ntotal}")

    # Save FAISS index
    try:
        output_dir = OUTPUT_INDEX_FILE.parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(OUTPUT_INDEX_FILE))
        print(f"FAISS index saved to {OUTPUT_INDEX_FILE}")
    except IOError as e:
        print(f"Error saving FAISS index: {e}")
        return

    # Save metadata mapping (index position -> chunk metadata)
    save_json_file(metadata, OUTPUT_METADATA_FILE, 'chunk metadata')

if __name__ == "__main__":
    main()
