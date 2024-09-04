#define MAGIC_CDB 0xABCDEF98
#define MAGIC_VDB 0xABCDEF99

// the first subfile has a file header and the rest have garbage here
struct FileHeader {
    // both are always 1
    uint16 something0;
    uint16 something1;
    uint32 subfileCount; // total number of subfiles
    uint32 unknown0;
    uint32 subfileSize; // size of each subfile
    uint32 unknown1;
};

struct SubfileHeader {
    uint32 magic;
    uint8 unknown0[8];
};

struct ChunkSection {
    int32 index; // -1 = empty
    int32 position; // -1 = empty; subtract 0xC to get the position within the chunk
    int32 compressedSize; // 0 = empty
    int32 decompressedSize; // 0 = empty
};

struct ChunkHeader {
    int16 unknown0;
    int16 unknown1;
    ChunkSection sections[6];
};
