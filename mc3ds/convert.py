import os
import gzip
from io import BytesIO

import pyanvileditor
from pyanvileditor.world import World, BlockState
from pyanvileditor.canvas import Canvas


def convert(extracted: dict) -> None:
    # with gzip.open(os.path.join(path, "level.dat"), mode="rb") as level:
    #     in_stream = pyanvileditor.stream.InputStream(level.read())
    #     level_data = pyanvileditor.nbt.parse_nbt(in_stream)
    #     level_name = level_data.get("Data").get("LevelName").get()
    #     print(level_name)
    with World("../World") as world:
        canvas = Canvas(world)

        air = BlockState("minecraft:air", {})
        dirt = BlockState("minecraft:dirt", {})
        grass = BlockState("minecraft:grass_block", {})
        bedrock = BlockState("minecraft:bedrock", {})
        DEFAULT = air
        mapped = {0x0: air, 0x2: bedrock, 0x3: dirt, 0x7: grass}

        for position, blocks in extracted.items():
            readme = BytesIO(blocks[0].data[0][0])
            for z in range(0x28):
                for x in range(0x10):
                    for y in range(0x10):
                        comeon = int.from_bytes(readme.read(1))
                        try:
                            new_block = mapped[comeon]
                        except KeyError:
                            print(f"0x{comeon:X}")
                            new_block = DEFAULT
                        offset_x = position[0] * 0x10
                        offset_z = position[1] * 0x28
                        pos = (x + offset_x, 0x28 - 1 - y, z + offset_z)
                        world.get_block(pos).set_state(new_block)
                        if new_block != air:
                            print(position)
            break


def main() -> None:
    convert("../World")


if __name__ == "__main__":
    main()
