from os import SEEK_SET, SEEK_CUR, SEEK_END
from pathlib import Path
import re
from io import BytesIO
import random
import zlib
from shutil import copytree, rmtree

INT8 = 0x1
INT16 = 0x2
INT32 = 0x4
INT64 = 0x8

NETHER_BIOMES = (8, 178, 179, 180, 181)

KEEP_BLOCKS = (90, 120, 138)


def process(blocks: dict[int, Path], biomes_path: Path | None) -> str:
    blank = True
    nether = False
    keeper = False
    null_bytes = bytes(128)
    for block_number, block_path in blocks.items():
        with open(block_path, "rb") as block_file:
            while True:
                byted = block_file.read(128)
                if not byted:
                    break
                if byted != null_bytes[: len(byted)]:
                    blank = False
                    for keep_me in KEEP_BLOCKS:
                        if keep_me in byted:
                            keeper = True
                            if 87 in byted:  # netherrack
                                input("!")
    with open(biomes_path, "rb") as biomes_file:
        raw_biomes = biomes_file.read()
    for biome in NETHER_BIOMES:
        if biome in raw_biomes:
            nether = True
    if blank:
        # if nether:
        #     print("blanknether")
        return "blank"
    elif nether:
        if keeper:
            print(f"preserving chunk with {len(blocks):d} unknowns")
            return "keeper"
        else:
            return "nether"
    else:
        return "none"


def read_int(stream: BytesIO, size: int = INT32, signed: bool = False) -> int:
    return int.from_bytes(stream.read(size), "little", signed=signed)


def skip_int(stream: BytesIO, count: int = 1, size: int = INT32) -> None:
    stream.seek(size * count, SEEK_CUR)


def extract_used_chunks(stream: BytesIO) -> list:
    "reads the CDB index and finds the used chunks"
    found = []

    skip_int(stream)
    entry_count = read_int(stream)
    skip_int(stream)
    entry_size = read_int(stream)
    assert entry_size == 0x10
    pointer_count = read_int(stream)
    skip_int(stream)

    skip_int(stream, pointer_count)
    for entry in range(entry_count):
        skip_int(stream, 2, INT16)

        region = read_int(stream, INT16)
        subfile = read_int(stream, INT16)
        found.append((region, subfile))

        skip_int(stream, 2, INT16)
        skip_int(stream)

    return found


def read_header(stream: BytesIO) -> tuple[int, int]:
    skip_int(stream, 2, INT16)
    subfile_count = read_int(stream)
    skip_int(stream)
    subfile_size = read_int(stream)
    skip_int(stream)
    return subfile_count, subfile_size


def seek_chunk(
    stream: BytesIO, chunk: int, subfile_count: int, subfile_size: int
) -> None:
    if chunk > subfile_count:
        raise ValueError("index goes past the bounds of the database")
    stream.seek(chunk * subfile_size + 0x14 + 0x10)


def read_chunk(
    stream: BytesIO,
    chunk: int,
    index: int,
    subfile_count: int,
    subfile_size: int,
    decompress: bool = True,
) -> bytes:
    seek_chunk(stream, chunk, subfile_count, subfile_size)
    sections = {}
    for i in range(6):
        current_index = read_int(stream, signed=True)
        position = read_int(stream, signed=True)
        compressed_size = read_int(stream, signed=True)
        decompressed_size = read_int(stream, signed=True)
        if current_index != -1:
            sections[current_index] = position, compressed_size, decompressed_size

    try:
        position, compressed_size, decompressed_size = sections[index]
    except KeyError:
        return None

    stream.seek(position - 0x70, SEEK_CUR)
    compressed = stream.read(compressed_size)
    if decompress:
        decompress_object = zlib.decompressobj()
        decompressed = decompress_object.decompress(compressed)
        if decompress_object.unused_data:
            raise ValueError("incorrect compressed size")
        if len(decompressed) != decompressed_size:
            raise ValueError("incorrect decompressed size")
        return decompressed
    else:
        return compressed, decompressed_size


