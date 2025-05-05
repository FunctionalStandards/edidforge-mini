#pragma endian little

// EDID Pattern for ImHex
// Manually created template based on BFIR example

// Forward declaration of the ManufacturerID struct
using ManufacturerID;

// Manufacturer ID bit fields
bitfield ManufacturerID {
    char1 : 5;  // First character (5 bits, A-Z)
    char2 : 5;  // Second character (5 bits, A-Z)
    char3 : 5;  // Third character (5 bits, A-Z)
    reserved : 1;  // Reserved bit
};

// Vendor & Product Identification
struct VendorProduct {
    ManufacturerID manufacturerID;
    u16 productCode;  // Manufacturer assigned product code
    u32 serialNumber;  // 32-bit serial number
    u8 weekOfManufacture;  // Week number when the display was manufactured
    u8 yearOfManufacture;  // Year of manufacture minus 1990
};

// Main EDID structure
struct EDID {
    u8 header[8];  // Fixed 8-byte pattern (00 FF FF FF FF FF FF 00)
    VendorProduct vendorProduct;
    
    // Version and revision
    u8 versionNumber;
    u8 revisionNumber;
};

// Place the EDID structure at the beginning of the file
EDID edid @ 0x00;
