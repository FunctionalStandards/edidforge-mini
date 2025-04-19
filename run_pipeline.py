#!/usr/bin/env python
"""
Run the complete EDID parsing pipeline from start to finish.
Optionally clean all generated artifacts before running.
"""
import os
import sys
import shutil
import argparse
import subprocess
import time

# --- Configuration ---
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
OUTPUT_DATA_DIR = os.path.join(DATA_DIR, 'output')
FUNCTIONS_DIR = os.path.join(PROJECT_ROOT, 'functions')
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')

# Python interpreter from virtual environment
PYTHON_EXECUTABLE = os.path.join(PROJECT_ROOT, '.venv', 'Scripts', 'python.exe')

# --- Helper Functions ---
def ensure_directories():
    """Ensure all required directories exist."""
    for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUT_DATA_DIR, FUNCTIONS_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

def clean_artifacts():
    """Remove all generated artifacts."""
    # Clean data directories
    for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUT_DATA_DIR]:
        if os.path.exists(directory):
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Removed file: {file_path}")
    
    # Clean functions directory
    if os.path.exists(FUNCTIONS_DIR):
        for file in os.listdir(FUNCTIONS_DIR):
            if file.endswith('.py'):
                file_path = os.path.join(FUNCTIONS_DIR, file)
                os.remove(file_path)
                print(f"Removed function: {file_path}")
    
    print("All generated artifacts have been cleaned.")

def run_command(args, description, cwd=None):
    """Run a command with proper error handling."""
    print(f"\n{'='*80}\n{description}\n{'='*80}")
    print(f"Running: {' '.join(args)}")
    
    start_time = time.time()
    
    result = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
    elapsed_time = time.time() - start_time
    
    print(f"Command completed in {elapsed_time:.2f} seconds with exit code: {result.returncode}")
    
    if result.stdout:
        print("\nOutput:")
        print(result.stdout)
    
    if result.returncode != 0:
        print("\nError:")
        print(result.stderr)
        return False
    
    return True

def run_pipeline():
    """Run the complete pipeline from start to finish."""
    ensure_directories()
    
    # Copy example hex file to raw data directory if needed
    example_file = os.path.join(PROJECT_ROOT, 'example', '0839EBB5CAB9')
    example_hex_dest = os.path.join(RAW_DATA_DIR, 'example_hex.txt')
    if not os.path.exists(example_hex_dest) and os.path.exists(example_file):
        shutil.copy2(example_file, example_hex_dest)
        print(f"Copied example hex file to: {example_hex_dest}")
    
    # Step 1: Extract text from PDF
    if not run_command([PYTHON_EXECUTABLE, 'extract_pdf.py'], 
                      "Step 1: Extracting text from PDF", SCRIPTS_DIR):
        return False
    
    # Copy spec_chunks.json from raw to processed directory for discover_fields.py
    raw_chunks = os.path.join(RAW_DATA_DIR, 'spec_chunks.json')
    processed_chunks = os.path.join(PROCESSED_DATA_DIR, 'spec_chunks.json')
    if os.path.exists(raw_chunks):
        shutil.copy2(raw_chunks, processed_chunks)
        print(f"Copied spec_chunks.json from {raw_chunks} to {processed_chunks}")
    
    # Step 2: Extract hex data to binary
    if not run_command([PYTHON_EXECUTABLE, 'extract_hex_to_bin.py'], 
                      "Step 2: Converting hex data to binary", SCRIPTS_DIR):
        return False
    
    # Step 3: Generate embeddings and store in FAISS index
    if not run_command([PYTHON_EXECUTABLE, 'embed_store.py'], 
                      "Step 3: Generating embeddings and FAISS index", SCRIPTS_DIR):
        return False
    
    # Step 4: Discover fields from specification
    if not run_command([PYTHON_EXECUTABLE, 'discover_fields.py'], 
                      "Step 4: Discovering fields from specification", SCRIPTS_DIR):
        return False
    
    # Step 5: Map fields to specification chunks
    if not run_command([PYTHON_EXECUTABLE, 'map_fields.py'], 
                      "Step 5: Mapping fields to specification chunks", SCRIPTS_DIR):
        return False
    
    # Step 6: Generate parsing code for each field
    if not run_command([PYTHON_EXECUTABLE, 'generate_code.py'], 
                      "Step 6: Generating parsing code", SCRIPTS_DIR):
        return False
    
    # Step 7: Parse EDID binary data
    if not run_command([PYTHON_EXECUTABLE, 'parse_edid.py'], 
                      "Step 7: Parsing EDID binary data", SCRIPTS_DIR):
        return False
    
    print("\n" + "="*80)
    print("Pipeline completed successfully!")
    print("="*80)
    print(f"\nParsed EDID data saved to: {os.path.join(OUTPUT_DATA_DIR, 'parsed_edid.json')}")
    return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Run the EDID parsing pipeline from start to finish.')
    parser.add_argument('--clean', '-c', action='store_true',
                        help='Clean all generated artifacts before running the pipeline')
    args = parser.parse_args()
    
    if args.clean:
        clean_artifacts()
    
    success = run_pipeline()
    if not success:
        print("\nPipeline execution failed. See error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
