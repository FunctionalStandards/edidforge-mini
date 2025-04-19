import json
import os
import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv

# --- Configuration ---
FIELD_DEFINITIONS_FILE = os.path.join('..', 'data', 'processed', 'field_definitions.json')
FAISS_INDEX_FILE = os.path.join('..', 'data', 'processed', 'faiss_index.bin')
CHUNK_METADATA_FILE = os.path.join('..', 'data', 'processed', 'chunk_metadata.json')
OUTPUT_MAPPING_FILE = os.path.join('..', 'data', 'processed', 'field_mapping.json')
EMBEDDING_MODEL = 'text-embedding-3-small'
NUM_CHUNKS_TO_RETRIEVE = 3 # Number of chunks to retrieve per field
# ---------------------

def load_api_key():
    """Loads OpenAI API key from .env file."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file or environment variables.")
    return api_key

def load_json_file(filepath, description):
    """Loads data from a JSON file with error handling."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {description} file '{filepath}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'.")
        return None

def load_faiss_index(filepath):
    """Loads a FAISS index from a file."""
    try:
        return faiss.read_index(filepath)
    except Exception as e:
        print(f"Error loading FAISS index from '{filepath}': {e}")
        return None

def get_single_embedding(client, text, model=EMBEDDING_MODEL):
    """Generates an embedding for a single text string."""
    try:
        response = client.embeddings.create(input=[text], model=model)
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding for text '{text[:50]}...': {e}")
        return None

def main():
    """Main function to map fields to relevant spec chunks."""
    try:
        api_key = load_api_key()
    except ValueError as e:
        print(e)
        return

    client = OpenAI(api_key=api_key)

    # Load necessary files
    field_definitions = load_json_file(FIELD_DEFINITIONS_FILE, "Field definitions")
    index = load_faiss_index(FAISS_INDEX_FILE)
    chunk_metadata = load_json_file(CHUNK_METADATA_FILE, "Chunk metadata")

    if not field_definitions or not index or not chunk_metadata:
        print("Missing necessary input files. Exiting.")
        return

    print(f"Loaded {len(field_definitions)} field definitions.")
    print(f"Loaded FAISS index with {index.ntotal} vectors.")
    print(f"Loaded {len(chunk_metadata)} chunk metadata entries.")

    final_mapping = []

    for field_def in field_definitions:
        query = field_def.get('query')
        if not query:
            print(f"Skipping field definition without a query: {field_def}")
            continue

        print(f"\nProcessing field: '{field_def.get('field', 'N/A')}' (Query: '{query}')")

        # 1. Embed the query
        query_embedding = get_single_embedding(client, query)
        if not query_embedding:
            print(f"  -> Failed to embed query. Skipping field.")
            continue

        query_embedding_np = np.array([query_embedding]).astype('float32')

        # 2. Search FAISS index
        try:
            distances, indices = index.search(query_embedding_np, NUM_CHUNKS_TO_RETRIEVE)
            retrieved_indices = indices[0] # Get the indices for the first (only) query
            retrieved_distances = distances[0]
            print(f"  -> Found relevant chunk indices: {retrieved_indices.tolist()}")
        except Exception as e:
            print(f"  -> Error searching FAISS index: {e}. Skipping field.")
            continue

        # 3. Retrieve chunk metadata
        retrieved_chunks_info = []
        for i, idx in enumerate(retrieved_indices):
            if 0 <= idx < len(chunk_metadata):
                metadata = chunk_metadata[idx]
                retrieved_chunks_info.append({
                    "chunk_id": metadata.get('id'),
                    "source_pdf": metadata.get('source_pdf'),
                    "page": metadata.get('page'),
                    "text_preview": metadata.get('text_preview'),
                    "distance": float(retrieved_distances[i]) # Include similarity score
                })
            else:
                print(f"  -> Warning: Retrieved index {idx} is out of bounds for metadata.")

        # 4. Combine field definition with retrieved info
        mapping_entry = {
            "offset": field_def.get('offset'),
            "field": field_def.get('field'),
            "query": query,
            "retrieved_chunks": retrieved_chunks_info
        }
        final_mapping.append(mapping_entry)
        print(f"  -> Added {len(retrieved_chunks_info)} retrieved chunk(s) to mapping.")

    # 5. Save the final mapping
    try:
        with open(OUTPUT_MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_mapping, f, indent=2, ensure_ascii=False)
        print(f"\nSuccessfully saved field mapping with retrieved chunks to {OUTPUT_MAPPING_FILE}")
    except IOError as e:
        print(f"Error writing final mapping file: {e}")

if __name__ == "__main__":
    main()
