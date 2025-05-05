#!/usr/bin/env python
"""
Generate ImHex pattern language (.hexpat) template from enhanced field definitions.
This script creates a complete, valid HexPat template for EDID binary data.
"""
import json
import sys
import time
from pathlib import Path
from openai import OpenAI, RateLimitError, APIError
from dotenv import load_dotenv
import os

# --- Configuration ---
ENHANCED_FIELDS_FILE = Path('..') / 'data' / 'processed' / 'enhanced_field_definitions.json'
OUTPUT_HEXPAT_FILE = Path('..') / 'data' / 'output' / 'edid.hexpat'
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

def save_text_file(text, file_path, description):
    """Save text to file."""
    try:
        # Create directory if it doesn't exist
        output_dir = Path(file_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Successfully saved {description} to {file_path}")
        return True
    except Exception as e:
        print(f"Error saving {description}: {e}")
        return False

def generate_hexpat_template(enhanced_fields, client):
    """
    Generate a complete HexPat template from enhanced field definitions.
    Returns the template as a string.
    """
    # Prepare context with all the enhanced field information
    fields_context = json.dumps(enhanced_fields, indent=2)
    
    system_prompt = """You are an expert in binary format specifications and ImHex pattern language (.hexpat).
Generate a complete, valid ImHex pattern file based on the provided field definitions for EDID (Extended Display Identification Data).

Your template should:
1. Include appropriate pragma statements (e.g., #pragma endian big)
2. Define structs for each field or group of related fields
3. Use appropriate types (u8, u16, etc.) and bit fields where needed
4. Include comments explaining each field, using the [[comment("")]] syntax
5. Define a main struct that includes all fields in the correct order
6. Place the main struct at the beginning of the file (offset 0)

Follow these ImHex pattern language best practices:
- Use descriptive struct and field names
- Include detailed comments for each field
- Use bit fields for fields that don't align to byte boundaries
- Use enums for fields with predefined values
- Use padding fields where necessary to maintain alignment
- Include the field offset in comments for clarity

Return ONLY the .hexpat code with no additional explanation or markdown formatting.
"""
    
    user_prompt = f"""
Generate a complete .hexpat template for ImHex based on these enhanced field definitions for EDID:

{fields_context}

Return ONLY the .hexpat code with no additional explanation.
"""
    
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"Sending request to {CHAT_MODEL} to generate HexPat template... ", end="", flush=True)
            response = client.chat.completions.create(
                model=CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent output
            )
            print("Done.")
            
            template = response.choices[0].message.content
            
            # Clean up the template if it has markdown code blocks
            template = template.replace("```hexpat", "").replace("```", "").strip()
            
            return template
                
        except RateLimitError:
            print(f"Rate limit exceeded. Retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
            time.sleep(retry_delay)
            retry_delay *= 2
            
        except APIError as e:
            print(f"API error: {e}. Retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
            time.sleep(retry_delay)
            retry_delay *= 2
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                print(f"Failed to generate HexPat template after {max_retries} attempts.")
                return "// Failed to generate HexPat template\n// Please check the enhanced field definitions and try again."
    
    # If we get here, all retries failed
    return "// Failed to generate HexPat template after multiple attempts\n// Please check the logs for more information."

def main():
    """Main entry point."""
    # Load enhanced field definitions
    enhanced_fields = load_json_file(ENHANCED_FIELDS_FILE, "enhanced field definitions")
    if not enhanced_fields:
        print("Error: Enhanced field definitions not found.")
        return 1
    
    try:
        api_key = load_api_key()
    except ValueError as e:
        print(e)
        return 1
    
    client = OpenAI(api_key=api_key)
    
    # Generate HexPat template
    template = generate_hexpat_template(enhanced_fields, client)
    
    # Save template to file
    success = save_text_file(template, OUTPUT_HEXPAT_FILE, "HexPat template")
    if not success:
        print("Error: Failed to save HexPat template.")
        return 1
    
    print("\nHexPat template generation complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
