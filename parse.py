import sys
from pathlib import Path
import re
import traceback

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
    uint32 unknown;
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


def parse_chunk(raw_chunk):
    parsed = parser.chunk(raw_chunk)
    chunk_sections = []
    data_left = bytes(parsed.data)
    total = len(data_left)
    for chunk_section in parsed.header.sections:
        # print(chunk_section)
        if chunk_section.index == -1:
            continue
        decompress_object = zlib.decompressobj()
        # print(f"0x{total - len(data_left):X}/0x{total:X} bytes parsed")

        decompressed_chunk = decompress_object.decompress(data_left)
        chunk_sections.append(decompressed_chunk)
        data_left = decompress_object.unused_data
    return chunk_sections, parsed.header.unknown


def parse_cdb_stream(cdb):
    chunks = []
    for chunk_index in range(40):
        raw_chunk = cdb.read(parser.chunk.size)
        chunks.append(parse_chunk(raw_chunk))
    return chunks


def parse_cdb(path):
    with open(path, "rb") as handle:
        return parse_cdb_stream(handle)


cdb_expression = re.compile(R"slt([1-9]\d*)\.cdb")


def get_cdb_files(world_path):
    """
    gets the CDB filenames from a path
    """
    result = {}
    cdb_path = world_path / "db" / "cdb"
    files = filter(lambda path: path.is_file(), cdb_path.iterdir())
    for cdb_file in files:
        filename = cdb_file.name
        matched = cdb_expression.fullmatch(filename)
        if matched is None:
            continue
        cdb_number = int(matched[1])
        result[cdb_number] = cdb_file
    return result


def main():
    script_path = Path(__file__).parent
    world_input = input("Enter path to world: ")
    cdb_files = get_cdb_files(script_path / world_input)
    out_path = Path(__file__).parent / "out"
    if out_path.exists():
        print(
            'already extracted, please move or delete the "out" folder', file=sys.stderr
        )
        sys.exit(1)
    out_path.mkdir()
    for number, cdb_file in cdb_files.items():
        region_path = out_path / f"region{number:d}"
        try:
            chunks = parse_cdb(cdb_file)
        except Exception:
            traceback.print_exc()
            print(f"error parsing region {number:d}", file=sys.stderr)
            continue
        else:
            print(f"extracted region {number:d}!")
        for index, chunk in enumerate(chunks):
            chunk_path = out_path / f"chunk{index:d}"
            chunk_path.mkdir()
            for section_index, chunk_section in enumerate(chunk[0]):
                chunk_section_path = chunk_path / f"section{section_index:d}"
                with open(chunk_section_path, "wb") as out:
                    out.write(chunk_section)


if __name__ == "__main__":
    main()
