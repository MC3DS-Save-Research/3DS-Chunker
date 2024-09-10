from io import BytesIO
import shutil
from pathlib import Path

import pyanvileditor
from pyanvileditor.world import World, BlockState
from pyanvileditor.canvas import Canvas
import nbtlib
from nbtlib.tag import String

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
    with World(world_out) as world:
        canvas = Canvas(world)

        air = BlockState("minecraft:air", {})
        dirt = BlockState("minecraft:dirt", {})
        grass = BlockState("minecraft:grass_block", {})
        bedrock = BlockState("minecraft:bedrock", {})
        DEFAULT = BlockState("minecraft:stone", {})
        mapped = {}
        unmapped = {
            0: "air",
            1: "stone",
            2: "grass_block",
            3: "dirt",
            4: "cobblestone",
            5: "oak_planks",
            7: "bedrock",
            8: "oak_leaves",
            12: "sand",
            35: "white_wool",
            47: "bookshelf",
            50: "torch",
            86: "pumpkin",
        }
        # cache the blocks for better performance
        for item_id, name in unmapped.items():
            mapped[item_id] = BlockState(f"minecraft:{name}", {})

        for position, debug, block_id in world_3ds:
            printer = False
            try:
                new_block = mapped[block_id]
            except KeyError:
                new_block = DEFAULT
                printer = True
            # position = (position[0], position[1] + debug[2] + debug[3] * 8, position[2])
            if printer or new_block.name in ("minercaft:white_wool", "minecraft:sand"):
                block_name = unmapped.get(block_id, f"unknown {block_id:d}")
                print(f"{block_name} at {position} debug {debug}")
            if new_block != air:
                try:
                    world.get_block(position).set_state(new_block)
                except Exception as exception:
                    pass  # print(position)
                    # raise exception from None
