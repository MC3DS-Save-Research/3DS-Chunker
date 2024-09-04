# released under MIT license

import sys
from pathlib import Path
import shutil
import re

from classes import *
from parser import *


def size_check(struct, expected_size, name):
    assert (
        struct.size == expected_size
    ), f"size of {name} is 0x{struct.size:X}, should be 0x{expected_size:X}"


size_check(parser.FileHeader, 0x14, "file header")
size_check(parser.SubfileHeader, 0x20, "subfile header")
size_check(parser.ChunkHeader, 0x64, "chunk header")


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
        with open(cdb_file, "rb") as stream:
            new = CDBFile(stream)
            for index, chunk in new:
                chunk_path = region_path / f"chunk{index:d}"
                chunk_path.mkdir()
                for subchunk_index, subchunk in chunk:
                    subchunk_path = chunk_path / f"subchunk{subchunk_index:d}"
                    with open(subchunk_path, "wb") as out:
                        out.write(subchunk.decompressed)
        print(f"extracted region {number:d}!")


if __name__ == "__main__":
    main()

# Licensed under the MIT License
# Copyright (c) 2024 Anonymous941
# See the LICENSE file for more information.
