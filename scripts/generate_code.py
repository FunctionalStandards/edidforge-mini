import json
import os  # Needed for os.getenv
import re
from openai import OpenAI, RateLimitError, APIError
from dotenv import load_dotenv
import time
from pathlib import Path

# --- Configuration ---
FIELD_MAPPING_FILE = Path('..') / 'data' / 'processed' / 'field_mapping.json'
SPEC_CHUNKS_FILE = Path('..') / 'data' / 'raw' / 'spec_chunks.json' # Needed to get full text
OUTPUT_DIR = Path('..') / 'functions'
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

def load_json_file(file_path, description):
    """Load JSON data from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {description}: {e}")
        return None

def sanitize_function_name(field_name):
    """Convert field name to a valid Python function name."""
    # Replace special characters with underscores
    func_name = re.sub(r'[^a-zA-Z0-9_]', '_', field_name.lower())
    # Ensure it starts with a letter
    if not func_name[0].isalpha():
        func_name = 'f_' + func_name
    return func_name

def generate_parsing_function(field_name, field_offset, spec_context):
    """Generate a parsing function for a field using OpenAI API."""
    # Create a valid function name
    func_name = f"parse_{field_name.lower().replace(' ', '_').replace('&', '').replace(',', '').replace('(', '').replace(')', '').replace('-', '_')}"
    
    # Create the prompt for the OpenAI API
    user_prompt = f"""
    Field Name: {field_name}
    Byte Offset(s): {field_offset}
    Relevant Specification Excerpts:
    ---
    {spec_context}
    ---
    Generate the Python function `{func_name}(byte_slice)` as described above.
    """
    
    # Create the system prompt
    system_prompt = """You are an expert in EDID (Extended Display Identification Data) specification and Python programming. 
    Your task is to generate a Python function that parses a specific field from an EDID binary data slice.
    
    Follow these requirements:
    1. The function should accept a single parameter: `byte_slice` (a bytes object containing the relevant bytes for this field)
    2. The function should return the parsed value in an appropriate Python data type
    3. Include detailed comments explaining the parsing logic
    4. Handle potential errors gracefully (e.g., check if byte_slice has the expected length)
    5. Return only the function code, no additional explanations
    
    For example, if asked to parse a header field that should contain the bytes [0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00], your response might be:
    
    ```python
    def parse_header(byte_slice):
        \"\"\"
        Parse the EDID header, which should be the fixed pattern: 00 FF FF FF FF FF FF 00
        
        Args:
            byte_slice (bytes): The 8-byte header
            
        Returns:
            bool: True if the header is valid, False otherwise
        \"\"\"
        # Check if we have the correct number of bytes
        if len(byte_slice) != 8:
            return f"ERROR: byte_slice must be exactly 8 bytes long"
            
        # Check if the header matches the expected pattern
        expected_header = bytes([0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00])
        return byte_slice == expected_header
    ```
    """
    
    # Initialize OpenAI client
    client = OpenAI(api_key=load_api_key())
    
    # Maximum number of retries
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            # Call the OpenAI API
            print(f"  -> Sending request to {CHAT_MODEL} for function {func_name}... ", end="", flush=True)
            response = client.chat.completions.create(
                model=CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # Low temperature for more deterministic output
                max_tokens=1000,  # Limit response length
                top_p=0.95
            )
            print("Done.")
            
            # Extract the function code from the response
            function_code = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            function_code = re.sub(r'```python\s*', '', function_code)
            function_code = re.sub(r'```\s*$', '', function_code)
            
            return function_code
            
        except RateLimitError:
            print(f"Rate limit exceeded. Retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff
            
        except APIError as e:
            print(f"API error: {e}. Retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
            time.sleep(retry_delay)
            retry_delay *= 2
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    print(f"Failed to generate function after {max_retries} attempts.")
    return None

def main():
    """Main entry point."""
    # Load field mapping
    field_mapping = load_json_file(FIELD_MAPPING_FILE, "field mapping")
    if not field_mapping:
        print("Error: Field mapping not found.")
        return
    
    # Load spec chunks
    spec_chunks = load_json_file(SPEC_CHUNKS_FILE, "specification chunks")
    if not spec_chunks:
        print("Error: Specification chunks not found.")
        return
    
    # Create output directory if it doesn't exist
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created output directory: {OUTPUT_DIR}")
    
    # Create a mapping from chunk IDs to chunk text
    chunk_id_to_text = {}
    for i, chunk in enumerate(spec_chunks):
        chunk_id = f"chunk_{i}"
        chunk_id_to_text[chunk_id] = chunk.get('text', '')
    
    # Count fields to process
    fields_to_process = list(field_mapping.keys())
    print(f"Generating parsing functions for {len(fields_to_process)} fields...\n")
    
    successful_generations = 0
    failed_generations = 0
    
    # Process each field
    for field_name in fields_to_process:
        field_info = field_mapping[field_name]
        chunk_ids = field_info.get('chunk_ids', [])
        field_offset = field_info.get('offset')
        
        print(f"\nProcessing Field: '{field_name}'")
        print(f"  -> Retrieved chunk IDs: {chunk_ids}")
        
        # Combine text from all chunks
        spec_context = ""
        for chunk_id in chunk_ids:
            if chunk_id in chunk_id_to_text:
                spec_context += chunk_id_to_text[chunk_id] + "\n\n"
        
        # Truncate context if too long
        if len(spec_context) > MAX_CONTEXT_TOKENS * 4:  # Rough estimate of tokens
            spec_context = spec_context[:MAX_CONTEXT_TOKENS * 4]
            print(f"  -> Truncated context from ~{len(spec_context)} to ~{MAX_CONTEXT_TOKENS * 4} characters.")
        
        # Generate the parsing function
        function_code = generate_parsing_function(field_name, field_offset, spec_context)
        
        if function_code:
            # Create a valid filename
            func_name = f"parse_{field_name.lower().replace(' ', '_').replace('&', '').replace(',', '').replace('(', '').replace(')', '').replace('-', '_')}"
            output_filename = OUTPUT_DIR / f"{func_name}.py"
            
            # Save the function to a file
            try:
                with open(output_filename, 'w', encoding='utf-8') as f:
                    f.write(function_code)
                print(f"  -> Saved function to {output_filename}")
                successful_generations += 1
            except Exception as e:
                print(f"  -> Error saving function: {e}")
                failed_generations += 1
        else:
            print(f"  -> Failed to generate function for '{field_name}'")
            failed_generations += 1
    
    print("\nGeneration complete.")
    print(f"Successfully generated functions: {successful_generations}")
    print(f"Failed or skipped generations: {failed_generations}")

if __name__ == "__main__":
    main()
