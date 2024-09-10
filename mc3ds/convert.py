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
    if world_out.exists():
        if delete_out:
            shutil.rmtree(world_out)
        else:
            raise FileExistsError("world output directory exists")
    shutil.copytree(blank_world, world_out)
    with nbtlib.load(world_out / "level.dat") as level:
        level["Data"]["LevelName"] = String(world_3ds.name)
    extracted = world_3ds.extracted

    block_ids = {}
    block_states = {}
    # read the JSON files containing MCPE block IDs
    with open(
        Path(__file__).parent / "minecraft-block-ids" / "blocks_274.json"
    ) as blocks_file:
        raw_blocks = json.load(blocks_file)
    for raw_block in raw_blocks:
        key = (raw_block["id"], raw_block["data"])
        name = raw_block["name"]
        if name == "minecraft:grass":
            name = "minecraft:grass_block"
        elif name == "minecraft:tallgrass":
            name = "minecraft:grass"
        elif name == "minecraft:portal":
            name = "minecraft:nether_portal"
        block_ids[key] = name
        # cache the block states for better performance
        block_states[key] = BlockState(name, {})
    air = block_states[(0, 0)]

    with World(world_out) as world:
        canvas = Canvas(world)

        DEFAULT = BlockState("minecraft:stone", {})
        # mapped = {}
        # unmapped = {
        #     0: "air",
        #     1: "stone",
        #     2: "grass_block",
        #     3: "dirt",
        #     4: "cobblestone",
        #     5: "oak_planks",
        #     7: "bedrock",
        #     8: "oak_leaves",
        #     11: "lava",
        #     12: "sand",
        #     35: "white_wool",
        #     47: "bookshelf",
        #     49: "obsidian",
        #     50: "torch",
        #     57: "diamond_block",
        #     86: "pumpkin",
        #     87: "netherrack",
        #     90: "portal",
        #     153: "quartz_ore",
        # }
        # for item_id, name in unmapped.items():
        #     mapped[item_id] = BlockState(f"minecraft:{name}", {})

        """
        (252,5,4): (15,0,1,1)
        """

        for position, debug, block_id in world_3ds:
            new_block = block_states[block_id]
            # position = (position[0], position[1] + debug[2] + debug[3] * 8, position[2])
            if new_block.name in ("minecraft:wool", "minecraft:sand"):
                block_name = block_ids.get(block_id, "unknown")
                print(f"{block_name} {block_id} at {position} debug {debug}")
            if new_block != air:
                try:
                    world.get_block(position).set_state(new_block)
                except Exception as exception:
                    pass  # print(position)
                    # raise exception from None
