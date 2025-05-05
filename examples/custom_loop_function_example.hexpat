// Custom example with loops and functions
import std.math;
import std.string;

struct ProcessedData {
    u32 original;
    u32 processed;
};

struct Example {
    u32 magic;
    u32 values[10];
    ProcessedData results[10];
};

Example example @ 0x00;

fn process_value(u32 value) {
    return std::math::pow(value, 2);
};

fn calculate_results() {
    for (u8 i = 0, i < 10, i = i + 1) {
        example.results[i].original = example.values[i];
        example.results[i].processed = process_value(example.values[i]);
    }
};
