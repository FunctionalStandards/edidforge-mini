import os
import sys
import json
import importlib.util
import argparse

# --- Configuration ---
FUNCTIONS_DIR = os.path.join('..', 'functions')
FIELD_DEFINITIONS_FILE = os.path.join('..', 'data', 'processed', 'field_definitions.json')
DEFAULT_EDID_FILE = os.path.join('..', 'data', 'raw', 'edid.bin')
DEFAULT_OUTPUT_FILE = os.path.join('..', 'data', 'output', 'parsed_edid.json')
EXPECTED_EDID_LENGTH = 128

# --- Helper Functions ---
def load_field_definitions():
    """Load field definitions from JSON file."""
    try:
        with open(FIELD_DEFINITIONS_FILE, 'r') as f:
            return json.load(f)
    except Exception as ex:
        print(f"Error loading field definitions: {ex}")
        return []

def load_edid_file(file_path):
    """Load binary EDID data from file."""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
            if len(data) != EXPECTED_EDID_LENGTH:
                print(f"Warning: EDID data is {len(data)} bytes, expected {EXPECTED_EDID_LENGTH}")
            return data
    except Exception as ex:
        print(f"Error loading EDID file: {ex}")
        return None

def load_parsing_function(function_name):
    """Dynamically load a parsing function from the functions directory."""
    try:
        # Convert function name to snake_case for filename
        module_name = "parse_" + function_name.lower().replace(' ', '_').replace('&', '_').replace('(', '_').replace(')', '_').replace('-', '_')
        module_path = os.path.join(FUNCTIONS_DIR, f"{module_name}.py")
        
        # Check if file exists
        if not os.path.exists(module_path):
            print(f"Warning: Function file not found: {module_path}")
            return None
            
        # Load module dynamically
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the parse function - look for the specific function name (e.g., parse_header)
        function_name_snake = module_name
        if hasattr(module, function_name_snake):
            return getattr(module, function_name_snake)
        else:
            print(f"Warning: No {function_name_snake} function found in {module_path}")
            return None
    except Exception as ex:
        print(f"Error loading parsing function '{function_name}': {ex}")
        return None

def convert_for_json(obj):
    """Convert objects that are not JSON serializable to serializable types."""
    if isinstance(obj, bytes):
        return list(obj)  # Convert bytes to list of integers
    elif hasattr(obj, 'to_json'):
        return obj.to_json()
    else:
        return obj

def parse_edid(edid_data, field_definitions):
    """Parse EDID data using field definitions and parsing functions."""
    results = {}
    
    for field in field_definitions:
        field_name = field.get('field', 'Unknown Field')
        field_offset = field.get('offset', '')
        print(f"Parsing field: {field_name}")
        
        # Extract byte slice based on offset
        byte_slice = None
        if field_offset:
            try:
                # Parse offset format like "0x08-0x17"
                offset_parts = field_offset.split('-')
                if len(offset_parts) == 2:
                    start_offset = int(offset_parts[0], 16)
                    end_offset = int(offset_parts[1], 16) + 1  # +1 to include end byte
                    byte_slice = edid_data[start_offset:end_offset]
                    print(f"  -> Extracted bytes {start_offset}-{end_offset-1} for field '{field_name}'")
                else:
                    # Handle single byte offset like "0x10"
                    start_offset = int(field_offset, 16)
                    byte_slice = edid_data[start_offset:start_offset+1]
                    print(f"  -> Extracted byte {start_offset} for field '{field_name}'")
            except Exception as ex:
                print(f"  -> Error extracting byte slice for '{field_name}': {ex}")
                results[field_name] = f"ERROR: Could not extract byte slice: {ex}"
                continue
        
        if byte_slice is None:
            print(f"  -> Skipping field '{field_name}' (no offset information)")
            continue
        
        # Load the parsing function
        parse_func = load_parsing_function(field_name)
        if not parse_func:
            print(f"  -> Skipping field '{field_name}' (no parser available)")
            continue
            
        # Execute the parsing function
        try:
            result = parse_func(byte_slice)
            # Convert result to JSON-serializable type if needed
            result = convert_for_json(result)
            results[field_name] = result
            print(f"  -> Success: {result}")
        except Exception as ex:
            print(f"  -> Error parsing '{field_name}': {ex}")
            results[field_name] = f"ERROR: {ex}"
            
    return results

def main():
    """Main function to parse EDID data."""
    parser = argparse.ArgumentParser(description='Parse EDID binary data')
    parser.add_argument('--input', '-i', default=DEFAULT_EDID_FILE,
                        help=f'Path to EDID binary file (default: {DEFAULT_EDID_FILE})')
    parser.add_argument('--output', '-o', default=DEFAULT_OUTPUT_FILE,
                        help=f'Path to output JSON file (default: {DEFAULT_OUTPUT_FILE})')
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Load field definitions
    print("Loading field definitions...")
    field_definitions = load_field_definitions()
    if not field_definitions:
        print("Error: No field definitions found. Exiting.")
        sys.exit(1)
    print(f"Loaded {len(field_definitions)} field definitions")
    
    # Load EDID data
    print(f"Loading EDID data from {args.input}...")
    edid_data = load_edid_file(args.input)
    if not edid_data:
        print("Error: Failed to load EDID data. Exiting.")
        sys.exit(1)
    print(f"Loaded {len(edid_data)} bytes of EDID data")
    
    # Parse EDID data
    print("Parsing EDID data...")
    results = parse_edid(edid_data, field_definitions)
    
    # Save results
    print(f"Saving results to {args.output}")
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=convert_for_json)
    
    print("Parsing complete!")

if __name__ == "__main__":
    main()
