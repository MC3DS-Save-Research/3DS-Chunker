import os
import gzip
from io import BytesIO

import pyanvileditor
from pyanvileditor.world import World, BlockState
from pyanvileditor.canvas import Canvas


def convert(block_data: bytes) -> None:
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

        readme = BytesIO(block_data)
        for z in range(0x28):
            for x in range(0x10):
                for y in range(0x10):
                    comeon = int.from_bytes(readme.read(1))
                    try:
                        new_block = mapped[comeon]
                    except KeyError:
                        print(f"0x{comeon:X}")
                        new_block = DEFAULT
                    position = (x, 0x28 - 1 - y, z)
                    world.get_block(position).set_state(new_block)
                    print(position)


def main() -> None:
    convert("../World")


if __name__ == "__main__":
    main()
