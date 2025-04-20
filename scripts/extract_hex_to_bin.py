"""
Extract hex data from the example file and save it as a binary file.
"""
import re
import sys
import argparse
from pathlib import Path

# --- Configuration ---
DEFAULT_INPUT_FILE = Path('..') / 'data' / 'raw' / 'example_hex.txt'
DEFAULT_OUTPUT_FILE = Path('..') / 'data' / 'raw' / 'edid.bin'
# ---------------------

def extract_hex_to_binary(input_file, output_file):
    """Extract hex data from the input file and save as binary."""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            # Read the first 10 lines
            lines = [f.readline() for _ in range(10)]
        
        # Skip the first two lines (header and empty line)
        hex_lines = lines[2:]
        
        # Extract hex values using regex
        hex_values = []
        for line in hex_lines:
            # Find all hex values (e.g., 00, FF, etc.)
            matches = re.findall(r'([0-9A-Fa-f]{2})', line)
            hex_values.extend(matches)
        
        # Convert hex strings to bytes
        binary_data = bytes([int(h, 16) for h in hex_values])
        
        # Create output directory if it doesn't exist
        output_dir = Path(output_file).parent
        if output_dir and not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write binary data to output file
        with open(output_file, 'wb') as f:
            f.write(binary_data)
        
        print(f"Successfully extracted {len(binary_data)} bytes of EDID data to {output_file}")
        return True
    except Exception as e:
        print(f"Error extracting hex data: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Extract hex data from a text file and save as binary.')
    parser.add_argument('--input', '-i', type=str, default=str(DEFAULT_INPUT_FILE),
                        help=f'Input file containing hex data (default: {DEFAULT_INPUT_FILE})')
    parser.add_argument('--output', '-o', type=str, default=str(DEFAULT_OUTPUT_FILE),
                        help=f'Output binary file (default: {DEFAULT_OUTPUT_FILE})')
    args = parser.parse_args()
    
    success = extract_hex_to_binary(args.input, args.output)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
