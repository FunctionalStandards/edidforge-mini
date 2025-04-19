import json
import os
import re
from openai import OpenAI, RateLimitError, APIError
from dotenv import load_dotenv
import time

# --- Configuration ---
FIELD_MAPPING_FILE = os.path.join('..', 'data', 'processed', 'field_mapping.json')
SPEC_CHUNKS_FILE = os.path.join('..', 'data', 'raw', 'spec_chunks.json') # Needed to get full text
OUTPUT_DIR = os.path.join('..', 'functions')
CHAT_MODEL = 'gpt-4o-mini'
MAX_CONTEXT_TOKENS = 4000 # Max tokens for LLM context
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

# Helper function to limit context size (simple token approximation)
def limit_context(text, max_tokens):
    tokens = text.split() # Very rough approximation
    if len(tokens) > max_tokens:
        print(f"    Context truncated from ~{len(tokens)} to ~{max_tokens} tokens.")
        return " ".join(tokens[:max_tokens]) + "..."
    return text

def generate_parsing_function(client, field_info, spec_context, chat_model):
    """Uses LLM to generate a Python parsing function for a specific field."""
    field_name = field_info.get('field', 'UnknownField')
    field_offset = field_info.get('offset', 'UnknownOffset')

    # Sanitize field name for function name
    func_name = 'parse_' + re.sub(r'\W|^(?=\d)', '_', field_name.lower()).strip('_')

    system_prompt = f"""
You are an expert Python programmer specializing in binary data parsing according to technical specifications.
Your task is to write a single, deterministic Python function to parse a specific field from a byte slice based ONLY on the provided specification excerpts.

Function Requirements:
- Name the function `{func_name}`.
- It should accept a single argument: `byte_slice` (a bytes object containing exactly the bytes for this field, e.g., if offset is 0x08-0x09, byte_slice will have length 2).
- It must return the parsed value in its appropriate Python type (e.g., int, string, float, dictionary).
- Use ONLY deterministic logic derived *strictly* from the provided specification text.
- Do NOT include any external libraries unless absolutely necessary and justified by the spec (e.g., math). Standard library is OK.
- Do NOT add example usage, comments explaining the LLM prompt, or any surrounding text.
- Output ONLY the complete Python function code, including the `def` line and necessary imports *if* needed within the function scope or standard library imports at the top.
- If the provided context is insufficient to write a reliable parsing function, return only the text "# Insufficient context to generate parser."
"""

    user_prompt = f"""
Field Name: {field_name}
Byte Offset(s): {field_offset}

Relevant Specification Excerpts:
---
{spec_context}
---

Generate the Python function `{func_name}(byte_slice)` as described above.
"""

    print(f"  -> Sending request to {chat_model} for function {func_name}...", end='', flush=True)
    try:
        # Add retry logic for API errors
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=chat_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0, # Zero temperature for deterministic code
                )
                response_content = response.choices[0].message.content
                print(" Done.")
                return response_content, func_name

            except (RateLimitError, APIError) as e:
                print(f" API Error ({type(e).__name__}), retrying in {2**(attempt+1)}s...", end='', flush=True)
                if attempt < 2:
                    time.sleep(2**(attempt+1))
                else:
                    print(" Failed after multiple retries.")
                    return f"# Failed to generate due to API error: {e}", func_name

            except Exception as e:
                 print(f" Unexpected Error: {e}.", end='', flush=True)
                 # Non-API errors are less likely to resolve on retry, break
                 return f"# Failed to generate due to unexpected error: {e}", func_name

        # Should not be reached if retries fail properly
        return "# Generation failed after retries.", func_name

    except Exception as e:
        print(f" Unexpected error during LLM call setup: {e}")
        return f"# Failed to generate due to setup error: {e}", func_name

def extract_python_code(raw_response):
    """Extracts Python code block from LLM response."""
    if raw_response.strip().startswith("#"): # Handle error/insufficient context messages
        return raw_response

    # Find ```python ... ``` block or assume the whole response is code
    match = re.search(r"```python\n(.*?)```", raw_response, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        # If no markdown block found, assume the whole response is code, strip leading/trailing whitespace
        return raw_response.strip()

def main():
    """Main function to generate parsing functions for each field."""
    try:
        api_key = load_api_key()
    except ValueError as e:
        print(e)
        return

    client = OpenAI(api_key=api_key)

    # Load field mapping and full spec chunks
    field_mappings = load_json_file(FIELD_MAPPING_FILE, "Field mapping")
    all_chunks = load_json_file(SPEC_CHUNKS_FILE, "Spec chunks")

    if not field_mappings or not all_chunks:
        print("Missing necessary input files (field_mapping.json or spec_chunks.json). Exiting.")
        return

    # Create a lookup for chunk text by ID
    chunk_text_lookup = {chunk['id']: chunk.get('text', '') for chunk in all_chunks}

    print(f"Generating parsing functions for {len(field_mappings)} fields...")

    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
            print(f"Created output directory: {OUTPUT_DIR}")
        except OSError as e:
            print(f"Error creating output directory '{OUTPUT_DIR}': {e}. Exiting.")
            return

    generated_count = 0
    failed_count = 0

    for field in field_mappings:
        field_name = field.get('field', 'UnknownField')
        print(f"\nProcessing Field: '{field_name}'")

        retrieved_chunk_ids = [c.get('chunk_id') for c in field.get('retrieved_chunks', [])]
        print(f"  -> Retrieved chunk IDs: {retrieved_chunk_ids}")

        # Gather context from retrieved chunks
        context_parts = []
        for chunk_id in retrieved_chunk_ids:
            if chunk_id in chunk_text_lookup:
                context_parts.append(chunk_text_lookup[chunk_id])
            else:
                print(f"  -> Warning: Chunk ID '{chunk_id}' not found in spec_chunks.json.")

        if not context_parts:
            print("  -> No context found for this field. Skipping generation.")
            failed_count += 1
            continue

        full_context = "\n\n---\n\n".join(context_parts)
        limited_context = limit_context(full_context, MAX_CONTEXT_TOKENS)

        # Generate function code
        raw_code, func_name = generate_parsing_function(client, field, limited_context, CHAT_MODEL)
        python_code = extract_python_code(raw_code)

        # Save the generated code
        output_filename = os.path.join(OUTPUT_DIR, f"{func_name}.py")
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(python_code)
            print(f"  -> Saved function to {output_filename}")
            if python_code.strip().startswith("#"):
                failed_count += 1 # Count generation failures/skipped
            else:
                generated_count += 1
        except IOError as e:
            print(f"  -> Error writing file {output_filename}: {e}")
            failed_count += 1

    print(f"\nCode generation complete.")
    print(f"  Successfully generated functions: {generated_count}")
    print(f"  Failed or skipped generations: {failed_count}")

if __name__ == "__main__":
    main()
