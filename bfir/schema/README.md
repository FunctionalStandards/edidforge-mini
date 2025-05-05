# BFIR Schema

## Overview

The Binary Format Intermediate Representation (BFIR) schema defines a structured JSON format for representing binary data formats. This schema serves as the foundation for the entire BFIR ecosystem, ensuring consistency and interoperability between different tools and converters.

## Schema Design Principles

1. **Completeness**: Capture all necessary information about binary structures
2. **Flexibility**: Support a wide range of binary format constructs
3. **Extensibility**: Allow for future extensions without breaking existing implementations
4. **Clarity**: Use clear, self-documenting field names and structures

## Schema Structure

The BFIR schema consists of two main sections:

### Format Metadata

```json
"format": {
  "name": "EDID",
  "version": "1.3",
  "endianness": "little",
  "description": "Extended Display Identification Data"
}
```

This section describes the overall binary format, including:

- **name**: The name of the binary format
- **version**: The version of the format specification
- **endianness**: The byte order used by the format (big, little, or mixed)
- **description**: A human-readable description of the format

### Fields

```json
"fields": [
  {
    "id": "header",
    "name": "Header",
    "description": "Fixed 8-byte pattern",
    "offset": "0x00-0x07",
    "size": 8,
    "type": "fixed_pattern",
    "value_type": "binary"
  }
]
```

This section defines the fields that make up the binary structure:

- **id**: A unique identifier for the field
- **name**: A human-readable name for the field
- **description**: A detailed description of the field's purpose
- **parent**: The ID of the parent field (for nested structures)
- **offset**: The byte offset(s) where the field appears in the binary data
- **size**: The size of the field in bytes
- **type**: The structural type of the field (simple_value, bit_fields, enum, struct, etc.)
- **value_type**: The data type of the field (uint8, uint16, string, etc.)

## Field Types

The schema supports several field types:

### Simple Value

A basic value of a specific type:

```json
{
  "id": "year",
  "name": "Year of Manufacture",
  "type": "simple_value",
  "value_type": "uint8"
}
```

### Bit Fields

A set of bit fields within a larger value:

```json
{
  "id": "features",
  "name": "Feature Support",
  "type": "bit_fields",
  "bit_fields": [
    {
      "name": "standby",
      "description": "Standby mode supported",
      "bits": 1
    },
    {
      "name": "suspend",
      "description": "Suspend mode supported",
      "bits": 1
    }
  ]
}
```

### Enum

A field with predefined values:

```json
{
  "id": "color_depth",
  "name": "Color Depth",
  "type": "enum",
  "value_type": "uint8",
  "enum_values": {
    "8-bit": 0,
    "16-bit": 1,
    "24-bit": 2,
    "32-bit": 3
  }
}
```

### Struct

A composite field containing other fields:

```json
{
  "id": "vendor_info",
  "name": "Vendor Information",
  "type": "struct"
}
```

### Array

An array of values:

```json
{
  "id": "timings",
  "name": "Standard Timings",
  "type": "array",
  "size": 8,
  "element_type": {
    "value_type": "uint16"
  }
}
```

## Schema Validation

The `bfir_schema.json` file is a formal JSON Schema that can be used to validate BFIR files. To validate a BFIR file against the schema:

```python
import jsonschema
import json

# Load the schema
with open("bfir_schema.json", "r") as f:
    schema = json.load(f)

# Load a BFIR file
with open("example.json", "r") as f:
    bfir = json.load(f)

# Validate
jsonschema.validate(bfir, schema)
```

## Schema Evolution

As binary formats evolve and new requirements emerge, the BFIR schema may need to be extended. When extending the schema:

1. Maintain backward compatibility where possible
2. Use versioning for breaking changes
3. Document all changes thoroughly
4. Update converters to handle new schema features
