#!/usr/bin/env python
"""
Analyze the binary structure of fields from EDID specification.
This script enhances field definitions with detailed binary encoding information.
"""
import json
import sys
import time
from pathlib import Path
from openai import OpenAI, RateLimitError, APIError
from dotenv import load_dotenv
import os

# --- Configuration ---
FIELD_DEFINITIONS_FILE = Path('..') / 'data' / 'processed' / 'field_definitions.json'
CHUNK_METADATA_FILE = Path('..') / 'data' / 'processed' / 'chunk_metadata.json'
SPEC_CHUNKS_FILE = Path('..') / 'data' / 'processed' / 'spec_chunks.json'
OUTPUT_ENHANCED_FIELDS_FILE = Path('..') / 'data' / 'processed' / 'enhanced_field_definitions.json'
CHAT_MODEL = 'gpt-4o-mini'
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

def get_field_context(field_name, field_offset, chunk_metadata, spec_chunks):
    """
    Get relevant specification context for a field based on its name and offset.
    Returns concatenated text from relevant chunks.
    """
    # First, find chunks that mention this field by name
    field_chunks = []
    field_name_lower = field_name.lower()
    offset_str = str(field_offset).lower()
    
    for i, chunk in enumerate(spec_chunks):
        chunk_text = chunk.get('text', '').lower()
        # Check if chunk mentions the field name or offset
        if field_name_lower in chunk_text or offset_str in chunk_text:
            field_chunks.append(chunk.get('text', ''))
    
    # If we found relevant chunks, concatenate them
    if field_chunks:
        return "\n\n".join(field_chunks)
    
    # If no specific chunks found, return a more general context
    # Look for chunks about byte offsets in general
    offset_chunks = []
    for i, chunk in enumerate(spec_chunks):
        chunk_text = chunk.get('text', '').lower()
        if "byte" in chunk_text and "offset" in chunk_text:
            offset_chunks.append(chunk.get('text', ''))
    
    if offset_chunks:
        return "\n\n".join(offset_chunks[:3])  # Limit to 3 chunks to avoid too much text
    
    # If still nothing found, return a minimal context
    return "No specific context found for this field."

