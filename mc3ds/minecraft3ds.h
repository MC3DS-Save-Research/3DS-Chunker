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

struct VDBHeader {
    // hack to get around dissect.cstruct's limitations
    uint32 magic;
    uint8 nameSize;
    uint8 list[7];

    uint32 unknown0;
    char name[nameSize];
    uint16 unknown1;
    uint16 unknown2; // 0x1 for map, 0x0 otherwise
}

struct IndexPointer {
    uint32 unknown; // seems to be related to slt numbers
};

struct CDBEntry {
    //int8 x; // probably not x
    //int8 z; // probably not z
    uint16 unknown0;
    uint16 unknown1; // how many blocks make up a row?
    uint16 slot; // slot (corresponds to a CDB file), unless it's <16?
    uint16 subfile; // subfile within the slot
    uint16 blocksPerRow; // always 0x20FF, and the block number is divisible by that
    uint16 constant1; // always 0xA
    uint16 unknown4; // usually 0x1, sometimes 0x2 or 0x3, and on large worlds as high as 0x6e
    uint16 constant2; // always 0x8000, subfile count?
};

struct Index {
    uint32 unknown0; // always 0x2
    uint32 entryCount;
    uint32 unknown1;
    uint32 entrySize;
    uint32 pointerCount;
    uint32 unknown2;
    IndexPointer pointers[pointerCount];
    CDBEntry entries[entryCount];
};
