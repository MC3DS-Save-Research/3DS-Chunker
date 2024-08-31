from pathlib import Path
import re
import itertools
import random
from io import BytesIO

from dissect.cstruct import cstruct
import zlib

# TODO update these
DEFINITION = """
#define MAGIC_CDB 0xABCDEF98
#define MAGIC_VDB 0xABCDEF99

struct commonHeader {
    // I think these are 16-bit, and are usually 1
    uint16 unknown0;
    uint16 unknown1;

    uint8 unknownBitmask; // USUALLY only has one bit set at a time, for some reaso
    padding[0xF];
    uint32 magic;
    padding[0x8];
};

struct CDBData {
    // -1 = missing
    int32 index;
    int32 compressedSize;
    int32 decompressedSize;
    uint32 unknown;
};

struct CDBHeader {
    commonHeader common;
    padding[0x4];
    CDBData data[6];
};

struct CDB {
    CDBHeader header;
};

CDB cdb @ 0x00;
"""
parser = cstruct().load(DEFINITION)

assert parser.commonHeader.size == 0x20, hex(parser.commonHeader.size)
assert parser.cdbHeader.size == 0x84, hex(parser.cdbHeader.size)


def parse_cdb_stream(cdb):
    cdb_struct = parser.cdb
    parsed = cdb_struct(cdb)
    chunks = []
    data_left = bytes(parsed.chunks[2].zlibCompressedData)
    total = parser.chunk.size
    # read header
    header = parser.cdbHeader(data_left)
    # remove the header from the data
    data_left = data_left[header.size :]
    while data_left:
        decompress_object = zlib.decompressobj()
        print(" ".join(f"{byte:02X}" for byte in data_left[:10]))
        input(f"0x{total - len(data_left):X}/0x{total:X} bytes parsed")

        decompressed_chunk = decompress_object.decompress(data_left)
        chunks.append(decompressed_chunk)
        data_left = decompress_object.unused_data
    with open(Path(__file__).parent / "chunk", "wb") as chunk_out:
        chunk_out.write(decompressed_chunk)
        input("decompressed")


def parse_cdb(path):
    with open(path, "rb") as handle:
        parse_cdb_stream(handle)


def get_cdb_files(world_path):
    cdb_path = world_path / "db" / "cdb"
    return filter(lambda path: path.is_file(), cdb_path.iterdir())


def main():
    script_path = Path(__file__).parent
    parse_cdb(input("Enter path to world: "))

if __name__ == "__main__":
    main()