def get_binary_structure_from_llm(field_name, field_offset, field_description, context, client):
    """
    Extract detailed binary structure for a specific field using LLM.
    Returns a structured representation of the binary encoding.
    """
    system_prompt = """You are an expert in binary data formats and low-level encoding, specializing in EDID (Extended Display Identification Data) format.
    
Analyze the provided specification text for the field and describe exactly how it is encoded at the binary level.

Focus on:
1. Bit-level layout (which bits represent what)
2. Encoding schemes (e.g., formulas to convert raw values)
3. Special values or flags
4. Alignment requirements
5. Dependencies on other fields

Format your response as a JSON object with the following structure:
{
  "type": "one of [simple_value, bit_fields, array, enum, fixed_pattern, formula_based]",
  "size_bytes": number of bytes this field occupies,
  "endianness": "big or little, if applicable",
  "fields": [list of sub-fields if this is a composite field],
  "encoding": "description of how raw values are converted to meaningful values",
  "hexpat_type": "suggested ImHex pattern type (u8, u16, etc. or struct with bit fields)",
  "hexpat_comment": "suggested comment for the ImHex pattern"
}

For bit fields, include a "fields" array with each element containing:
{
  "name": "name of the bit field",
  "bits": number of bits,
  "position": "start:end bit positions",
  "encoding": "how to interpret these bits",
  "description": "what these bits represent"
}

Be as precise and detailed as possible about the binary representation.
"""
    
    user_prompt = f"""
Field: {field_name}
Offset: {field_offset}
Description: {field_description}

Specification text:
{context}

Describe the exact binary structure of this field for a HexPat template.
"""
    
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"  -> Sending request to {CHAT_MODEL} for binary structure of '{field_name}'... ", end="", flush=True)
            response = client.chat.completions.create(
                model=CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for factual extraction
                response_format={"type": "json_object"},
            )
            print("Done.")
            
            response_content = response.choices[0].message.content
            
            try:
                # Parse the JSON response
                binary_structure = json.loads(response_content)
                return binary_structure
            except json.JSONDecodeError:
                print("  -> Error: Failed to parse JSON response from LLM.")
                print("  -> Raw response: " + response_content)
                # Try to extract JSON if it's embedded in text
                import re
                json_match = re.search(r'({.*})', response_content, re.DOTALL)
                if json_match:
                    try:
                        binary_structure = json.loads(json_match.group(1))
                        return binary_structure
                    except json.JSONDecodeError:
                        print("  -> Failed to parse extracted JSON.")
                
                if attempt < max_retries - 1:
                    print(f"  -> Retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print("  -> Failed to get valid binary structure after all attempts.")
                    # Return a minimal structure to avoid breaking the pipeline
                    return {
                        "type": "unknown",
                        "size_bytes": 1,
                        "hexpat_type": "u8",
                        "hexpat_comment": f"Unknown structure for {field_name}"
                    }
                    
        except RateLimitError:
            print(f"  -> Rate limit exceeded. Retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
            time.sleep(retry_delay)
            retry_delay *= 2
            
        except APIError as e:
            print(f"  -> API error: {e}. Retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
            time.sleep(retry_delay)
            retry_delay *= 2
            
        except Exception as e:
            print(f"  -> Unexpected error: {e}")
            if attempt < max_retries - 1:
                print(f"  -> Retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                # Return a minimal structure to avoid breaking the pipeline
                return {
                    "type": "unknown",
                    "size_bytes": 1,
                    "hexpat_type": "u8",
                    "hexpat_comment": f"Unknown structure for {field_name}"
                }
    
    # If we get here, all retries failed
    return {
        "type": "unknown",
        "size_bytes": 1,
        "hexpat_type": "u8",
        "hexpat_comment": f"Failed to analyze binary structure for {field_name}"
    }

def analyze_binary_structure(field_definitions, chunk_metadata, spec_chunks, client):
    """
    Analyze the binary structure of each field in detail.
    Returns enhanced field definitions with binary encoding details.
    """
    enhanced_fields = []
    
    print(f"Analyzing binary structure for {len(field_definitions)} fields...")
    
    for field in field_definitions:
        field_name = field.get('field')
        if not field_name:
            field_name = field.get('name', 'Unknown Field')
            
        field_offset = field.get('offset', 'Unknown')
        field_description = field.get('description', '')
        
        print(f"\nProcessing field: '{field_name}' (Offset: {field_offset})")
        
        # Get relevant specification chunks for this field
        field_context = get_field_context(field_name, field_offset, chunk_metadata, spec_chunks)
        
        # Prompt for detailed binary structure
        binary_structure = get_binary_structure_from_llm(
            field_name, field_offset, field_description, field_context, client
        )
        
        # Enhance field definition with binary details
        enhanced_field = {**field, "binary_structure": binary_structure}
        enhanced_fields.append(enhanced_field)
        
        # Brief pause to avoid rate limiting
        time.sleep(0.5)
    
    return enhanced_fields

def main():
    """Main entry point."""
    # Load field definitions
    field_definitions = load_json_file(FIELD_DEFINITIONS_FILE, "field definitions")
    if not field_definitions:
        print("Error: Field definitions not found.")
        return 1
    
    # Load chunk metadata
    chunk_metadata = load_json_file(CHUNK_METADATA_FILE, "chunk metadata")
    if not chunk_metadata:
        print("Error: Chunk metadata not found.")
        return 1
    
    # Load specification chunks
    spec_chunks = load_json_file(SPEC_CHUNKS_FILE, "specification chunks")
    if not spec_chunks:
        print("Error: Specification chunks not found.")
        return 1
    
    try:
        api_key = load_api_key()
    except ValueError as e:
        print(e)
        return 1
    
    client = OpenAI(api_key=api_key)
    
    # Analyze binary structure
    enhanced_fields = analyze_binary_structure(field_definitions, chunk_metadata, spec_chunks, client)
    
    # Save enhanced field definitions
    success = save_json_file(enhanced_fields, OUTPUT_ENHANCED_FIELDS_FILE, "enhanced field definitions")
    if not success:
        print("Error: Failed to save enhanced field definitions.")
        return 1
    
    print(f"\nBinary structure analysis complete. Enhanced {len(enhanced_fields)} fields.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
