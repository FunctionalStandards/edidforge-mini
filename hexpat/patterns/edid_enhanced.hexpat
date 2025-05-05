#pragma endian little

// Enhanced EDID (Extended Display Identification Data) Pattern for ImHex
// Base EDID structure (128 bytes)
// Based on VESA E-EDID Standard Release A, Rev. 2
// Created based on official VESA documentation

// Import standard libraries
import std.math;

// Forward declarations
using ManufacturerID;
using VideoInputDefinition;
using FeatureSupport;
using RedGreenLowBits;
using BlueWhiteLowBits;
using EstablishedTiming1;
using EstablishedTiming2;
using EstablishedTiming3;
using StandardTimingAspectRatio;
using HorizontalVerticalHighBits;
using SyncDetails;
using DisplayDescriptorType;
using DisplayRangeLimitsOffsets;
using DetailedTimingDescriptor;
using DisplayDescriptor;

// ==================== HEADER (8 bytes) ====================
struct EDIDHeader {
    u8 headerPattern[8] @ 0x00; // Fixed pattern: 00 FF FF FF FF FF FF 00
};

// ==================== VENDOR & PRODUCT ID (10 bytes) ====================
// Manufacturer ID encoded in 2 bytes (5-bit compressed ASCII)
bitfield ManufacturerID {
    reserved : 1;  // Always 0
    char1 : 5;     // First character (5 bits, A-Z, 1=A, 26=Z)
    char2 : 5;     // Second character (5 bits, A-Z)
    char3 : 5;     // Third character (5 bits, A-Z)
};

struct VendorProductID {
    ManufacturerID manufacturerID @ 0x08;
    u16 productCode @ 0x0A;      // Manufacturer-assigned product code
    u32 serialNumber @ 0x0C;     // 32-bit serial number (optional)
    u8 manufactureWeek @ 0x10;   // Week of manufacture (1-54) or 0
    u8 manufactureYear @ 0x11;   // Year of manufacture (offset from 1990) or model year
};

// ==================== EDID VERSION & REVISION (2 bytes) ====================
struct EDIDVersion {
    u8 version @ 0x12;   // EDID version (1 for EDID 1.x)
    u8 revision @ 0x13;  // EDID revision (4 for EDID 1.4)
};

// ==================== BASIC DISPLAY PARAMETERS (5 bytes) ====================
// Video input definition (byte 14h)
bitfield VideoInputDefinition {
    digitalInput : 1;  // 0 = Analog, 1 = Digital
    
    // For analog input (when digitalInput = 0)
    signalLevelStandard : 2 [[hidden]]; // Video signal level standard
    setupExpected : 1 [[hidden]];       // Setup (blank-to-black) expected
    separateSyncs : 1 [[hidden]];       // Separate syncs supported
    compositeSyncOnHorizontal : 1 [[hidden]]; // Composite sync on horizontal
    compositeSyncOnGreen : 1 [[hidden]];      // Composite sync on green
    serrationOnVerticalSync : 1 [[hidden]];   // Serration on vertical sync
    
    // For digital input (when digitalInput = 1)
    bitDepth : 3 [[hidden]];         // Color bit depth
    videoInterface : 4 [[hidden]];   // Digital video interface standard
};

// Feature support (byte 18h)
bitfield FeatureSupport {
    standbySupported : 1;      // DPMS standby supported
    suspendSupported : 1;      // DPMS suspend supported
    activeOffSupported : 1;    // DPMS active-off supported
    displayType : 2;           // Display type (color/mono, RGB/non-RGB)
    sRGBStandard : 1;          // Standard sRGB color space
    preferredTimingMode : 1;   // Preferred timing mode in first detailed timing block
    continuousFrequency : 1;   // Continuous frequency supported (GTF or CVT)
};

struct BasicDisplayParameters {
    VideoInputDefinition videoInput @ 0x14;
    
    // Screen size or aspect ratio (bytes 15h-16h)
    u8 horizontalScreenSize @ 0x15;  // Horizontal screen size in cm or aspect ratio
    u8 verticalScreenSize @ 0x16;    // Vertical screen size in cm or aspect ratio
    
    // Display transfer characteristic (gamma) (byte 17h)
    u8 gamma @ 0x17;  // Display gamma, value = (gamma * 100) - 100 (1.0 to 3.54)
    
    // Feature support (byte 18h)
    FeatureSupport featureSupport @ 0x18;
};

// ==================== CHROMATICITY COORDINATES (10 bytes) ====================
// Chromaticity coordinates - low bits
bitfield RedGreenLowBits {
    redX_low : 2;    // Red X value, 2 least significant bits
    redY_low : 2;    // Red Y value, 2 least significant bits
    greenX_low : 2;  // Green X value, 2 least significant bits
    greenY_low : 2;  // Green Y value, 2 least significant bits
};

bitfield BlueWhiteLowBits {
    blueX_low : 2;   // Blue X value, 2 least significant bits
    blueY_low : 2;   // Blue Y value, 2 least significant bits
    whiteX_low : 2;  // White X value, 2 least significant bits
    whiteY_low : 2;  // White Y value, 2 least significant bits
};

