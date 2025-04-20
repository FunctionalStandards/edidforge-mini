import sys
import json
import importlib.util
import argparse
from pathlib import Path

# --- Configuration ---
FUNCTIONS_DIR = Path('..') / 'functions'
FIELD_DEFINITIONS_FILE = Path('..') / 'data' / 'processed' / 'field_definitions.json'
DEFAULT_EDID_FILE = Path('..') / 'data' / 'raw' / 'edid.bin'
DEFAULT_OUTPUT_FILE = Path('..') / 'data' / 'output' / 'parsed_edid.json'
EXPECTED_EDID_LENGTH = 128

# --- Helper Functions ---
def load_field_definitions():
    """Load field definitions from JSON file."""
    try:
        with FIELD_DEFINITIONS_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as ex:
        print(f"Error loading field definitions: {ex}")
        return []

def load_parsing_function(field_name):
    """Dynamically load a parsing function from the functions directory."""
    try:
        # Convert field name to a valid module name
        module_name = f"parse_{field_name.lower().replace(' ', '_').replace('&', '').replace(',', '').replace('(', '').replace(')', '').replace('-', '_')}"
        
        # Check if the module exists
        module_path = FUNCTIONS_DIR / f"{module_name}.py"
        
        # Skip if the module doesn't exist
        if not module_path.exists():
            print(f"Warning: Module file not found: {module_path}")
            return None
        
        # Load the module dynamically
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the parsing function from the module
        function_name = module_name  # The function has the same name as the module
        if hasattr(module, function_name):
            return getattr(module, function_name)
        else:
            print(f"Error: Function '{function_name}' not found in module '{module_name}'")
            return None
    except Exception as ex:
        print(f"Error loading parsing function for '{field_name}': {ex}")
        return None

def parse_edid(edid_data, field_definitions):
    """Parse EDID binary data using field definitions."""
    if not edid_data or not field_definitions:
        print("Error: Missing EDID data or field definitions.")
        return None
    
    # Verify EDID data length
    if len(edid_data) != 128:
        print(f"Warning: EDID data length is {len(edid_data)} bytes, expected 128 bytes.")
    
    results = {}
    
    # Process each field
    for field in field_definitions:
        field_name = field.get('field') or field.get('name')  # Support both field structures
        if not field_name:
            print("Warning: Field missing 'field' or 'name' attribute, skipping.")
            continue
            
        field_offset = field.get('offset')
        if not field_offset:
            print(f"Warning: Field '{field_name}' missing offset, skipping.")
            continue
        
        print(f"Parsing field: {field_name}")
        
        # Load the parsing function for this field
        parsing_function = load_parsing_function(field_name)
        
        if not parsing_function:
            print(f"Warning: No parsing function found for field '{field_name}', skipping.")
            continue
        
        # Parse the offset string (e.g., "0x00-0x07")
        try:
            start_offset, end_offset = parse_offset_string(field_offset)
        except ValueError as e:
            print(f"Error parsing offset for field '{field_name}': {e}")
            continue
        
        # Extract the relevant byte slice
        if end_offset > len(edid_data):
            print(f"Warning: Field '{field_name}' offset {field_offset} exceeds EDID data length.")
            end_offset = len(edid_data)
        
        byte_slice = edid_data[start_offset:end_offset]
        
        # Parse the field
        try:
            field_value = parsing_function(byte_slice)
            results[field_name] = field_value
        except Exception as e:
            print(f"Error parsing field '{field_name}': {e}")
            results[field_name] = None
    
    return results

def parse_offset_string(offset_string):
    """Parse offset string in format like '0x00-0x07' to start and end byte offsets."""
    try:
        if '-' in offset_string:
            start, end = offset_string.split('-')
            start_offset = int(start.strip(), 16) if '0x' in start else int(start.strip())
            end_offset = int(end.strip(), 16) if '0x' in end else int(end.strip())
            # End offset is inclusive in the specification, but we need exclusive for slicing
            end_offset += 1
        else:
            # Single byte
            start_offset = int(offset_string.strip(), 16) if '0x' in offset_string else int(offset_string.strip())
            end_offset = start_offset + 1
        
        return start_offset, end_offset
    except Exception as e:
        raise ValueError(f"Invalid offset format '{offset_string}': {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Parse EDID binary data using field definitions.')
    parser.add_argument('--input', '-i', type=str, default=str(DEFAULT_EDID_FILE),
                        help=f'Input EDID binary file (default: {DEFAULT_EDID_FILE})')
    parser.add_argument('--output', '-o', type=str, default=str(DEFAULT_OUTPUT_FILE),
                        help=f'Output JSON file (default: {DEFAULT_OUTPUT_FILE})')
    args = parser.parse_args()
    
    # Load field definitions
    field_definitions = load_field_definitions()
    if not field_definitions:
        print("Error: No field definitions found.")
        sys.exit(1)
    
    # Read EDID binary data
    try:
        with Path(args.input).open('rb') as f:
            edid_data = f.read()
    except Exception as ex:
        print(f"Error reading EDID data: {ex}")
        sys.exit(1)
    
    # Parse EDID data
    result = parse_edid(edid_data, field_definitions)
    
    # Save results to JSON file
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(args.output).parent
        if output_dir and not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Saving results to {args.output}")
        with Path(args.output).open('w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print("Parsing complete!")
    except Exception as ex:
        print(f"Error saving results: {ex}")
        sys.exit(1)

if __name__ == "__main__":
    main()
