#!/usr/bin/env python
"""
BFIR Pipeline Integration Script

This script integrates the Binary Format Intermediate Representation (BFIR)
into the existing pipeline, connecting binary structure analysis with
BFIR to HexPat conversion.
"""
import json
import sys
import time
from pathlib import Path
import argparse
import subprocess

# --- Configuration ---
ENHANCED_FIELDS_FILE = Path('..') / 'data' / 'processed' / 'enhanced_field_definitions.json'
BFIR_OUTPUT_FILE = Path('..') / 'data' / 'processed' / 'bfir_output.json'
HEXPAT_OUTPUT_FILE = Path('..') / 'data' / 'output' / 'bfir_generated.hexpat'
# ---------------------

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

def convert_enhanced_fields_to_bfir(enhanced_fields):
    """
    Convert enhanced field definitions to BFIR format.
    
    Args:
        enhanced_fields: List of enhanced field definitions
        
    Returns:
        BFIR data structure
    """
    # Create basic BFIR structure
    bfir = {
        "format": {
            "name": "EDID",
            "version": "1.4",
            "description": "Extended Display Identification Data",
            "endianness": "little"
        },
        "fields": []
    }
    
    # Process each enhanced field
    for field in enhanced_fields:
        field_name = field.get('field') or field.get('name', 'Unknown')
        field_offset = field.get('offset')
        field_description = field.get('description', '')
        binary_structure = field.get('binary_structure', {})
        
        # Create BFIR field based on binary structure
        bfir_field = {
            "name": field_name,
            "description": field_description,
            "offset": field_offset
        }
        
        # Determine field type based on binary structure
        field_type = binary_structure.get('type')
        if field_type == 'bitfield':
            bfir_field["type"] = "bit_fields"
            bfir_field["bit_fields"] = []
            
            # Process bit fields
            bit_fields = binary_structure.get('bit_fields', [])
            for bit_field in bit_fields:
                bfir_field["bit_fields"].append({
                    "name": bit_field.get('name', 'Unknown'),
                    "description": bit_field.get('description', ''),
                    "bits": bit_field.get('bits', 1)
                })
                
        elif field_type == 'enum':
            bfir_field["type"] = "enum"
            bfir_field["size"] = binary_structure.get('size_bytes', 1)
            bfir_field["enum_values"] = []
            
            # Process enum values
            enum_values = binary_structure.get('values', [])
            for enum_value in enum_values:
                bfir_field["enum_values"].append({
                    "name": enum_value.get('name', 'Unknown'),
                    "value": enum_value.get('value', 0),
                    "description": enum_value.get('description', '')
                })
                
        elif field_type == 'struct':
            bfir_field["type"] = "struct"
            bfir_field["fields"] = []
            
            # Process struct fields
            struct_fields = binary_structure.get('fields', [])
            for struct_field in struct_fields:
                bfir_field["fields"].append({
                    "name": struct_field.get('name', 'Unknown'),
                    "type": "simple_value",
                    "size": struct_field.get('size_bytes', 1),
                    "description": struct_field.get('description', '')
                })
                
        else:
            # Default to simple value
            bfir_field["type"] = "simple_value"
            bfir_field["size"] = binary_structure.get('size_bytes', 1)
        
        # Add field to BFIR structure
        bfir["fields"].append(bfir_field)
    
    return bfir

def run_script(script_path, cwd=None):
    """
    Run a Python script using the virtual environment Python interpreter.
    
    Args:
        script_path: Path to the script to run
        cwd: Current working directory for the script
        
    Returns:
        True if script executed successfully, False otherwise
    """
    try:
        # Use the Python interpreter from the virtual environment
        venv_python = Path('..') / '.venv' / 'Scripts' / 'python.exe'
        if not venv_python.exists():
            print(f"Virtual environment Python not found at {venv_python}")
            # Fall back to system Python
            venv_python = 'python'
        
        # Run the script
        result = subprocess.run(
            [str(venv_python), str(script_path)],
            cwd=cwd or Path(script_path).parent,
            check=True
        )
        
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running script {script_path}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error running script {script_path}: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="BFIR Pipeline Integration")
    parser.add_argument("--skip-analysis", action="store_true", help="Skip binary structure analysis")
    parser.add_argument("--skip-hexpat", action="store_true", help="Skip HexPat generation")
    args = parser.parse_args()
    
    # Get the script directory
    script_dir = Path(__file__).parent
    
    # Step 1: Run binary structure analysis if not skipped
    if not args.skip_analysis:
        print("\n=== Step 1: Running Binary Structure Analysis ===")
        success = run_script(script_dir / "binary_structure_analysis.py")
        if not success:
            print("Error: Binary structure analysis failed.")
            return 1
    
    # Step 2: Convert enhanced field definitions to BFIR
    print("\n=== Step 2: Converting Enhanced Fields to BFIR ===")
    enhanced_fields = load_json_file(ENHANCED_FIELDS_FILE, "enhanced field definitions")
    if not enhanced_fields:
        print("Error: Enhanced field definitions not found.")
        return 1
    
    bfir_data = convert_enhanced_fields_to_bfir(enhanced_fields)
    success = save_json_file(bfir_data, BFIR_OUTPUT_FILE, "BFIR data")
    if not success:
        print("Error: Failed to save BFIR data.")
        return 1
    
    # Step 3: Generate HexPat from BFIR if not skipped
    if not args.skip_hexpat:
        print("\n=== Step 3: Generating HexPat from BFIR ===")
        success = run_script(script_dir / "generate_bfir_hexpat.py")
        if not success:
            print("Error: HexPat generation failed.")
            return 1
    
    print("\nBFIR pipeline integration complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