struct ChromaticityCoordinates {
    RedGreenLowBits redGreenLow @ 0x19;
    BlueWhiteLowBits blueWhiteLow @ 0x1A;
    
    u8 redX_high @ 0x1B;    // Red X value, high byte
    u8 redY_high @ 0x1C;    // Red Y value, high byte
    u8 greenX_high @ 0x1D;  // Green X value, high byte
    u8 greenY_high @ 0x1E;  // Green Y value, high byte
    u8 blueX_high @ 0x1F;   // Blue X value, high byte
    u8 blueY_high @ 0x20;   // Blue Y value, high byte
    u8 whiteX_high @ 0x21;  // White X value, high byte
    u8 whiteY_high @ 0x22;  // White Y value, high byte
};

// ==================== ESTABLISHED TIMINGS (3 bytes) ====================
// Established timing bitmap
bitfield EstablishedTiming1 {
    timing_720x400_70 : 1;  // 720x400 @ 70Hz (VGA)
    timing_720x400_88 : 1;  // 720x400 @ 88Hz (XGA)
    timing_640x480_60 : 1;  // 640x480 @ 60Hz (VGA)
    timing_640x480_67 : 1;  // 640x480 @ 67Hz (Mac II)
    timing_640x480_72 : 1;  // 640x480 @ 72Hz
    timing_640x480_75 : 1;  // 640x480 @ 75Hz
    timing_800x600_56 : 1;  // 800x600 @ 56Hz
    timing_800x600_60 : 1;  // 800x600 @ 60Hz
};

bitfield EstablishedTiming2 {
    timing_800x600_72 : 1;  // 800x600 @ 72Hz
    timing_800x600_75 : 1;  // 800x600 @ 75Hz
    timing_832x624_75 : 1;  // 832x624 @ 75Hz (Mac II)
    timing_1024x768_87 : 1; // 1024x768 @ 87Hz interlaced
    timing_1024x768_60 : 1; // 1024x768 @ 60Hz
    timing_1024x768_70 : 1; // 1024x768 @ 70Hz
    timing_1024x768_75 : 1; // 1024x768 @ 75Hz
    timing_1280x1024_75 : 1; // 1280x1024 @ 75Hz
};

bitfield EstablishedTiming3 {
    timing_1152x870_75 : 1; // 1152x870 @ 75Hz (Mac II)
    manufacturerReserved : 7; // Reserved for manufacturer specific timings
};

struct EstablishedTimings {
    EstablishedTiming1 establishedTiming1 @ 0x23;
    EstablishedTiming2 establishedTiming2 @ 0x24;
    EstablishedTiming3 establishedTiming3 @ 0x25;
};

// ==================== STANDARD TIMINGS (16 bytes) ====================
// Standard timing information - aspect ratio
bitfield StandardTimingAspectRatio {
    aspectRatio : 2;  // 00=16:10, 01=4:3, 10=5:4, 11=16:9
    refreshRate : 6;  // (value + 60) Hz
};

struct StandardTiming {
    u8 horizontalResolution;            // (value + 31) * 8 pixels
    StandardTimingAspectRatio verticalInfo; // Aspect ratio and refresh rate
};

// ==================== DETAILED TIMING DESCRIPTORS (72 bytes) ====================
// Detailed timing descriptor bitfields
bitfield HorizontalVerticalHighBits {
    horizontalActive_high : 4;   // Horizontal active pixels (upper 4 bits)
    horizontalBlanking_high : 4; // Horizontal blanking pixels (upper 4 bits)
    verticalActive_high : 4;     // Vertical active lines (upper 4 bits)
    verticalBlanking_high : 4;   // Vertical blanking lines (upper 4 bits)
};

bitfield SyncDetails {
    horizontalSyncOffset_high : 2;      // Horizontal sync offset pixels (upper 2 bits)
    horizontalSyncPulseWidth_high : 2;  // Horizontal sync pulse width pixels (upper 2 bits)
    verticalSyncOffset_high : 2;        // Vertical sync offset lines (upper 2 bits)
    verticalSyncPulseWidth_high : 2;    // Vertical sync pulse width lines (upper 2 bits)
    horizontalImageSize_high : 4;       // Horizontal image size in mm (upper 4 bits)
    verticalImageSize_high : 4;         // Vertical image size in mm (upper 4 bits)
    horizontalBorder : 8;               // Horizontal border pixels (each side)
    verticalBorder : 8;                 // Vertical border lines (each side)
    interlaced : 1;                     // Interlaced mode
    stereo : 2;                         // Stereo mode
    syncType : 2;                       // Sync type
    vSyncPositive : 1;                  // Vertical sync polarity (1=positive)
    hSyncPositive : 1;                  // Horizontal sync polarity (1=positive)
    reserved : 1;                       // Reserved
};

