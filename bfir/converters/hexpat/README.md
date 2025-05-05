# BFIR to HexPat Converter

## Overview

This converter transforms Binary Format Intermediate Representation (BFIR) JSON files into ImHex pattern language files (HexPat).

## Features

- **Complete Structure Generation**: Creates a full HexPat template with proper struct definitions
- **Type Mapping**: Maps BFIR types to appropriate HexPat types
- **Bit Field Support**: Correctly handles bit fields with proper alignment
- **Enum Generation**: Creates enum definitions for enumerated values
- **Comment Preservation**: Maintains field descriptions as HexPat comments
- **Offset Annotations**: Includes original byte offsets as comments

## Usage

```python
from bfir.converters.hexpat.converter import BFIRToHexPatConverter

# Load BFIR JSON
with open('path/to/bfir.json', 'r') as f:
    bfir_data = json.load(f)

# Create converter
converter = BFIRToHexPatConverter(bfir_data)

# Convert to HexPat
hexpat_content = converter.convert()

# Write to file
with open('output.hexpat', 'w') as f:
    f.write(hexpat_content)
```

You can also use the converter directly from the command line:

```bash
python converter.py path/to/bfir.json output.hexpat
```

## ImHex Pattern Language Syntax

The converter follows these ImHex pattern language syntax requirements:

1. **Forward Declarations**: Use `using TypeName;` to declare types before they're used
2. **Struct Definitions**: Define structs with proper field types and semicolons
3. **Bit Fields**: Use the `bitfield` keyword for bit field definitions:

   ```hexpat
   bitfield MyBitField {
       field1 : 3;  // 3 bits
       field2 : 5;  // 5 bits
   };
   ```

4. **Comments**: Use C-style comments (`// comment`) for field descriptions
5. **Arrays**: Define arrays with square brackets after the field name
6. **Placement**: Place the main struct at a specific offset using `@ 0x00` syntax

## Supported BFIR Field Types

The converter supports the following BFIR field types:

- `simple_value`: Basic numeric values (u8, u16, u32, u64)
- `struct`: Composite types with multiple fields
- `bit_fields`: Bit-level fields within a byte or word
- `fixed_pattern`: Fixed byte patterns (converted to byte arrays)
- `enum`: Enumerated values (with named constants)
- `array`: Arrays of any other type

## Known Limitations

- Nested bit fields are not currently supported
- Custom types beyond the basic ImHex types are not supported
- Some advanced ImHex features (like custom colors, references) are not implemented

## Type Mapping

| BFIR Type | HexPat Type |
|-----------|-------------|
| uint8     | u8          |
| uint16    | u16         |
| uint32    | u32         |
| uint64    | u64         |
| int8      | s8          |
| int16     | s16         |
| int32     | s32         |
| int64     | s64         |
| float     | float       |
| double    | double      |
| char      | char        |
| string    | char[]      |
| binary    | u8[]        |

## Known Issues

- Array size handling needs improvement for certain field types
- Bit field alignment may need adjustment for complex structures
- Nested structs with variable sizes need special handling

## Future Improvements

- Add validation of the generated HexPat syntax
- Support for custom patterns and complex types
- Better handling of endianness at the field level
- Support for unions and conditional fields

## Example

See the `examples` directory for sample BFIR files and their corresponding HexPat outputs.
