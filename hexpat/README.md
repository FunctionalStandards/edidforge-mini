# ImHex Patterns for Display Standards

This directory contains ImHex pattern language (HexPat) templates for analyzing binary data related to display standards.

## Available Patterns

### EDID (Extended Display Identification Data)

We provide two HexPat templates for EDID analysis:

1. **Standard EDID Template** (`patterns/edid.hexpat`) - A basic template for parsing 128-byte base EDID data
2. **Enhanced EDID Template** (`patterns/edid_enhanced.hexpat`) - A more comprehensive template with improved structure and helper functions

#### Standard EDID Template

The `patterns/edid.hexpat` file provides a template for parsing standard 128-byte base EDID binary data according to the VESA E-EDID standard. This template was created based on parametric knowledge of the EDID structure without direct reference to the official documentation.

#### Enhanced EDID Template

The `patterns/edid_enhanced.hexpat` file is an improved version of the standard template created with detailed reference to approximately 30 pages of the official VESA E-EDID standard documentation. This comprehensive template includes the following enhancements:

- More accurate bit-level encoding based on the official E-EDID standard documentation
- Better organization with clear section headers and byte offset comments
- Helper functions for decoding manufacturer IDs, calculating gamma values, and handling aspect ratios
- Proper handling of descriptor blocks with appropriate type detection
- Improved chromaticity coordinate calculations
- More detailed comments explaining encoding rules and value ranges

#### Differences Between Templates

| Feature | Standard Template | Enhanced Template |
|---------|------------------|-------------------|
| Structure Organization | Basic sections | Clearly labeled sections with byte offsets |
| Bit Field Handling | Basic implementation | Improved with `[[hidden]]` attributes for conditional fields |
| Helper Functions | None | Includes functions for decoding values and calculations |
| Chromaticity Handling | Basic | Includes binary fraction conversion |
| Comments | Basic field descriptions | Detailed explanations of encoding rules and ranges |
| Descriptor Handling | Simple approach | Comprehensive enum for all descriptor types |

#### Usage

1. Open ImHex and load an EDID binary file
2. Go to File > Import > Pattern
3. Select either `edid.hexpat` or `edid_enhanced.hexpat`
4. The EDID structure will be parsed and displayed in the Pattern Data view

#### EDID Structure Overview

Both templates cover all major sections of the EDID:

1. **Header and Manufacturer Information** (bytes 0-19)
   - 8-byte fixed header pattern
   - Manufacturer ID (3-character code)
   - Product code, serial number, manufacture date
   - EDID version and revision

2. **Basic Display Parameters** (bytes 20-24)
   - Video input definition (analog/digital)
   - Screen dimensions
   - Gamma
   - Feature support (DPMS, display type, color space)

3. **Color Characteristics** (bytes 25-34)
   - Chromaticity coordinates for red, green, blue, and white point

4. **Established Timings** (bytes 35-37)
   - Bitmap of standard timings (VGA, SVGA, XGA, etc.)

5. **Standard Timing Information** (bytes 38-53)
   - 8 standard timing blocks with resolution and refresh rate

6. **Detailed Timing Descriptors** (bytes 54-125)
   - First detailed timing (preferred timing if indicated)
   - Three additional display descriptors (names, ranges, etc.)

7. **Extension Flag and Checksum** (bytes 126-127)
   - Number of extension blocks
   - Checksum byte

## Relationship to BFIR

These HexPat templates were created as reference implementations to compare with the output of the Binary Format Intermediate Representation (BFIR) to HexPat converter. They demonstrate the correct ImHex pattern language syntax for representing complex binary structures.

The key syntax elements demonstrated include:

1. Forward declarations using the `using TypeName;` syntax
2. Bit fields defined with the `bitfield` keyword
3. C-style comments for field descriptions
4. Proper struct field declarations with semicolons
5. Array definitions with square brackets
6. Helper functions with proper ImHex pattern language syntax

## Future Extensions

These templates can be extended to support:

1. EDID extension blocks (CEA, DisplayID, etc.)
2. Other display-related binary formats (DisplayPort DPCD, HDMI EDID extensions)
3. Additional analysis functions for calculating display parameters

## References

- VESA E-EDID Standard Release A, Rev. 2
- [ImHex Pattern Language Documentation](https://docs.werwolv.net/pattern-language)