struct DetailedTimingDescriptor {
    u16 pixelClock;                     // Pixel clock in 10 kHz units
    u8 horizontalActive_low;            // Horizontal active pixels (lower 8 bits)
    u8 horizontalBlanking_low;          // Horizontal blanking pixels (lower 8 bits)
    HorizontalVerticalHighBits hvHighBits; // High bits for horizontal/vertical values
    u8 verticalActive_low;              // Vertical active lines (lower 8 bits)
    u8 verticalBlanking_low;            // Vertical blanking lines (lower 8 bits)
    u8 horizontalSyncOffset_low;        // Horizontal sync offset pixels (lower 8 bits)
    u8 horizontalSyncPulseWidth_low;    // Horizontal sync pulse width pixels (lower 8 bits)
    u8 verticalSyncOffsetWidth_low;     // Vertical sync offset/width (packed)
    SyncDetails syncDetails;            // Sync details and other features
};

// ==================== DISPLAY DESCRIPTORS ====================
// Display descriptor types
enum DisplayDescriptorType : u8 {
    DISPLAY_SERIAL_NUMBER = 0xFF,   // Display serial number
    ALPHANUMERIC_DATA_STRING = 0xFE, // Unspecified text
    DISPLAY_RANGE_LIMITS = 0xFD,    // Display range limits
    DISPLAY_PRODUCT_NAME = 0xFC,    // Display product name
    COLOR_POINT_DATA = 0xFB,        // Additional color point data
    STANDARD_TIMING_IDS = 0xFA,     // Additional standard timing identifiers
    COLOR_MANAGEMENT_DATA = 0xF9,   // Color management data
    CVT_TIMING_CODES = 0xF8,        // CVT 3-byte timing codes
    ESTABLISHED_TIMINGS_III = 0xF7, // Additional established timings
    DUMMY_DESCRIPTOR = 0x10         // Dummy descriptor
};

// Display Range Limits Descriptor
bitfield DisplayRangeLimitsOffsets {
    verticalRateOffsets : 4;   // Vertical rate offsets
    horizontalRateOffsets : 4; // Horizontal rate offsets
};

// Generic Display Descriptor
struct DisplayDescriptor {
    u16 flag;                 // 0x0000 for display descriptor
    u8 reserved1;             // 0x00
    u8 descriptorType;        // Type of descriptor (see DisplayDescriptorType enum)
    u8 reserved2;             // 0x00
    u8 data[13];              // Descriptor data (depends on descriptorType)
};

// ==================== MAIN EDID STRUCTURE ====================
struct EDID {
    // Header (8 bytes)
    EDIDHeader header @ 0x00;
    
    // Vendor & Product ID (10 bytes)
    VendorProductID vendorProduct @ 0x08;
    
    // EDID Version & Revision (2 bytes)
    EDIDVersion version @ 0x12;
    
    // Basic Display Parameters (5 bytes)
    BasicDisplayParameters displayParams @ 0x14;
    
    // Chromaticity Coordinates (10 bytes)
    ChromaticityCoordinates chromaticity @ 0x19;
    
    // Established Timings (3 bytes)
    EstablishedTimings establishedTimings @ 0x23;
    
    // Standard Timing Information (16 bytes)
    StandardTiming standardTimings[8] @ 0x26;
    
    // Detailed Timing Descriptors (72 bytes)
    // The first descriptor is always a detailed timing descriptor
    DetailedTimingDescriptor detailedTiming1 @ 0x36;
    
    // The remaining descriptors can be either detailed timing or display descriptors
    // We'll use a union to handle both possibilities
    DisplayDescriptor descriptor2 @ 0x48;
    DisplayDescriptor descriptor3 @ 0x5A;
    DisplayDescriptor descriptor4 @ 0x6C;
    
    // Extension flag and checksum (2 bytes)
    u8 extensionCount @ 0x7E; // Number of optional extension blocks
    u8 checksum @ 0x7F;       // Sum of all 128 bytes should equal 0 (mod 256)
};

// Place the EDID structure at the beginning of the file
EDID edid @ 0x00;

// ==================== HELPER FUNCTIONS ====================
// Function to decode manufacturer ID from 2 bytes
fn decodeManufacturerID(u16 id) {
    u8 char1 = ((id >> 10) & 0x1F) + 'A' - 1;
    u8 char2 = ((id >> 5) & 0x1F) + 'A' - 1;
    u8 char3 = (id & 0x1F) + 'A' - 1;
    return (char1 << 16) | (char2 << 8) | char3;
};

// Function to calculate gamma from stored value
fn calculateGamma(u8 value) {
    if (value == 0xFF) {
        return 0.0; // Gamma not defined
    }
    return (value + 100) / 100.0;
};

// Function to calculate aspect ratio from stored value (landscape mode)
fn calculateLandscapeAspectRatio(u8 value) {
    return (value + 99) / 100.0;
};

// Function to calculate aspect ratio from stored value (portrait mode)
fn calculatePortraitAspectRatio(u8 value) {
    return 100.0 / (value + 99);
};

// Function to convert binary fraction to decimal (for chromaticity)
fn binaryFractionToDecimal(u16 value) {
    float result = 0.0;
    u8 i = 0;
    while (i < 10) {
        if (value & (1 << i)) {
            result = result + std::math::pow(2, i - 10);
        }
        i = i + 1;
    }
    return result;
};
