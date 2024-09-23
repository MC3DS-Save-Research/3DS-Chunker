from io import BytesIO
import shutil
from pathlib import Path

import pyanvileditor
from pyanvileditor.world import World, BlockState
from pyanvileditor.canvas import Canvas
import nbtlib
from nbtlib.tag import String
import json

from . import classes


def convert(
    world_3ds: classes.World,
    blank_world: Path,
    world_out: Path,
    delete_out: bool = False,
) -> None:
    print(world_3ds.vdb[world_3ds.vdb.keys()[0]]._header)
    if world_out.exists():
        if delete_out:
            shutil.rmtree(world_out)
        else:
            raise FileExistsError("world output directory exists")
    shutil.copytree(blank_world, world_out)
    with nbtlib.load(world_out / "level.dat") as level:
        level["Data"]["LevelName"] = String(world_3ds.name)

    converted = {}
    block_ids = {}
    block_states = {}
    # read the JSON files containing MCPE block IDs
    with open(
        Path(__file__).parent / "data" / "minecraft-block-ids" / "blocks_274.json"
    ) as blocks_file:
        raw_blocks = json.load(blocks_file)
    with open(Path(__file__).parent / "data" / "blocksB2J.json") as convert_file:
        convert = json.load(convert_file)
    for old, new in convert.items():
        # remove the data
        old_position = old.find("[")
        if old_position == -1:
            continue
        new_position = new.find("[")
        if new_position == -1:
            continue
        old_name = old[:old_position]
        if old_name in converted:
            pass
        else:
            converted[old_name] = new[:new_position]
    for raw_block in raw_blocks:
        key = (raw_block["id"], raw_block["data"])
        old_name = raw_block["name"]
        try:
            name = converted[old_name]
        except KeyError:
            # ignore Bedrock / Education edition exclusive blocks
            continue
        block_ids[key] = name
        # cache the block states for better performance
        block_states[key] = BlockState(name, {})
    air = block_states[(0, 0)]
    glass = block_states[(20, 0)]
    done = set()
    nether = {}
    end = {}
    print("Placing blocks")
    with World(world_out) as world:
        canvas = Canvas(world)

        for position, dimension, entry, block_id in world_3ds:
            debug = entry.debug
            try:
                new_block = block_states[block_id]
            except KeyError:
                if block_id[0] not in (0, 7, 73):
                    print(f"unknown block {block_id} debug {debug}")
                new_block = air
            if (
                False
                and entry._header.unknownChunkParameter == 0x1
                and new_block == air
            ):
                new_block = glass
            # position = (position[0], position[1] + debug[2] + debug[3] * 8, position[2])
            if new_block.name in (
                "minecraft:nether_portal",
                "minecraft:beacon",
                "minecraft:diamond_block",
            ):
                block_name = block_ids.get(block_id, "unknown")
                print(
                    f"{block_name} {block_id} at {position} dimension {dimension} debug {debug}"
                )
            unique_position = (position, dimension)
            if unique_position in done:
                raise ValueError("blocks overlap")
            else:
                done.add(unique_position)
            if new_block != air:
                if dimension == 0:
                    try:
                        world.get_block(position).set_state(new_block)
                    except Exception as exception:
                        print(f"failed to set block at {position}")
                        raise exception from None
                elif dimension == 1:
                    nether[position] = new_block
                elif dimension == 2:
                    end[position] = new_block
                else:
                    raise ValueError(f"invalid dimension {dimension:d}")
    if nether:
        print("Placing Nether blocks")
        with World(world_out, dimension=1) as world:
            for position, block in nether.items():
                try:
                    world.get_block(position).set_state(block)
                except Exception as exception:
                    print(f"failed to set block at Nether {position}")
                    raise exception from None
    if end:
        print("Placing End blocks")
        with World(world_out, dimension=2) as world:
            for position, block in end.items():
                try:
                    world.get_block(position).set_state(block)
                except Exception as exception:
                    print(f"failed to set block at End {position}")
                    # raise exception from None
