import json
import os
import numpy as np
import faiss
from openai import OpenAI, RateLimitError, APIError
from dotenv import load_dotenv
import time
from pathlib import Path

# --- Configuration ---
FAISS_INDEX_FILE = Path('..') / 'data' / 'processed' / 'faiss_index.bin'
CHUNK_METADATA_FILE = Path('..') / 'data' / 'processed' / 'chunk_metadata.json'
OUTPUT_FIELD_DEFINITIONS_FILE = Path('..') / 'data' / 'processed' / 'field_definitions.json'
EMBEDDING_MODEL = 'text-embedding-3-small'
CHAT_MODEL = 'gpt-4o-mini' # Using the specified chat model
INITIAL_SEARCH_QUERIES = [ # Queries to find general structure info
    "EDID data structure overview",
    "byte layout definition",
    "table of contents for EDID fields",
    "EDID base block format"
]
NUM_CONTEXT_CHUNKS_PER_QUERY = 3 # How many chunks to retrieve per query for context
MAX_CONTEXT_TOKENS = 3500 # Rough limit for LLM prompt context
# ---------------------

def load_api_key():
    """Loads OpenAI API key from .env file."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file or environment variables.")
    return api_key

def load_json_file(file_path, description):
    """Loads data from a JSON file with error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {description} file '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{file_path}'.")
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

def load_faiss_index(filepath):
    """Loads a FAISS index from a file."""
    try:
        return faiss.read_index(str(filepath))
    except Exception as e:
        print(f"Error loading FAISS index from '{filepath}': {e}")
        return None

def get_single_embedding(client, text, model=EMBEDDING_MODEL):
    """Generates an embedding for a single text string."""
    try:
        # Add retry logic for potential transient API issues
        for attempt in range(3):
            try:
                response = client.embeddings.create(input=[text], model=model)
                return response.data[0].embedding
            except (RateLimitError, APIError) as e:
                if attempt < 2:
                    print(f"API Error ({type(e).__name__}) embedding text, retrying in {2**(attempt+1)}s...")
                    time.sleep(2**(attempt+1))
                else:
                    print(f"API Error ({type(e).__name__}) embedding text after multiple retries: {e}")
                    return None
            time.sleep(0.1) # Small delay between attempts
    except Exception as e:
        print(f"An unexpected error occurred during embedding: {e}")
        return None
    return None # Should not be reached normally

# Helper function to limit context size (simple token approximation)
def limit_context(text, max_tokens):
    tokens = text.split() # Very rough approximation
    if len(tokens) > max_tokens:
        print(f"Context truncated from ~{len(tokens)} to ~{max_tokens} tokens.")
        return " ".join(tokens[:max_tokens]) + "..."
    return text

def get_context_from_queries(client, index, metadata, queries, num_chunks_per_query, embedding_model):
    """Retrieves relevant text chunks based on initial search queries."""
    all_retrieved_indices = set()
    print(f"Searching for context using {len(queries)} initial queries...")

    # Load full chunks data for text lookup
    full_chunks_data = load_json_file(Path('..') / 'data' / 'processed' / 'spec_chunks.json', 'Full spec chunks')
    if not full_chunks_data:
        print("Error: Cannot load full text from spec_chunks.json. Falling back to metadata previews.")
        # Create an empty lookup or handle fallback gracefully
        chunk_text_lookup = {}
    else:
        # Create a lookup dictionary: chunk_id -> full_text
        chunk_text_lookup = {chunk.get('id'): chunk.get('text', '') for chunk in full_chunks_data}
        print(f"Loaded full text for {len(chunk_text_lookup)} chunks from spec_chunks.json.")

    for query in queries:
        print(f"  Query: '{query}'")
        query_embedding = get_single_embedding(client, query, model=embedding_model)
        if query_embedding:
            query_embedding_np = np.array([query_embedding]).astype('float32')
            try:
                _, indices = index.search(query_embedding_np, num_chunks_per_query)
                found_indices = [idx for idx in indices[0].tolist() if idx != -1] # FAISS can return -1
                all_retrieved_indices.update(found_indices)
                print(f"    -> Found indices: {found_indices}")
            except Exception as e:
                print(f"    -> Error searching FAISS index for query '{query}': {e}")
        else:
            print(f"    -> Failed to embed query '{query}'")
        time.sleep(0.5) # Increased delay between embedding calls

    print(f"Retrieved {len(all_retrieved_indices)} unique chunk indices.")

    # Retrieve text for unique indices, preserving order roughly
    context_texts = []
    sorted_indices = sorted(list(all_retrieved_indices))
    for idx in sorted_indices:
        if 0 <= idx < len(metadata):
            meta_item = metadata[idx]
            page = meta_item.get('page', 'N/A')
            chunk_id = meta_item.get('id')

            # Use full text from lookup if available, otherwise fallback to preview in metadata
            text = chunk_text_lookup.get(chunk_id, meta_item.get('text_preview', '')).strip()

            if text:
                # Add identifier for clarity
                context_texts.append(f"[Chunk ID: {chunk_id}, Page: {page}]\n{text}")
            else:
                 print(f"Warning: No text found for chunk index {idx} (ID: {chunk_id}).")
        else:
            print(f"Warning: Retrieved index {idx} is out of bounds for metadata.")

    full_context = "\n\n---\n\n".join(context_texts)
    return full_context

