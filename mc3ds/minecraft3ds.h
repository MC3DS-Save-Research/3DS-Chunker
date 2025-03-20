#define MAGIC_CDB 0xABCDEF98
#define MAGIC_VDB 0xABCDEF99

// the first subfile has a file header and the rest have garbage here
struct FileHeader {
    // both are always 1, version?
    uint16 something0;
    uint16 something1;
    uint32 subfileCount; // total number of subfiles
    uint32 footerSize; // footer after the subfiles, it seems to always be blank (all zeroes)
    uint32 subfileSize; // size of each subfile
    uint32 unknown0; // 0x4 for CDB, 0x100 for VDB
};

struct SubfileHeader {
    uint32 magic;
};

struct Position {
    uint32 x : 14; // signed
    uint32 z : 14; // signed
    uint32 dimension : 4; // unsigned
};

struct ChunkParameters {
    int8 unknown0;
    int8 unknown1;
};

struct ChunkSection {
    int32 index; // -1 = empty
    int32 position; // -1 = empty; subtract 0xC to get the position within the chunk
    int32 compressedSize; // 0 = empty
    int32 decompressedSize; // 0 = empty
};

struct ChunkHeader {
    Position position;
    ChunkParameters parameters;
    uint16 unknown0;
    uint16 unknown1;
    uint16 unknown2;
    ChunkSection sections[6];
};

struct VDBHeader {
    uint8 parameters[8];
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
    Position position;
    uint16 slot; // slot (corresponds to a CDB file), unless it's <16?
    uint16 subfile; // subfile within the slot
    uint16 constant0; // always 0x20FF
    uint16 constant1; // always 0xA
    ChunkParameters parameters; // also in the chunk; usually 0x1, sometimes 0x2 or 0x3, and on large worlds as high as 0x6e
    uint16 constant2; // always 0x8000, subfile count?
};

struct Index {
    uint32 constant0; // always 0x2
    uint32 entryCount;
    uint32 unknown0;
    uint32 entrySize;
    uint32 pointerCount;
    uint32 constant1; // always 0x80
    IndexPointer pointers[pointerCount];
    CDBEntry entries[entryCount];
};

struct Subchunk {
        uint8 constant0; // always 0x0
        uint8 blocks[16][16][16];
        uint8 blockData[16 * 16 * 16 / 2]; // 16*16*16 array of nibbles
        uint8 unknownBlockData[16][16][16]; // always 0x0?
};

struct BlockData {
    uint8 subchunkCount;
    Subchunk subchunks[subchunkCount];
    uint16 unknown0[16][16];
    uint8 biomes[16][16];
};
