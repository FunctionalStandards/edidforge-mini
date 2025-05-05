#!/usr/bin/env python
"""
Run the complete EDID parsing pipeline from start to finish.
Optionally clean all generated artifacts before running.
"""
import sys
import shutil
import argparse
import subprocess
import time
import datetime
from pathlib import Path

# --- Configuration ---
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
OUTPUT_DATA_DIR = DATA_DIR / 'output'
FUNCTIONS_DIR = PROJECT_ROOT / 'functions'
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'
LOGS_DIR = PROJECT_ROOT / 'logs'

# Python interpreter from virtual environment
PYTHON_EXECUTABLE = PROJECT_ROOT / '.venv' / 'Scripts' / 'python.exe'

# --- Logging Setup ---
class TeeLogger:
    """Custom logger that writes to both console and log file."""
    
    def __init__(self, log_file):
        self.terminal = sys.stdout
        self.log_file = log_file
        
    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()  # Ensure log is written immediately
        
    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

def setup_logging():
    """Set up logging to both console and file."""
    # Create logs directory if it doesn't exist
    if not LOGS_DIR.exists():
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped log filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = LOGS_DIR / f"pipeline_run_{timestamp}.log"
    
    # Open log file and redirect stdout/stderr
    log_file = open(log_filename, 'w', encoding='utf-8')
    sys.stdout = TeeLogger(log_file)
    
    print(f"=== EDID Forge Mini Pipeline Run - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    print(f"Log file: {log_filename}")
    
    return log_file

def cleanup_logging(log_file):
    """Clean up logging resources."""
    sys.stdout = sys.__stdout__  # Restore original stdout
    if log_file:
        log_file.close()

# --- Helper Functions ---
def ensure_directories():
    """
    Ensure all required directories exist for the pipeline.
    
    This function creates the following directory structure if it doesn't exist:
    - data/
      - raw/       : For raw extracted data from PDFs and hex files
      - processed/ : For intermediate processed data
      - output/    : For final output files
    - functions/   : For generated parsing functions
    - logs/        : For pipeline run logs
    """
    for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUT_DATA_DIR, FUNCTIONS_DIR, LOGS_DIR]:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")

def clean_artifacts():
    """Remove all generated artifacts."""
    # Clean data directories
    for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUT_DATA_DIR]:
        if directory.exists():
            for file in directory.iterdir():
                if file.is_file():
                    file.unlink()
                    print(f"Removed file: {file}")
    
    # Clean functions directory
    if FUNCTIONS_DIR.exists():
        for file in FUNCTIONS_DIR.iterdir():
            if file.name.endswith('.py'):
                file.unlink()
                print(f"Removed function: {file}")
    
    print("All generated artifacts have been cleaned.")

