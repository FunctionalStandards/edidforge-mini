# Binary Format Intermediate Representation (BFIR)

## Overview

The Binary Format Intermediate Representation (BFIR) is a structured JSON format designed to represent binary data formats in a consistent, format-agnostic way. It serves as an intermediate layer between binary format specifications and various output formats such as HexPat templates, parsers, and documentation.

## Project Objectives

1. **Format-Agnostic Representation**: Define a JSON schema that can represent any binary format structure (EDID, USB descriptors, file formats, etc.)
2. **Extensible Design**: Allow for future extensions without breaking existing implementations
3. **Decoupled Converters**: Support multiple output formats through dedicated converters
4. **Structured Metadata**: Capture all necessary information about fields, including types, offsets, and relationships

## Project Structure

```
bfir/
├── schema/               # JSON Schema definition for BFIR
│   └── bfir_schema.json  # Formal schema specification
├── converters/           # Converters for different output formats
│   └── hexpat/           # ImHex pattern language converter
│       └── converter.py  # BFIR to HexPat converter implementation
└── examples/             # Example BFIR files
    └── edid_bfir_example.json  # Example EDID representation in BFIR
```

## BFIR Schema

The BFIR schema defines a structured way to represent binary formats with the following key components:

- **Format Metadata**: Name, version, endianness, and description
- **Field Definitions**: Hierarchical structure of fields with types, sizes, and offsets
- **Relationships**: Parent-child relationships between fields
- **Type Information**: Detailed type information including bit fields, enums, and arrays

See `schema/bfir_schema.json` for the complete schema definition.

## Converters

Converters transform BFIR into specific output formats:

### HexPat Converter

The HexPat converter (`converters/hexpat/converter.py`) transforms BFIR into ImHex pattern language files (`.hexpat`). It handles:

- Struct definitions
- Bit fields
- Enums
- Arrays
- Comments and metadata

## Usage

### Converting BFIR to HexPat

```bash
python bfir/converters/hexpat/converter.py input.json output.hexpat
```

### Integration with EDID Forge Mini

BFIR is designed to integrate with the EDID Forge Mini pipeline:

1. The binary structure analysis step outputs BFIR-compliant JSON
2. The BFIR to HexPat converter generates the final template

## Future Extensions

The BFIR project is designed to be extended in the following ways:

1. **Additional Converters**: Support for other output formats (C structs, Python classes, etc.)
2. **Schema Evolution**: Versioned schema to accommodate new binary format features
3. **Validation Tools**: Tools to validate BFIR against known binary formats
4. **Visualization**: Tools to visualize binary structures defined in BFIR

## Contributing

When extending BFIR, please follow these guidelines:

1. Maintain backward compatibility with existing BFIR files
2. Document any schema changes thoroughly
3. Update converters to handle new schema features
4. Add examples demonstrating new capabilities
