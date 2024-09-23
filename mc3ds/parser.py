from pathlib import Path

from dissect.cstruct import cstruct

parser = cstruct()
parser.loadfile(Path(__file__).parent / "minecraft3ds.h")


def size_check(struct, expected_size, name):
    assert (
        struct.size == expected_size
    ), f"size of {name} is 0x{struct.size:X}, should be 0x{expected_size:X}"


size_check(parser.FileHeader, 0x14, "file header")
size_check(parser.SubfileHeader, 0x4, "subfile header")
size_check(parser.ChunkSection, 0x10, "chunk section")
size_check(parser.ChunkHeader, 0x6C, "chunk header")
