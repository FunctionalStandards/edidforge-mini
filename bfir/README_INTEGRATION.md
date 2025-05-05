# BFIR Integration Guide

This document explains how the Binary Format Intermediate Representation (BFIR) is integrated into the EDIDForge pipeline.

## Overview

The BFIR integration connects the binary structure analysis with the HexPat template generation, providing a standardized intermediate format that can be used for multiple output formats.

```mermaid
┌─────────────────┐     ┌─────────────┐     ┌───────────────┐
│ Binary Structure │     │             │     │ HexPat        │
│ Analysis         │────▶│ BFIR JSON   │────▶│ Template      │
└─────────────────┘     │             │     └───────────────┘
                        └─────────────┘
```

## Pipeline Components

1. **Binary Structure Analysis** (`scripts/binary_structure_analysis.py`)
   - Analyzes EDID field definitions
   - Extracts detailed binary encoding information
   - Outputs enhanced field definitions

2. **BFIR Conversion** (`scripts/bfir_pipeline.py`)
   - Converts enhanced field definitions to BFIR format
   - Standardizes field types, bit fields, enums, and structs
   - Outputs BFIR JSON

3. **HexPat Generation** (`scripts/generate_bfir_hexpat.py`)
   - Uses the BFIR to HexPat converter
   - Generates syntactically correct ImHex pattern files
   - Outputs .hexpat template files

## Running the Pipeline

To run the complete pipeline:

```bash
cd scripts
python bfir_pipeline.py
```

### Command Line Options

- `--skip-analysis`: Skip the binary structure analysis step
- `--skip-hexpat`: Skip the HexPat generation step

Example:

```bash
# Run only the BFIR conversion (skip analysis and HexPat generation)
python bfir_pipeline.py --skip-analysis --skip-hexpat

# Run analysis and BFIR conversion, but skip HexPat generation
python bfir_pipeline.py --skip-hexpat
```

## File Locations

- **Input Files**:
  - Enhanced field definitions: `data/processed/enhanced_field_definitions.json`

- **Output Files**:
  - BFIR JSON: `data/processed/bfir_output.json`
  - Generated HexPat: `data/output/bfir_generated.hexpat`

## Extending the Pipeline

The BFIR format is designed to be extensible. To add support for additional output formats:

1. Create a new converter in the `bfir/converters/` directory
2. Implement the conversion logic from BFIR to your target format
3. Create a script to integrate the converter into the pipeline

## Troubleshooting

If you encounter issues with the pipeline:

1. Check the enhanced field definitions for completeness
2. Verify that the BFIR JSON is correctly formatted
3. Ensure the HexPat converter is generating valid syntax
4. Consult the [ImHex pattern language documentation](https://docs.werwolv.net/pattern-language) for syntax questions

For more information on BFIR itself, see the main [BFIR README](../bfir/README.md).
