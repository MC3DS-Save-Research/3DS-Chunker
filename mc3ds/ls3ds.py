"a command line utility to show the world names in the current directory, useful for knowing which world is which in the minecraftWorlds directory"

import sys
import os
from pathlib import Path
from io import BytesIO
from warnings import warn

import click

from .nbt import NBT


def get_world_name_stream(stream: BytesIO) -> str:
    parsed = NBT(stream.read())
    return parsed.get("LevelName")


def get_world_name(level_dat: Path) -> str:
    with open(level_dat, "rb") as stream:
        return get_world_name_stream(stream)


def get_world_names(directory: Path) -> dict[Path, str]:
    result = {}
    if (directory / "level.dat").is_file():
        result[directory.name] = get_world_name(directory / "level.dat")
    else:
        for subdirectory in directory.iterdir():
            if subdirectory.is_dir() and (subdirectory / "level.dat").is_file():
                if subdirectory.name in result:
                    warn("duplicate world IDs")
                result[subdirectory] = get_world_name(subdirectory / "level.dat")
    return result


@click.command()
@click.argument(
    "directory",
    default=os.path.curdir,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
def main(directory: Path) -> None:
    world_names = get_world_names(directory)
    if world_names:
        for path, world_name in world_names.items():
            print(f"{path} - {world_name}")
    else:
        print("no worlds found", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
