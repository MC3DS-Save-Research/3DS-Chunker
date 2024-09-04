# released under MIT license

import sys
from pathlib import Path
import shutil
import re

import click

from .classes import *
from .parser import *


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
    "-d",
    "--delete-out",
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
    for number, cdb_file in world.cdb:
        region_path = out / f"region{number:d}"
        region_path.mkdir()
        for index, chunk in cdb_file:
            chunk_path = region_path / f"chunk{index:d}"
            chunk_path.mkdir()
            for subchunk_index, subchunk in chunk:
                subchunk_path = chunk_path / f"subchunk{subchunk_index:d}"
                with open(subchunk_path, "wb") as subchunk_out:
                    subchunk_out.write(subchunk.decompressed)
        print(f"extracted region {number:d}!")


if __name__ == "__main__":
    main()

# Licensed under the MIT License
# Copyright (c) 2024 Anonymous941
# See the LICENSE file for more information.
