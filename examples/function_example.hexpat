// Function example with proper ImHex syntax
import std.math;

struct Example {
    u16 value;
    u8 multiplier;
};

Example example @ 0x00;

fn calculateValue(u16 value, u8 multiplier) {
    // Calculate the result using math library
    float base = std::math::pow(value, 2);
    return base * multiplier;
};

fn processValue() {
    return calculateValue(example.value, example.multiplier);
};