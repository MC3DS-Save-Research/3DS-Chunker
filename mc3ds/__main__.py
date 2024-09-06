# released under MIT license

import sys
from pathlib import Path
import shutil
import json

import click

from .classes import *
from .parser import parser
from .convert import convert


@click.command()
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=False,
)
@click.option(
    "-o",
    "--out",
    type=click.Path(file_okay=False, path_type=Path),
    default="out",
    help="Directory for output",
)
@click.option(
    "--delete-out",
    is_flag=True,
    help="Permanently delete the out folder and its contents if it exists (make sure it's the right folder!)",
)
def main(path: Path, out: Path, delete_out: bool = False) -> None:
    script_path = Path(__file__).parent
    if out.exists():
        if delete_out:
            shutil.rmtree(out)
        else:
            print(
                'already extracted, please move or delete the "out" folder',
                file=sys.stderr,
            )
            sys.exit(1)

    if path is None:
        path = Path(input("Enter path to world: "))
    world = World(path)
    print(f"World name: {world.name}")
    out.mkdir()

    vdb_out = out / "vdb"
    vdb_out.mkdir()
    for number, vdb_file in world.vdb:
        region_path = vdb_out / f"region{number:d}"
        region_path.mkdir()
        for index, data in vdb_file:
            try:
                name = data.name.decode()
            except UnicodeDecodeError:
                name = "None"
            nbt_path = region_path / name
            nbt_metadata_path = region_path / f"{name}.json"
            with open(nbt_metadata_path, "x") as subfile_metadata_out:
                json.dump(
                    {
                        "unknown0": f"0x{data.unknown0:X}",
                        "unknown1": f"0x{data.unknown1:X}",
                        "unknown2": f"0x{data.unknown2:X}",
                    },
                    subfile_metadata_out,
                )
            with open(nbt_path, "xb") as subfile_out:
                subfile_out.write(data.raw)

    cdb_out = out / "cdb"
    cdb_out.mkdir()
    for number, cdb_file in world.cdb:
        region_path = cdb_out / f"region{number:d}"
        region_path.mkdir()
        for index, chunk in cdb_file:
            chunk_path = region_path / f"chunk{index:d}"
            chunk_path.mkdir()
            for subchunk_index, subchunk in chunk:
                subchunk_path = chunk_path / f"subchunk{subchunk_index:d}"
                if subchunk_index == 0:
                    block_data, tail = subchunk.data
                    for block_index, block in enumerate(block_data):
                        convert(block)
                        sys.exit()
                        block_path = chunk_path / f"block{block_index:d}"
                        with open(block_path, "wb") as block_data_out:
                            block_data_out.write(block)
                    tail_path = chunk_path / "blocktail"
                    with open(tail_path, "wb") as tail_out:
                        tail_out.write(tail)
                else:
                    with open(subchunk_path, "wb") as subchunk_out:
                        subchunk_out.write(subchunk.raw_decompressed)
        print(f"extracted region {number:d}!")


if __name__ == "__main__":
    main()

# Licensed under the MIT License
# Copyright (c) 2024 Anonymous941
# See the LICENSE file for more information.
