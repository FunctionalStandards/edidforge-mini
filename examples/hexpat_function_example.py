#!/usr/bin/env python
"""
Example script demonstrating how to use the function declaration capabilities
with the BFIR to HexPat converter.
"""

import sys
import json
from pathlib import Path

# Add the parent directory to the path so we can import the converter
sys.path.append(str(Path(__file__).parent.parent))

from bfir.converters.hexpat.converter import BFIRToHexPatConverter

def main():
    """Main function demonstrating the use of function declarations."""
    # Create a simple converter instance
    converter = BFIRToHexPatConverter({"format": {"name": "FunctionExample"}})
    
    # Example of using the function declaration generator
    params = [
        {"type": "u16", "name": "value"},
        {"type": "u8", "name": "multiplier"}
    ]
    
    body_lines = [
        "// Calculate the result using math library",
        "float base = std::math::pow(value, 2);",
        "return base * multiplier;"
    ]
    
    function_declaration = converter._generate_function_declaration(
        function_name="calculateValue",
        params=params,
        body_lines=body_lines
    )
    
    # Example of using the function call generator
    function_call = converter._generate_function_call(
        namespace="std.math",
        function="pow",
        args=["value", "2"]
    )
    
    # Print examples
    print("Generated Function Declaration:")
    print("\n".join(function_declaration))
    print("\nGenerated Function Call:")
    print(function_call)
    print("\nRequired Libraries:")
    print(converter.required_libraries)
    
    # Create a complete example
    complete_example = [
        "// Function example with proper ImHex syntax",
        "import std.math;",
        "",
        *function_declaration,
        "",
        "struct Example {",
        "    u16 value;",
        "    u8 multiplier;",
        "",
        "    fn processValue() {",
        "        return calculateValue(value, multiplier);",
        "    };",
        "};",
        "",
        "Example example @ 0x00;"
    ]
    
    # Save to file
    output_file = Path(__file__).parent / "function_example.hexpat"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(complete_example))
    
    print(f"\nSaved example HexPat to {output_file}")
    
if __name__ == "__main__":
    main()
