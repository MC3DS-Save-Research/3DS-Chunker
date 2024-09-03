# released under MIT license

import sys
from pathlib import Path
import shutil
import re
import traceback

from dissect.cstruct import cstruct
import zlib

# TODO update these
DEFINITION = """
#define MAGIC_CDB 0xABCDEF98
#define MAGIC_VDB 0xABCDEF99

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
    uint8 unknown0[sizeof(FileHeader)]; // the first subfile has a file header and the rest have garbage here
    uint32 magic;
    uint8 unknown1[8]; // unknown
};

struct ChunkSection {
    int32 index; // -1 = empty
    int32 compressedSize; // -1 = empty
    int32 decompressedSize; // 0 = empty
    int32 unknown; // 0 = empty
};

struct ChunkHeader {
    SubfileHeader subfileHeader;
    int16 unknown0;
    int16 unknown1;
    ChunkSection sections[6];
};
"""
parser = cstruct().load(DEFINITION)


def size_check(struct, expected_size, name):
    assert (
        struct.size == expected_size
    ), f"size of {name} is 0x{struct.size:X}, should be 0x{expected_size:X}"


size_check(parser.FileHeader, 0x14, "file header")
size_check(parser.SubfileHeader, 0x20, "subfile header")
size_check(parser.ChunkHeader, 0x84, "chunk header")


def parse_chunk(stream, subfile_size):
    header = parser.ChunkHeader(stream)
    unknown = (header.unknown0, header.unknown1)
    # sometimes there are chunks with all 0 for some reason
    if header.subfileHeader.magic == 0x0:
        return None
    errors = 0
    chunk_sections = {}
    data_left = stream.read(subfile_size - header.size)
    total = len(data_left)
    for chunk_section in header.sections:
        if chunk_section.index == -1:
            continue
        decompress_object = zlib.decompressobj()
        # print(f"0x{total - len(data_left):X}/0x{total:X} bytes parsed")

        try:
            decompressed_chunk = decompress_object.decompress(data_left)
        except Exception:
            print(f"decompression error", file=sys.stderr)
            errors += 1
            # traceback.print_exc()
            continue
        chunk_sections[chunk_section.index] = decompressed_chunk
        data_left = decompress_object.unused_data
    # if header.unknown0 != 0x3:
    #     input(repr(header))
    return (chunk_sections, unknown, errors)


def parse_cdb_stream(stream):
    old_seek = stream.tell()
    file_header = parser.FileHeader(stream)
    stream.seek(old_seek)
    chunks = []
    for chunk_index in range(file_header.subfileCount):
        chunks.append(parse_chunk(stream, file_header.subfileSize))
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
    out_path = script_path / "out"
    if out_path.exists():
        if 1:
            shutil.rmtree(out_path)
        else:
            print(
                'already extracted, please move or delete the "out" folder',
                file=sys.stderr,
            )
            sys.exit(1)
    world_input = input("Enter path to world: ")
    cdb_files = get_cdb_files(script_path / world_input)
    out_path.mkdir()
    for number, cdb_file in cdb_files.items():
        region_path = out_path / f"region{number:d}"
        region_path.mkdir()
        print(f"parsing region {number:d}")
        chunks = parse_cdb(cdb_file)
        print(f"extracted region {number:d}!")
        for index, chunk in enumerate(chunks):
            if chunk is None:
                continue
            chunk_path = region_path / f"chunk{index:d}"
            chunk_path.mkdir()
            for section_index, chunk_section in chunk[0].items():
                chunk_section_path = chunk_path / f"section{section_index:d}"
                with open(chunk_section_path, "wb") as out:
                    out.write(chunk_section)


if __name__ == "__main__":
    main()

# Licensed under the MIT License
# Copyright (c) 2024 Anonymous941
# See the LICENSE file for more information.
