#pragma endian little

// EDID (Extended Display Identification Data) Pattern for ImHex
// Base EDID structure (128 bytes)
// Based on VESA E-EDID standard

// Forward declarations
using ManufacturerID;
using VideoInputDefinition;
using FeatureSupport;
using RedGreenLowBits;
using BlueWhiteLowBits;
using EstablishedTiming1;
using EstablishedTiming2;
using EstablishedTiming3;
using VerticalInfo;
using HorizontalHighBits;
using VerticalHighBits;
using VerticalSyncHighBits;
using SyncHighBits;
using ImageSizeHighBits;
using SignalFeatures;
using DisplayDescriptorType;

// Manufacturer ID encoded in 2 bytes
bitfield ManufacturerID {
    char1 : 5;  // First character (5 bits, A-Z)
    char2 : 5;  // Second character (5 bits, A-Z)
    char3 : 5;  // Third character (5 bits, A-Z)
    reserved : 1;  // Reserved bit
};

// Video input definition
bitfield VideoInputDefinition {
    digitalInput : 1;  // 0 = Analog, 1 = Digital
    // For analog input (when digitalInput = 0)
    separateSyncSupported : 1;  // Separate sync supported (analog)
    compositeSyncSupported : 1;  // Composite sync supported (analog)
    separateSyncsOnGreenSupported : 1;  // Separate syncs on green supported (analog)
    // For digital input (when digitalInput = 1)
    bitDepth : 3;  // DFP 1.x compatible (digital) or bit depth
    videoInterface : 4;  // Video interface (digital)
    reserved : 1;  // Reserved
};

// Feature support
bitfield FeatureSupport {
    standbySupported : 1;  // DPMS standby supported
    suspendSupported : 1;  // DPMS suspend supported
    activeOffSupported : 1;  // DPMS active-off supported
    displayType : 2;  // Display type (color/mono, RGB/non-RGB)
    sRGBStandard : 1;  // Standard sRGB color space
    preferredTimingMode : 1;  // Preferred timing mode in first detailed timing block
    continuousTimings : 1;  // Continuous timings with GTF or CVT
};

// Chromaticity coordinates - low bits
bitfield RedGreenLowBits {
    redX_low : 2;  // Red X value, 2 least significant bits
    redY_low : 2;  // Red Y value, 2 least significant bits
    greenX_low : 2;  // Green X value, 2 least significant bits
    greenY_low : 2;  // Green Y value, 2 least significant bits
};

bitfield BlueWhiteLowBits {
    blueX_low : 2;  // Blue X value, 2 least significant bits
    blueY_low : 2;  // Blue Y value, 2 least significant bits
    whiteX_low : 2;  // White X value, 2 least significant bits
    whiteY_low : 2;  // White Y value, 2 least significant bits
};

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
    timing_1024x768_87 : 1;  // 1024x768 @ 87Hz interlaced
    timing_1024x768_60 : 1;  // 1024x768 @ 60Hz
    timing_1024x768_70 : 1;  // 1024x768 @ 70Hz
    timing_1024x768_75 : 1;  // 1024x768 @ 75Hz
    timing_1280x1024_75 : 1;  // 1280x1024 @ 75Hz
};

bitfield EstablishedTiming3 {
    timing_1152x870_75 : 1;  // 1152x870 @ 75Hz (Mac II)
    reserved : 7;  // Reserved, set to 0
};

// Standard timing information
bitfield VerticalInfo {
    aspectRatio : 2;  // Aspect ratio: 00=16:10, 01=4:3, 10=5:4, 11=16:9
    refreshRate : 6;  // (value + 60) Hz
};

// Detailed timing descriptor bitfields
bitfield HorizontalHighBits {
    horizontalActive_high : 4;  // Horizontal active pixels (upper 4 bits)
    horizontalBlanking_high : 4;  // Horizontal blanking pixels (upper 4 bits)
};

bitfield VerticalHighBits {
    verticalActive_high : 4;  // Vertical active lines (upper 4 bits)
    verticalBlanking_high : 4;  // Vertical blanking lines (upper 4 bits)
};

bitfield VerticalSyncHighBits {
    verticalSyncOffset_low : 4;  // Vertical sync offset lines (lower 4 bits)
    verticalSyncPulseWidth_low : 4;  // Vertical sync pulse width lines (lower 4 bits)
};

bitfield SyncHighBits {
    horizontalSyncOffset_high : 2;  // Horizontal sync offset pixels (upper 2 bits)
    horizontalSyncPulseWidth_high : 2;  // Horizontal sync pulse width pixels (upper 2 bits)
    verticalSyncOffset_high : 2;  // Vertical sync offset lines (upper 2 bits)
    verticalSyncPulseWidth_high : 2;  // Vertical sync pulse width lines (upper 2 bits)
};

bitfield ImageSizeHighBits {
    horizontalImageSize_high : 4;  // Horizontal image size in mm (upper 4 bits)
    verticalImageSize_high : 4;  // Vertical image size in mm (upper 4 bits)
};

bitfield SignalFeatures {
    interlaced : 1;  // Interlaced
    stereo : 2;  // Stereo mode
    syncType : 2;  // Sync type (bit-field specific, see standard)
    syncPolarity : 2;  // Sync polarity (depends on syncType)
    reserved : 1;  // Reserved
};

