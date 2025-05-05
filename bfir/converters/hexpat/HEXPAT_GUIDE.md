# ImHex Pattern Language Guide

This document provides a comprehensive guide to the ImHex pattern language (HexPat) syntax and best practices, based on our experience developing the BFIR to HexPat converter and creating patterns for binary formats like EDID.

> **Note**: This guide is based on our experience and may not cover all aspects of the ImHex pattern language. For the most up-to-date and comprehensive documentation, please refer to the [official ImHex pattern language documentation](https://docs.werwolv.net/pattern-language).

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

## Control Structures

### If Statements

ImHex supports standard if-else statements:

```hexpat
if (condition) {
    // Code executed if condition is true
} else if (another_condition) {
    // Code executed if another_condition is true
} else {
    // Code executed if no conditions are true
}
```

### For Loops

For loops in ImHex use commas instead of semicolons as separators:

```hexpat
// Correct for loop syntax
for (u8 i = 0, i < 10, i = i + 1) {
    // Loop body
}
```

Note these important differences from C/C++:

- Use commas (,) instead of semicolons (;) as separators
- Don't use shorthand increment operators like `i++` or `i += 1`
- Use explicit assignment: `i = i + 1` instead

### While Loops

While loops follow standard syntax:

```hexpat
u8 i = 0;
while (i < 10) {
    // Loop body
    i = i + 1;
}
```

## Library Functions

### Importing Libraries

ImHex uses dot notation for importing libraries:

```hexpat
import std.math;  // Import math library
import std.core;  // Import core library
```

### Using Library Functions

Despite using dot notation for imports, ImHex uses double colon notation for function calls:

```hexpat
// Import library
import std.math;

// Use library function (note the double colons)
float result = std::math::pow(2, 10);
```

This inconsistency between import syntax (dots) and function call syntax (double colons) is important to remember.

### Common Libraries

- `std.math`: Mathematical functions (pow, sqrt, etc.)
- `std.core`: Core utilities
- `std.mem`: Memory operations
- `std.string`: String manipulation

## Custom Functions

### Function Declaration and Placement

ImHex supports custom functions using the `fn` keyword. **Important**:

1. Function declarations must end with a semicolon after the closing brace
2. Functions should be defined after struct placement, not inside structs

```hexpat
// Define struct
struct Example {
    u32 value;
};

// Place struct at beginning of file
Example example @ 0x00;

// Define functions after struct placement
fn calculateValue(u32 input) {
    return input * 2;
}; // Note the semicolon here after the closing brace
```

### Function Parameters and Return Values

Functions can have multiple parameters and return values:

```hexpat
fn processData(u8 a, u16 b) {
    // Function body
    return a + b;
};
```

### Working with Struct Data

To access struct data from a function, use the variable name directly:

```hexpat
// Define and place struct
struct Example {
    u32 value;
};
Example example @ 0x00;

// Function that accesses struct data
fn processStruct() {
    return example.value * 2; // Direct access to struct instance
};
```

### Calling Custom Functions

Custom functions are called directly by name:

```hexpat
u32 result = calculateValue(10); // Calls the custom function

// To process struct data
processStruct(); // No need to pass the struct as a parameter
```

## Best Practices

1. **Define Types Before Use**
   - Always define structs, enums, and bitfields before using them
   - Use forward declarations when necessary

2. **Use Descriptive Names**
   - Choose clear, descriptive names for types and fields
   - Follow a consistent naming convention

3. **Add Comments**
   - Document the purpose of each field and struct
   - Include offset information for clarity

4. **Organize Related Fields**
   - Group related fields into separate structs
   - Use nested structs sparingly and only when appropriate

5. **Validate Your Patterns**
   - Test patterns with real data
   - Verify that all fields are correctly decoded

6. **Consult Official Documentation**
   - When in doubt, refer to the [official ImHex pattern language documentation](https://docs.werwolv.net/pattern-language)
   - Check examples in the [ImHex-Patterns repository](https://github.com/WerWolv/ImHex-Patterns) for guidance

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
