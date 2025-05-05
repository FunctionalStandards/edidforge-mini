#pragma endian little

// Simple struct definition
struct Header {
    u8 magic[8];
};

// Nested struct definition
struct EDID {
    Header header @ 0x00;
    
    struct ManufacturerID {
        u16 id;
    } manufacturer @ 0x08;
    
    u16 product_code @ 0x0A;
    u32 serial_number @ 0x0C;
};

// Place the main struct at the beginning
EDID edid @ 0x00;
