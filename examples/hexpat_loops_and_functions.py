#!/usr/bin/env python
"""
Example script demonstrating how to use for loops and library functions
with the BFIR to HexPat converter.
"""

import sys
import json
from pathlib import Path

# Add the parent directory to the path so we can import the converter
sys.path.append(str(Path(__file__).parent.parent))

from bfir.converters.hexpat.converter import BFIRToHexPatConverter

def create_example_bfir():
    """Create a simple BFIR example that will use loops and library functions."""
    return {
        "format": {
            "name": "LoopAndFunctionExample",
            "version": "1.0",
            "description": "Example format demonstrating loops and library functions",
            "endianness": "little"
        },
        "fields": [
            {
                "name": "Header",
                "type": "struct",
                "description": "Example header with array that will use a loop",
                "fields": [
                    {
                        "name": "Magic",
                        "type": "simple_value",
                        "size": 4,
                        "description": "Magic number"
                    },
                    {
                        "name": "Values",
                        "type": "simple_value",
                        "size": 40,  # 10 u32 values
                        "description": "Array of 10 values that will be processed with a loop"
                    }
                ]
            }
        ]
    }

def main():
    """Main function demonstrating the use of for loops and library functions."""
    # Create example BFIR
    bfir_data = create_example_bfir()
    
    # Create converter instance
    converter = BFIRToHexPatConverter(bfir_data)
    
    # Example of using the for loop generator
    loop_body = [
        "u32 value = values[i];",
        "// Process each value",
        "result[i] = std::math::pow(value, 2);"
    ]
    
    for_loop = converter._generate_for_loop(
        init_var="u8 i", 
        init_value=0, 
        condition="i < 10", 
        increment="i = i + 1",
        body_lines=loop_body
    )
    
    # Example of using the function call generator
    function_call = converter._generate_function_call(
        namespace="std.math",
        function="pow",
        args=["value", "2"]
    )
    
    # Print examples
    print("Example BFIR:")
    print(json.dumps(bfir_data, indent=2))
    print("\nGenerated For Loop:")
    print("\n".join(for_loop))
    print("\nGenerated Function Call:")
    print(function_call)
    print("\nRequired Libraries:")
    print(converter.required_libraries)
    
    # Generate complete HexPat template
    hexpat = converter.convert()
    
    # Save to file
    output_file = Path(__file__).parent / "loop_function_example.hexpat"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(hexpat)
        
    # Now add a custom example with loops and functions
    custom_hexpat = """
// Custom example with loops and functions
import std.math;
import std.string;

struct ProcessedData {
    u32 original;
    u32 processed;
};

fn process_value(u32 value) {
    return std::math::pow(value, 2);
}

struct Example {
    u32 magic;
    u32 values[10];
    ProcessedData results[10];
    
    fn calculate_results() {
        for (u8 i = 0, i < 10, i = i + 1) {
            results[i].original = values[i];
            results[i].processed = process_value(values[i]);
        }
    }
};

Example example @ 0x00;
"""
    
    # Save custom example
    custom_file = Path(__file__).parent / "custom_loop_function_example.hexpat"
    with open(custom_file, "w", encoding="utf-8") as f:
        f.write(custom_hexpat)
    
    print(f"\nSaved example HexPat to {output_file}")
    print(f"Saved custom example to {custom_file}")
    
if __name__ == "__main__":
    main()