// Display descriptor types
enum DisplayDescriptorType : u8 {
    Manufacturer = 0xFF,  // Manufacturer specified data
    DisplayName = 0xFC,   // Display name
    DisplayRange = 0xFD,  // Display range limits
    DisplaySerial = 0xFF, // Display serial number
    Unspecified = 0x10,   // Unspecified text
    DisplayASCII = 0xFE   // Display ASCII string
};

// Header and version information
struct EDIDHeader {
    u8 header[8];  // Fixed header pattern: 00 FF FF FF FF FF FF 00
    
    // Vendor & Product Identification
    ManufacturerID manufacturerID;  // Manufacturer ID from EISA registry
    u16 productCode;  // Manufacturer product code
    u32 serialNumber;  // Serial number
    u8 manufactureWeek;  // Week of manufacture, or 0xFF for model year only
    u8 manufactureYear;  // Year of manufacture minus 1990, or model year
    
    // EDID version/revision
    u8 edidVersion;  // EDID version number
    u8 edidRevision;  // EDID revision number
};

// Basic display parameters
struct DisplayParameters {
    // Video input definition
    VideoInputDefinition videoInput;
    
    // Screen dimensions
    u8 screenWidth;  // Horizontal screen size in cm (0 for projectors)
    u8 screenHeight;  // Vertical screen size in cm (0 for projectors)
    
    // Display transfer characteristics
    u8 gamma;  // Display gamma, (gamma * 100) - 100 (1.0 to 3.54)
    
    // Feature support
    FeatureSupport featureSupport;
};

// Color characteristics
struct ColorCharacteristics {
    // Chromaticity coordinates
    RedGreenLowBits redGreenLow;
    BlueWhiteLowBits blueWhiteLow;
    
    u8 redX_high;  // Red X value, high byte
    u8 redY_high;  // Red Y value, high byte
    u8 greenX_high;  // Green X value, high byte
    u8 greenY_high;  // Green Y value, high byte
    u8 blueX_high;  // Blue X value, high byte
    u8 blueY_high;  // Blue Y value, high byte
    u8 whiteX_high;  // White X value, high byte
    u8 whiteY_high;  // White Y value, high byte
};

struct EstablishedTiming {
    EstablishedTiming1 establishedTiming1;
    EstablishedTiming2 establishedTiming2;
    EstablishedTiming3 establishedTiming3;
};

// Standard timing information
struct StandardTiming {
    u8 horizontalResolution;  // (value + 31) * 8 pixels
    VerticalInfo verticalInfo;
};

// Detailed timing descriptor
struct DetailedTiming {
    u16 pixelClock;  // Pixel clock in 10 kHz units
    u8 horizontalActive_low;  // Horizontal active pixels (lower 8 bits)
    u8 horizontalBlanking_low;  // Horizontal blanking pixels (lower 8 bits)
    HorizontalHighBits horizontalHighBits;
    
    u8 verticalActive_low;  // Vertical active lines (lower 8 bits)
    u8 verticalBlanking_low;  // Vertical blanking lines (lower 8 bits)
    VerticalHighBits verticalHighBits;
    
    u8 horizontalSyncOffset_low;  // Horizontal sync offset pixels (lower 8 bits)
    u8 horizontalSyncPulseWidth_low;  // Horizontal sync pulse width pixels (lower 8 bits)
    VerticalSyncHighBits verticalSyncHighBits;
    SyncHighBits syncHighBits;
    
    u8 horizontalImageSize_low;  // Horizontal image size in mm (lower 8 bits)
    u8 verticalImageSize_low;  // Vertical image size in mm (lower 8 bits)
    ImageSizeHighBits imageSizeHighBits;
    
    u8 horizontalBorder;  // Horizontal border pixels (each side)
    u8 verticalBorder;  // Vertical border lines (each side)
    SignalFeatures signalFeatures;
};

// Display descriptor
struct DisplayDescriptor {
    u16 flag;  // 0x0000 indicates a descriptor
    u8 reserved1;  // 0x00
    u8 descriptorType;  // Descriptor type (see DisplayDescriptorType enum)
    u8 reserved2;  // 0x00
    u8 data[13];  // Descriptor data (depends on descriptorType)
};

// Main EDID structure
struct EDID {
    // Header and basic information (bytes 0-19)
    EDIDHeader header;
    
    // Basic display parameters (bytes 20-24)
    DisplayParameters displayParameters;
    
    // Color characteristics (bytes 25-34)
    ColorCharacteristics colorCharacteristics;
    
    // Established timings (bytes 35-37)
    EstablishedTiming establishedTimings;
    
    // Standard timing information (bytes 38-53)
    StandardTiming standardTimings[8];
    
    // Detailed timing descriptors (bytes 54-125)
    DetailedTiming detailedTiming1;  // First detailed timing is preferred if indicated
    DisplayDescriptor descriptor2;  // Additional descriptor block
    DisplayDescriptor descriptor3;  // Additional descriptor block
    DisplayDescriptor descriptor4;  // Additional descriptor block
    
    // Extension flag and checksum (bytes 126-127)
    u8 extensionCount;  // Number of optional extension blocks
    u8 checksum;  // Sum of all 128 bytes should equal 0 (mod 256)
};

// Place the EDID structure at the beginning of the file
EDID edid @ 0x00;
