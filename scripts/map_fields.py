import json
import os
import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# --- Configuration ---
FIELD_DEFINITIONS_FILE = Path('..') / 'data' / 'processed' / 'field_definitions.json'
FAISS_INDEX_FILE = Path('..') / 'data' / 'processed' / 'faiss_index.bin'
CHUNK_METADATA_FILE = Path('..') / 'data' / 'processed' / 'chunk_metadata.json'
OUTPUT_MAPPING_FILE = Path('..') / 'data' / 'processed' / 'field_mapping.json'
EMBEDDING_MODEL = 'text-embedding-3-small'
NUM_CHUNKS_TO_RETRIEVE = 3 # Number of chunks to retrieve per field
# ---------------------

def load_api_key():
    """Loads OpenAI API key from .env file."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
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
            json.dump(data, f, indent=2)
        print(f"Successfully saved {description} to {file_path}")
        return True
    except Exception as e:
        print(f"Error saving {description}: {e}")
        return False

def get_embedding(text, client):
    """Get embedding for a text using OpenAI API."""
    try:
        response = client.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def map_fields_to_chunks():
    """Map fields to relevant chunks from the specification."""
    # Load field definitions
    field_definitions = load_json_file(FIELD_DEFINITIONS_FILE, "field definitions")
    if not field_definitions:
        return False
    
    # Load FAISS index
    try:
        index = faiss.read_index(str(FAISS_INDEX_FILE))
        print(f"Loaded FAISS index with {index.ntotal} vectors.")
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return False
    
    # Load chunk metadata
    chunk_metadata = load_json_file(CHUNK_METADATA_FILE, "chunk metadata")
    if not chunk_metadata:
        return False
    
    # Initialize OpenAI client
    client = OpenAI(api_key=load_api_key())
    
    # Create mapping from fields to chunks
    field_mapping = {}
    
    for field in field_definitions:
        # Support both 'field' and 'name' keys for backward compatibility
        field_name = field.get('field') or field.get('name', 'Unknown Field')
        query = field.get('query', f"What is the {field_name} field in EDID?")
        
        print(f"\nProcessing field: '{field_name}' (Query: '{query}')")
        
        # Get embedding for the query
        query_embedding = get_embedding(query, client)
        if not query_embedding:
            print(f"  -> Skipping field '{field_name}' due to embedding error")
            continue
        
        # Convert embedding to numpy array
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        # Search for similar chunks
        distances, indices = index.search(query_vector, NUM_CHUNKS_TO_RETRIEVE)
        
        print(f"  -> Found relevant chunk indices: {indices[0].tolist()}")
        
        # Map field to chunks
        chunk_ids = [f"chunk_{idx}" for idx in indices[0].tolist()]
        field_mapping[field_name] = {
            "query": query,
            "chunk_ids": chunk_ids,
            "offset": field.get('offset', None)
        }
        
        print(f"  -> Added {len(chunk_ids)} retrieved chunk(s) to mapping.")
    
    # Save mapping to file
    return save_json_file(field_mapping, OUTPUT_MAPPING_FILE, "field mapping with retrieved chunks")

def main():
    """Main entry point."""
    success = map_fields_to_chunks()
    if not success:
        print("Failed to map fields to chunks.")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
