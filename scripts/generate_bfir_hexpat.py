#!/usr/bin/env python
"""
Generate ImHex pattern language (.hexpat) template from BFIR JSON.
This script integrates the BFIR to HexPat converter into the pipeline.
"""
import json
import sys
import time
from pathlib import Path

# --- Configuration ---
BFIR_JSON_FILE = Path('..') / 'data' / 'processed' / 'bfir_output.json'
OUTPUT_HEXPAT_FILE = Path('..') / 'data' / 'output' / 'bfir_generated.hexpat'
# ---------------------

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

def convert_bfir_to_hexpat(bfir_data, output_file):
    """
    Convert BFIR JSON data to HexPat template using the BFIR converter.
    
    Args:
        bfir_data: The BFIR JSON data
        output_file: Path to save the generated HexPat file
    
    Returns:
        True if conversion was successful, False otherwise
    """
    try:
        # Import the converter here to avoid circular imports
        sys.path.append(str(Path(__file__).parent.parent))
        from bfir.converters.hexpat.converter import BFIRToHexPatConverter
        
        # Create converter instance
        converter = BFIRToHexPatConverter(bfir_data)
        
        # Convert BFIR to HexPat
        hexpat_content = converter.convert()
        
        # Save HexPat file
        return save_text_file(hexpat_content, output_file, "HexPat template")
        
    except Exception as e:
        print(f"Error converting BFIR to HexPat: {e}")
        return False

def main():
    """Main entry point."""
    # Load BFIR JSON data
    bfir_data = load_json_file(BFIR_JSON_FILE, "BFIR JSON")
    if not bfir_data:
        print("Error: BFIR JSON data not found.")
        return 1
    
    # Convert BFIR to HexPat
    success = convert_bfir_to_hexpat(bfir_data, OUTPUT_HEXPAT_FILE)
    if not success:
        print("Error: Failed to convert BFIR to HexPat.")
        return 1
    
    print("\nBFIR to HexPat conversion complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
