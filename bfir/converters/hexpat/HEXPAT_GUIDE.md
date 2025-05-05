# ImHex Pattern Language Guide

This document provides a comprehensive guide to the ImHex pattern language (HexPat) syntax and best practices, based on our experience developing the BFIR to HexPat converter and creating patterns for binary formats like EDID.

## Basic Syntax

### File Structure

A typical HexPat file follows this structure:

```hexpat
#pragma endian little  // or big

// Forward declarations
using TypeA;
using TypeB;

// Type definitions (bitfields, enums, structs)
bitfield TypeA {
    field1 : 3;  // 3 bits
    field2 : 5;  // 5 bits
};

enum TypeB : u8 {
    ValueA = 0x01,
    ValueB = 0x02
};

struct MainType {
    TypeA fieldA;
    TypeB fieldB;
    u8 simpleField;
};

// Placement at file offset
MainType instance @ 0x00;
```

### Pragmas

Pragmas are directives that control how the pattern is interpreted:

```hexpat
#pragma endian little  // Set endianness to little-endian
#pragma endian big     // Set endianness to big-endian
#pragma pattern_limit 0x1000  // Limit pattern parsing to first 0x1000 bytes
```

## Type System

### Basic Types

ImHex provides the following built-in types:

- Unsigned integers: `u8`, `u16`, `u32`, `u64`
- Signed integers: `s8`, `s16`, `s32`, `s64`
- Floating point: `float`, `double`
- Characters: `char`
- Boolean: `bool`

### Arrays

Arrays are defined by appending square brackets with a size to a type:

```hexpat
u8 buffer[16];  // 16-byte array
char string[10];  // 10-character string
```

### Structs

Structs are defined using the `struct` keyword:

```hexpat
struct Point {
    u32 x;  // Note the semicolon after each field
    u32 y;
};
```

### Bitfields

Bitfields must be defined using the `bitfield` keyword, not inside structs:

```hexpat
bitfield Flags {
    flag1 : 1;  // 1 bit
    flag2 : 1;
    value : 6;  // 6 bits
};
```

### Enums

Enums are defined using the `enum` keyword:

```hexpat
enum ColorType : u8 {
    RGB = 0,
    CMYK = 1,
    HSV = 2
};
```

## Forward Declarations

ImHex requires forward declarations for types that are used before they are defined. Use the `using` keyword:

```hexpat
using TypeName;  // Forward declaration
```

**Important**: Use `using TypeName;` instead of `struct TypeName;` for forward declarations.

## Comments

ImHex supports C-style comments:

```hexpat
// Single-line comment

/* 
   Multi-line
   comment
*/
```

Field comments should use `//` style comments, not attributes:

```hexpat
u8 field;  // This is correct
u8 field;  /* This is also correct */
```

## Placement

To place a pattern at a specific offset in the file:

```hexpat
MainType instance @ 0x00;  // Place at offset 0
```

## Nested Types vs. Separate Types

### Approach 1: Nested Types (Not Recommended)

```hexpat
struct OuterType {
    struct InnerType {
        u8 field1;
        u16 field2;
    } inner;
    
    u32 outerField;
};
```

### Approach 2: Separate Types (Recommended)

```hexpat
struct InnerType {
    u8 field1;
    u16 field2;
};

struct OuterType {
    InnerType inner;
    u32 outerField;
};
```

The second approach is preferred as it:
1. Makes the code more readable
2. Allows reuse of types
3. Avoids nesting issues
4. Follows the ImHex pattern language design philosophy

## Common Pitfalls and Solutions

### 1. Bitfield Definition

**Incorrect:**
```hexpat
struct MyStruct {
    u8 field1 : 3;  // Error: Bit fields must be defined using the bitfield keyword
    u8 field2 : 5;
};
```

**Correct:**
```hexpat
bitfield MyBitfield {
    field1 : 3;
    field2 : 5;
};

struct MyStruct {
    MyBitfield fields;
};
```

### 2. Forward Declaration Syntax

**Incorrect:**
```hexpat
struct TypeName;  // Error: Wrong forward declaration syntax
```

**Correct:**
```hexpat
using TypeName;  // Correct forward declaration syntax
```

### 3. Missing Semicolons

**Incorrect:**
```hexpat
struct Point {
    u32 x  // Error: Missing semicolon
    u32 y
};
```

**Correct:**
```hexpat
struct Point {
    u32 x;  // Correct: Semicolon present
    u32 y;
};
```

### 4. Type Order

**Incorrect:**
```hexpat
struct User {
    Address address;  // Error: Address type not defined yet
};

struct Address {
    u8 street[50];
    u8 city[20];
};
```

**Correct:**
```hexpat
using Address;  // Forward declaration

struct Address {
    u8 street[50];
    u8 city[20];
};

struct User {
    Address address;  // Now it works
};
```

## Best Practices

1. **Define Types Before Use**
   - Use forward declarations with `using TypeName;`
   - Define types in dependency order
   - Consider implementing topological sorting for complex type hierarchies

2. **Bitfield Handling**
   - Always use the `bitfield` keyword for bit-level fields
   - Define bitfields as separate types
   - Use meaningful names for bitfield values

3. **Comments and Documentation**
   - Use C-style comments (`// comment`)
   - Document the purpose of each field
   - Include units and valid ranges where applicable
   - Add byte offset information for important fields

4. **Naming Conventions**
   - Use CamelCase for type names
   - Use camelCase or snake_case for field names
   - Be consistent throughout the pattern

5. **Structure Organization**
   - Group related fields together
   - Use comments to separate logical sections
   - Consider byte alignment in your structure design

6. **Reusability**
   - Define common structures as separate types
   - Use enums for constants and type codes
   - Consider creating a library of common patterns

## Advanced Features

### Attributes

ImHex supports attributes for additional metadata:

```hexpat
struct Point {
    u32 x [[color("FF0000")]];  // Highlighted in red
    u32 y [[comment("Y coordinate")]];  // With comment
};
```

Common attributes:
- `[[color("RRGGBB")]]`: Highlight with color
- `[[comment("text")]]`: Add comment
- `[[format("format string")]]`: Custom formatting

### Conditional Fields

Use if statements for conditional fields:

```hexpat
struct ConditionalStruct {
    u8 type;
    
    if (type == 1) {
        u32 typeOneData;
    } else if (type == 2) {
        u16 typeTwoData;
    }
};
```

## Conclusion

The ImHex pattern language is a powerful tool for analyzing binary data. By following these guidelines, you can create clear, maintainable, and effective patterns for any binary format.

This guide is based on our experience developing the BFIR to HexPat converter and creating patterns for binary formats like EDID. The syntax and best practices documented here should help future development efforts in creating ImHex patterns.
