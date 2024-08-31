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
    uint8 unknown2[0xF];
    uint32 magic;
    uint8 unknown3[0x8];
};

struct chunkSection {
    // -1 = missing
    int32 index;
    int32 compressedSize;
    int32 decompressedSize;
    uint32 unknown;
};

struct chunkHeader {
    commonHeader common;
    uint8 unknown0[0x4];
    chunkSection sections[6];
};

struct chunk {
    chunkHeader header;
    uint8 data[0x2800-0x84];
};
"""
parser = cstruct().load(DEFINITION)


def size_check(struct, expected_size, name):
    assert (
        struct.size == expected_size
    ), f"size of {name} is 0x{struct.size:X}, should be 0x{expected_size:X}"


size_check(parser.commonHeader, 0x20, "common header")
size_check(parser.chunkHeader, 0x84, "chunk header")
size_check(parser.chunk, 0x2800, "chunk")


def parse_cdb_stream(cdb):
    chunk_struct = parser.chunk
    parsed = chunk_struct(cdb)
    chunks = []
    data_left = bytes(parsed.data)
    total = len(data_left)
    for chunk_section in parsed.header.sections:
        print(chunk_section)
        print(" ".join(f"{byte:02X}" for byte in data_left[:10]))
        decompress_object = zlib.decompressobj()
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
    world_input = input("Enter path to world: ")
    cdb_input = input("Enter CDB filename (slt#.cdb): ")
    cdb_path = Path(world_input) / "db" / "cdb" / cdb_input
    parse_cdb(cdb_path)


if __name__ == "__main__":
    main()