def generate_field_definitions(client, context, chat_model):
    """Uses LLM to identify fields and generate queries from context."""
    system_prompt = """
You are an AI assistant analyzing excerpts from a technical specification (likely EDID).
Your task is to identify the main data fields described in the provided text, focusing on those within a typical 128-byte structure.
For each field you identify, provide:
1.  `field`: A concise name for the field (e.g., "Manufacturer ID", "Header Pattern").
2.  `offset`: The byte offset(s) in hexadecimal format (e.g., "0x00-0x07", "0x11"). If the exact offset isn't clear from the text, use "Unknown".
3.  `description`: A brief description of the field's purpose based *only* on the provided text excerpts.
4.  `query`: A *search query* suitable for finding detailed information about *how this specific field is encoded or calculated* in the full specification document. The query should be specific to the field itself. Examples: "How is the EDID Manufacturer ID encoded?", "What is the calculation for EDID checksum?", "EDID byte 17 year calculation".

Present the output as a single JSON object containing a single key "fields" which holds a list of objects, where each object represents a field. Ensure the output is valid JSON.
Example JSON output format:
{
  "fields": [
    {
      "field": "Example Field",
      "offset": "0xAA-0xBB",
      "description": "This field does something specific.",
      "query": "How is the Example Field value determined or encoded in EDID?"
    },
    { ... another field ... }
  ]
}
If the text does not contain enough information to identify fields, return {"fields": []}.
"""
    user_prompt = f"""
Analyze the following specification excerpts and extract the data fields as requested. Return the result in the specified JSON format.

Specification Excerpts:
---
{context}
---

Generate the JSON output.
"""

    print(f"\nSending request to {chat_model}...")
    try:
        response = client.chat.completions.create(
            model=chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={ "type": "json_object" }, # Request JSON output
            temperature=0.1, # Low temperature for factual extraction
        )
        response_content = response.choices[0].message.content
        print("LLM response received.")

        try:
            parsed_json = json.loads(response_content)
            if isinstance(parsed_json, dict) and 'fields' in parsed_json and isinstance(parsed_json['fields'], list):
                print(f"Successfully parsed JSON and found 'fields' list with {len(parsed_json['fields'])} items.")
                return parsed_json['fields'] # Return the list directly
            else:
                print("Error: LLM response was valid JSON but did not match the expected format {'fields': [...]}.")
                print(f"Raw response content: {response_content}")
                return None # Indicate parsing failure due to format mismatch
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON response from LLM.")
            print(f"Raw response content: {response_content}")
            return None

    except RateLimitError:
        print("Error: OpenAI rate limit exceeded. Please wait and try again.")
        return None
    except APIError as e:
        print(f"Error: OpenAI API error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during LLM interaction: {e}")
        return None

def main():
    """Main function to discover fields using LLM."""
    try:
        api_key = load_api_key()
    except ValueError as e:
        print(e)
        return

    client = OpenAI(api_key=api_key)

    # Load index and metadata
    index = load_faiss_index(FAISS_INDEX_FILE)
    chunk_metadata = load_json_file(CHUNK_METADATA_FILE, "Chunk metadata")

    if not index or not chunk_metadata:
        print("Missing FAISS index or metadata file. Run previous steps first. Exiting.")
        return

    # Get context
    print("Gathering context from specification chunks...")
    context = get_context_from_queries(client, index, chunk_metadata, INITIAL_SEARCH_QUERIES, NUM_CONTEXT_CHUNKS_PER_QUERY, EMBEDDING_MODEL)

    if not context:
        print("Could not gather sufficient context. Exiting.")
        return

    # Limit context size before sending to LLM
    limited_context = limit_context(context, MAX_CONTEXT_TOKENS)
    print(f"\nContext gathered (approx {len(limited_context.split())} tokens). Asking LLM to identify fields...")

    # Generate field definitions using LLM
    generated_fields = generate_field_definitions(client, limited_context, CHAT_MODEL)

    if generated_fields is None:
        print("Field definition generation failed or response format was incorrect. Exiting.")
        return

    if not generated_fields:
        print("LLM did not identify any fields based on the provided context, or the response format was invalid.")
    else:
        print(f"\nLLM identified {len(generated_fields)} potential fields.")

    # Save the generated fields (even if empty, to overwrite the old file)
    try:
        # Ensure we wrap the list in the expected object format for consistency if needed, but prompt asks LLM for it.
        # For now, save whatever list the LLM returned.
        save_json_file(generated_fields, OUTPUT_FIELD_DEFINITIONS_FILE, 'Field definitions')
        print(f"Successfully saved LLM-generated field definitions to {OUTPUT_FIELD_DEFINITIONS_FILE}")
    except IOError as e:
        print(f"Error writing field definitions file: {e}")

if __name__ == "__main__":
    main()
