import sys
from io import BytesIO
import shutil
from pathlib import Path
import random
import json

import pyanvileditor
from pyanvileditor.world import World, BlockState
from pyanvileditor.canvas import Canvas
import nbtlib
from nbtlib.tag import String
from tqdm import tqdm

from . import classes


def convert(
    world_3ds: classes.World,
    blank_world: Path,
    world_out: Path,
    delete_out: bool = False,
) -> None:
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
    netherite_block = BlockState("minecraft:netherite_block", {})
    done = set()
    overworld = {}
    nether = {}
    end = {}
    total = 0
    for entry in world_3ds.entries.values():
        total += 16 * 16 * 16 * entry.subchunk_count
    blocks_since_update = 0  # blocks since progress bar update
    with tqdm(total=total, unit="block", desc="Parsing chunks") as progress_bar:
        for position, dimension, entry, block_id in world_3ds:
            try:
                new_block = block_states[block_id]
            except KeyError:
                unknown_block = True
                new_block = netherite_block
                print(f"unknown {block_id} at {position} dimension {dimension}")
            else:
                unknown_block = False
            # unique_position = (position, dimension)
            # if unique_position in done:
            #     raise ValueError("blocks overlap")
            # else:
            #     done.add(unique_position)
            if new_block != air:
                if dimension == 0:
                    overworld[position] = new_block
                elif dimension == 1:
                    nether[position] = new_block
                elif dimension == 2:
                    end[position] = new_block
                else:
                    raise ValueError(f"invalid dimension {dimension:d}")
            blocks_since_update += 1
            if random.randint(1, 1000) == 1:
                progress_bar.update(blocks_since_update)
                blocks_since_update = 0

    def place_dimension(number, blocks, name):
        if not blocks:
            return
        total = len(blocks)
        with World(world_out, dimension=number) as world:
            for position, block in tqdm(
                blocks.items(), desc=f"Placing {name} blocks", unit="block"
            ):
                try:
                    world.get_block(position).set_state(block)
                except Exception as exception:
                    print(f"failed to set block at {postion}", file=sys.stderr)
                    # raise exception from None

    place_dimension(0, overworld, "Overworld")
    place_dimension(1, nether, "Nether")
    place_dimension(2, end, "End")