def run_command(args, description, cwd=None):
    """Run a command with proper error handling."""
    print(f"\n{'='*80}\n{description}\n{'='*80}")
    print(f"Running: {' '.join(str(arg) for arg in args)}")
    
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
    # Copy example hex file to raw data directory if needed
    example_file = PROJECT_ROOT / 'example' / '0839EBB5CAB9'
    example_hex_dest = RAW_DATA_DIR / 'example_hex.txt'
    if not example_hex_dest.exists() and example_file.exists():
        shutil.copy2(example_file, example_hex_dest)
        print(f"Copied example hex file to: {example_hex_dest}")
    
    # Log the input hex data if available
    if example_file.exists():
        print("\n" + "="*80)
        print("INPUT HEX DATA")
        print("="*80)
        try:
            with example_file.open('r', encoding='utf-8') as f:
                hex_data = f.read()
                print(hex_data)
        except Exception as e:
            print(f"Error reading hex data: {e}")
    
    # Step 1: Extract text from PDF
    if not run_command([PYTHON_EXECUTABLE, 'extract_pdf.py'], 
                      "Step 1: Extracting text from PDF", SCRIPTS_DIR):
        return False
    
    # Copy spec_chunks.json from raw to processed directory for discover_fields.py
    raw_chunks = RAW_DATA_DIR / 'spec_chunks.json'
    processed_chunks = PROCESSED_DATA_DIR / 'spec_chunks.json'
    if raw_chunks.exists():
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
    
    # Step 8: Analyze binary structure of fields
    if not run_command([PYTHON_EXECUTABLE, 'binary_structure_analysis.py'], 
                      "Step 8: Analyzing binary structure of fields", SCRIPTS_DIR):
        return False
    
    # Step 9: Generate BFIR from enhanced field definitions
    if not run_command([PYTHON_EXECUTABLE, 'bfir_pipeline.py', '--skip-analysis', '--skip-hexpat'], 
                      "Step 9: Converting to BFIR format", SCRIPTS_DIR):
        return False
    
    # Step 10: Generate HexPat template (original method)
    if not run_command([PYTHON_EXECUTABLE, 'generate_hexpat.py'], 
                      "Step 10: Generating HexPat template (original method)", SCRIPTS_DIR):
        return False
    
    # Step 11: Generate HexPat template from BFIR
    if not run_command([PYTHON_EXECUTABLE, 'generate_bfir_hexpat.py'], 
                      "Step 11: Generating HexPat template from BFIR", SCRIPTS_DIR):
        return False
    
    print("\n" + "="*80)
    print("Pipeline completed successfully!")
    print("="*80)
    
    output_json_path = OUTPUT_DATA_DIR / 'parsed_edid.json'
    print(f"\nParsed EDID data saved to: {output_json_path}")
    
    # Log the output JSON if available
    if output_json_path.exists():
        print("\n" + "="*80)
        print("OUTPUT JSON")
        print("="*80)
        try:
            with output_json_path.open('r', encoding='utf-8') as f:
                json_data = f.read()
                print(json_data)
        except Exception as e:
            print(f"Error reading output JSON: {e}")
    
    # Log the HexPat template if available
    output_hexpat_path = OUTPUT_DATA_DIR / 'edid.hexpat'
    if output_hexpat_path.exists():
        print("\n" + "="*80)
        print("HEXPAT TEMPLATE (ORIGINAL METHOD)")
        print("="*80)
        try:
            with output_hexpat_path.open('r', encoding='utf-8') as f:
                hexpat_data = f.read()
                # Print first 20 lines of the template
                hexpat_lines = hexpat_data.split('\n')
                print('\n'.join(hexpat_lines[:20]))
                if len(hexpat_lines) > 20:
                    print(f"\n... (and {len(hexpat_lines) - 20} more lines)")
        except Exception as e:
            print(f"Error reading HexPat template: {e}")
    
    # Log the BFIR-generated HexPat template if available
    bfir_hexpat_path = OUTPUT_DATA_DIR / 'bfir_generated.hexpat'
    if bfir_hexpat_path.exists():
        print("\n" + "="*80)
        print("HEXPAT TEMPLATE (BFIR METHOD)")
        print("="*80)
        try:
            with bfir_hexpat_path.open('r', encoding='utf-8') as f:
                bfir_hexpat_data = f.read()
                # Print first 20 lines of the template
                bfir_hexpat_lines = bfir_hexpat_data.split('\n')
                print('\n'.join(bfir_hexpat_lines[:20]))
                if len(bfir_hexpat_lines) > 20:
                    print(f"\n... (and {len(bfir_hexpat_lines) - 20} more lines)")
        except Exception as e:
            print(f"Error reading BFIR-generated HexPat template: {e}")
    
    return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Run the EDID parsing pipeline from start to finish.')
    parser.add_argument('--clean', '-c', action='store_true',
                        help='Clean all generated artifacts before running the pipeline')
    args = parser.parse_args()
    
    # Set up logging
    log_file = setup_logging()
    
    try:
        # Always ensure directories exist first
        ensure_directories()
        
        if args.clean:
            clean_artifacts()
        
        success = run_pipeline()
        if not success:
            print("\nPipeline execution failed. See error messages above.")
            sys.exit(1)
    finally:
        # Clean up logging resources
        cleanup_logging(log_file)

if __name__ == "__main__":
    main()
