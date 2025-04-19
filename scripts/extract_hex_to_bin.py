"""
Extract hex data from the example file and save it as a binary file.
"""
import re
import sys
import os
import argparse

# --- Configuration ---
DEFAULT_INPUT_FILE = os.path.join('..', 'data', 'raw', 'example_hex.txt')
DEFAULT_OUTPUT_FILE = os.path.join('..', 'data', 'raw', 'edid.bin')
# ---------------------

def extract_hex_to_binary(input_file, output_file):
    """Extract hex data from the input file and save as binary."""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            # Read the first 10 lines
            lines = [f.readline() for _ in range(10)]
        
        # Skip the first two lines (header and empty line)
        hex_lines = lines[2:10]
        
        # Extract hex values and join them
        hex_string = ''
        for line in hex_lines:
            # Extract only the hex values (remove any text)
            hex_values = re.findall(r'[0-9A-Fa-f]{2}', line)
            hex_string += ''.join(hex_values)
        
        # Convert hex string to bytes
        binary_data = bytes.fromhex(hex_string)
        
        # Verify we have 128 bytes (standard EDID size)
        if len(binary_data) != 128:
            print(f"Warning: Expected 128 bytes, got {len(binary_data)} bytes")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Write binary data to output file
        with open(output_file, 'wb') as f:
            f.write(binary_data)
        
        print(f"Successfully extracted {len(binary_data)} bytes to {output_file}")
        return True
    
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract hex data to binary EDID file')
    parser.add_argument('--input', '-i', default=DEFAULT_INPUT_FILE,
                        help=f'Path to input hex file (default: {DEFAULT_INPUT_FILE})')
    parser.add_argument('--output', '-o', default=DEFAULT_OUTPUT_FILE,
                        help=f'Path to output binary file (default: {DEFAULT_OUTPUT_FILE})')
    args = parser.parse_args()
    
    if extract_hex_to_binary(args.input, args.output):
        print("Extraction completed successfully.")
    else:
        print("Extraction failed.")
        sys.exit(1)