def write_chunk(
    stream: BytesIO, chunk: int, new_data: dict, subfile_count: int, subfile_size: int
) -> None:
    seek_chunk(stream, chunk, subfile_count, subfile_size)
    updated = {}
    headers = b""
    # merge the old and new data
    position = 0x70
    for index in range(6):
        try:
            new = new_data[index]
        except KeyError:
            new = read_chunk(
                stream, chunk, index, subfile_count, subfile_size, decompress=False
            )
            if new is None:
                compressed = None
            else:
                compressed, decompressed_size = new
        else:
            if new is None:
                compressed = None
            else:
                compressed = zlib.compress(new)
                decompressed_size = len(new)
        if compressed is None:
            new_header = (-1, -1, 0, 0)
        else:
            updated[index] = compressed
            new_header = (index, position, len(compressed), decompressed_size)
            position += len(compressed)
            if position > subfile_size:
                raise ValueError("out of space")
        for param in new_header:
            headers += param.to_bytes(INT32, "little", signed=True)

    # now write it to the CDB file
    seek_chunk(stream, chunk, subfile_count, subfile_size)
    # old = stream.read(len(headers))
    # stream.seek(-len(headers), SEEK_CUR)
    # assert old == headers
    stream.write(headers)
    for index in range(6):
        try:
            data = updated[index]
        except KeyError:
            pass
        else:
            # old = stream.read(len(data))
            # assert old == data
            # stream.seek(-len(data), SEEK_CUR)
            stream.write(data)


def main() -> None:
    script_path = Path(__file__).parent
    world_path = script_path.parent.parent / "skyer"
    out_path = script_path.parent.parent / "out"

    cdb_path = out_path / "cdb"
    region_pattern = re.compile(r"region(0|(?:[1-9]\d*))")
    chunk_pattern = re.compile(r"chunk(0|(?:[1-9]\d*))")
    block_pattern = re.compile(r"blocks(0|(?:[1-9]\d*))")
    blanks = []
    nethers = []

    if world_path.exists():
        if (world_path / "db").is_dir():
            rmtree(world_path)
        else:
            raise ValueError("invalid world")
    copytree(world_path.parent / f"{world_path.name}.bak", world_path)
    with open(world_path / "new", "x"):
        pass
    for region_path in cdb_path.iterdir():
        if not region_path.is_dir():
            continue
        matched = region_pattern.fullmatch(region_path.name)
        if matched is None:
            continue
        region = int(matched[1])
        for chunk_path in region_path.iterdir():
            if not chunk_path.is_dir():
                continue
            matched = chunk_pattern.fullmatch(chunk_path.name)
            if matched is None:
                continue
            chunk = int(matched[1])
            blocks = {}
            biomes_path = None
            for item_path in chunk_path.iterdir():
                if not item_path.is_file():
                    continue
                if item_path.name == "biomes":
                    biomes_path = item_path
                matched = block_pattern.fullmatch(item_path.name)
                if matched is None:
                    continue
                block_number = int(matched[1])
                blocks[block_number] = item_path
            chunk_type = process(blocks, biomes_path)
            if chunk_type != "none":
                chunk_value = region.to_bytes(2, "little") + chunk.to_bytes(2, "little")
                value_parsed = " ".join([f"{byte:02X}" for byte in chunk_value])
                # print(f"{chunk_type}: {value_parsed}")
                if chunk_type == "blank":
                    blanks.append((region, chunk))
                if chunk_type == "nether":
                    nethers.append((region, chunk))
    # write it to the file!!
    with open(world_path / "db" / "cdb" / "newindex.cdb", "rb") as new_index:
        found = extract_used_chunks(new_index)
    for entry in found:
        if entry in blanks:
            print("found blank")
        elif entry in nethers:
            print("found nether")
            region, chunk = entry
            region_path = world_path / "db" / "cdb" / f"slt{region:d}.cdb"
            with open(region_path, "rb+") as cdb:
                subfile_count, subfile_size = read_header(cdb)
                print(region, chunk)
                raw_chunk = read_chunk(cdb, chunk, 0, subfile_count, subfile_size)
                unknown_size = int.from_bytes(raw_chunk[:INT16], "little")

                # generate a new chunk with all blocks removed
                new_bytes = raw_chunk[:INT16]
                for i in range(unknown_size):
                    if False and i == 0:
                        # put glowstone so it's not fully blank
                        new_bytes += bytes([89])
                        new_bytes += bytes(0x2800 - 1)
                    else:
                        new_bytes += bytes(0x2800)
                unknown = raw_chunk[INT16 + unknown_size * 0x2800 : -0x100]
                biomes = raw_chunk[-0x100:]
                new_bytes += bytes(len(unknown))
                new_bytes += biomes
                assert len(new_bytes) == len(raw_chunk)
                new_data = {0: new_bytes}
                write_chunk(cdb, chunk, new_data, subfile_count, subfile_size)


if __name__ == "__main__":
    main()
