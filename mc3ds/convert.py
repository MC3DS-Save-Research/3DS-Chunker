import sys
import shutil
from pathlib import Path
import random
import re
import json5
import asyncio
import logging
from multiprocessing import Lock
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from typing import Any

from anvil import EmptyRegion, Block
import nbtlib
from nbtlib.tag import String
from tqdm import tqdm
from p_tqdm import p_umap, p_uimap

from .classes import World, Entry
from .EmptyChunk import EmptyChunk

OVERWORLD = 0
NETHER = 1
END = 2

AIR = (0, 0)

logger = logging.getLogger(__name__)


class ChunkConverter:
    def __init__(
        self, position: tuple[int, int, int], entry: Entry, blocks: dict
    ) -> None:
        self.chunk_x, self.chunk_z, self.dimension = position
        self.entry = entry
        self.blocks = blocks
        self.chunk = EmptyChunk(self.chunk_x, self.chunk_z)

    def place_blocks(self) -> None:
        setted = set()
        for subchunk_y, subchunk in enumerate(self.entry.data_chunk.data.subchunks):
            y_offset = subchunk_y * 16
            for x, row in enumerate(subchunk.blocks):
                for z, column in enumerate(row):
                    for y, block in enumerate(column):
                        unknown_block_data = subchunk.unknownBlockData[x][z][y]
                        calculated_y = y + y_offset
                        pos = x, calculated_y, z
                        setted.add(pos)
                        position = x * 16 * 16 + z * 16 + y
                        # extract the nibble from the byte
                        block_byte = subchunk.blockData[position // 2]
                        if position % 2 == 0:
                            block_data = block_byte & 0xF
                        else:
                            block_data = block_byte >> 4

                        block_id = (block, block_data)
                        if unknown_block_data:
                            raise ValueError(
                                f"UNKNOWN UNKNOWN UNKNOWN 0x{unknown_block_data:02X}"
                            )
                            if block_id == AIR:
                                block = Block("minecraft", "glass")
                                self.chunk.set_block(block, x, calculated_y, z)
                                continue
                        if block_id != AIR:
                            try:
                                block = self.blocks[block_id]
                            except KeyError:
                                logger.warning(
                                    f"unknown block {block_id} at {(self.chunk_x * 16 + x, calculated_y, self.chunk_z * 16 + z)} dimension {self.dimension}"
                                )
                                sys.stderr.flush()
                                block = Block("minecraft", "netherite_block")
                            self.chunk.set_block(block, x, calculated_y, z)

    def place_biomes(self) -> None:
        for section_z, biome_z in enumerate(self.entry.data_chunk.data.biomes):
            for section_x, biome_v in enumerate(biome_z):
                self.chunk.paint_biome_column(section_x, section_z, biome_v)

    @property
    def region_position(self) -> tuple[int, int, int]:
        return self.chunk_x // 32, self.chunk_z // 32, self.dimension


class RegionConverter:
    def __init__(self, world_directory: Path, position: tuple[int, int, int]) -> None:
        self.region_x, self.region_z, self.dimension = position
        self.world_directory = Path(world_directory)
        if self.dimension == OVERWORLD:
            dimension_path = self.world_directory
        elif self.dimension == NETHER:
            dimension_path = self.world_directory / "DIM-1"
        elif self.dimension == END:
            dimension_path = self.world_directory / "DIM1"
        else:
            raise ValueError("invalid dimension")
        self.region_file = (
            dimension_path / "region" / f"r.{self.region_x:d}.{self.region_z:d}.mca"
        )
        self.region = EmptyRegion(self.region_x, self.region_z)
        self.chunk_count = 0

    def add_chunk(self, chunk: EmptyChunk) -> None:
        self.region.add_chunk(chunk)

    def save(self) -> None:
        # if the region directory hasn't been generated yet, create it
        if self.world_directory.exists():
            self.region_file.parent.mkdir(parents=True, exist_ok=True)
        self.region.save(str(self.region_file))


def parse_block_json(raw_blocks: dict) -> dict:
    block_json = re.compile(r"^([^\[\]]+)(?:\[([^\[\]]*)\])?$")
    blocks = {}

    for numerical_id, new in raw_blocks["blocks"].items():
        block_str, data_str = numerical_id.split(":")
        block_id = (int(block_str), int(data_str))

        # convert minecraft:item[key=value,otherkey=value] to {"key": "value", "otherkey": "value"}
        parsed = block_json.match(new)
        if parsed is None:
            raise ValueError("invalid block")
        name = parsed[1]
        raw_nbt_data = parsed[2]
        # intentionally not using "is None" because it should match an empty string too
        if raw_nbt_data:
            nbt_data = dict(item.split("=") for item in raw_nbt_data.split(","))
        else:
            nbt_data = {}

        namespace, block = name.split(":")
        blocks[block_id] = Block(namespace, block, nbt_data)

    return blocks


def convert(
    world: World,
    blank_world: Path,
    world_out: Path,
    delete_out: bool = False,
    interactive: bool = True,
    world_void = False,
) -> None:
    if world_out.exists():
        if not world_out.is_dir() or not (world_out / "level.dat").is_file():
            raise FileExistsError(
                "world output folder already exists, and is not a Java savefile, did you select the right folder?"
            )
        elif delete_out:
            shutil.rmtree(world_out)
        elif interactive:
            print("A converted world already exists, do you want to overwrite it?")
            while True:
                choice = input("[y/n]> ").strip().upper()
                if choice in ("Y", "YES"):
                    shutil.rmtree(world_out)
                    break
                elif choice in ("N", "NO"):
                    print("world output folder already exists", file=sys.stderr)
                    sys.exit(1)
                elif not choice:
                    pass
                else:
                    print("Invalid input, please enter Y or N")
        else:
            print("world output folder already exists", file=sys.stderr)
            sys.exit(1)
    shutil.copytree(blank_world, world_out)
    with nbtlib.load(world_out / "level.dat") as level:
        level["Data"]["LevelName"] = String(world.name)
        # Set world spawn point
        level["Data"]["SpawnX"] = nbtlib.tag.Int(world.metadata.value["SpawnX"])
        #level["Data"]["SpawnY"] = nbtlib.tag.Int(world.metadata.value["SpawnY"]) # the 3ds value is weird
        level["Data"]["SpawnZ"] = nbtlib.tag.Int(world.metadata.value["SpawnZ"])
        #level["Data"]["GameRules"] = nbtlib.tag.Compound()
        #level["Data"]["GameRules"]["doMobSpawning"] = nbtlib.tag.String("true")
        if "fml" in level:
            del level["fml"]
        if "forge" in level:
            del level["forge"]
        # Delete Player from level.dat so it uses the world spawn point (at least while no player info is imported)
        if "Player" in level["Data"]:
            del level["Data"]["Player"]
        if "DataPacks" in level["Data"]:
            del level["Data"]["DataPacks"]
        if "GameRules" in level["Data"]:
            del level["Data"]["GameRules"]

        # remove when no void world
        if not world_void:
            if "WorldGenSettings" in level["Data"]:
                del level["Data"]["WorldGenSettings"]

        if "CustomBossEvents" in level["Data"]:
            del level["Data"]["CustomBossEvents"]
        if "ServerBrands" in level["Data"]:
            del level["Data"]["ServerBrands"]
        #if "WasModded" in level["Data"]:
            #del level["Data"]["WasModded"]
        if "ScheduledEvents" in level["Data"]:
            del level["Data"]["ScheduledEvents"]
        #print(level["Data"])
    #sys.exit(0)

    # read the JSON files containing MCPE block IDs
    with open(Path(__file__).parent / "data" / "blocks.jsonc") as blocks_file:
        raw_blocks = json5.load(blocks_file)
    blocks = parse_block_json(raw_blocks)

    chunk_converters: list[ChunkConverter] = []

    for position, entry in world.entries.items():
        chunk_converters.append(ChunkConverter(position, entry, blocks))

    def convert_chunk(
        chunk_converter: ChunkConverter,
    ) -> tuple[tuple[int, int, int], EmptyChunk]:
        chunk_converter.place_blocks()
        return chunk_converter.region_position, chunk_converter.chunk

    regions = {}

    def process_region(
        region_position: tuple[int, int, int], chunk_converters: list[EmptyChunk]
    ):
        assert region_position not in regions
        regions[region_position] = region_converter = RegionConverter(
            world_out, region_position
        )
        for chunk in chunk_converters:
            region_converter.add_chunk(chunk)

    def save_region(region_converter: RegionConverter) -> None:
        region_converter.save()

    chunk_regions = defaultdict(list)
    region_converters: dict[Any, RegionConverter] = {}

    class DummyPoolExecutorContext:
        def map(self, func, iter):
            for thing in iter:
                yield func(thing)

    class DummyPoolExecutor:
        def __enter__(self):
            return DummyPoolExecutorContext()

        def __exit__(self, exc_type, exc_value, traceback):
            return False
        
    # get all regions
    for chunk_converter in chunk_converters:
        current_region_position = chunk_converter.region_position
        if not current_region_position in region_converters:
            region_converters[current_region_position] = RegionConverter(world_out, current_region_position)
            region_converters[current_region_position].chunk_count = 1
        else:
            region_converters[current_region_position].chunk_count += 1

    # process chunks for each region, save it and discard after to save memory
    total_regions = len(region_converters.keys())
    for ri, key in enumerate(list(region_converters.keys())):
        count = 0
        pbar = tqdm(total=region_converters[key].chunk_count, desc=f"Converting region {ri+1}/{total_regions} chunks")
        for chunk_converter in chunk_converters[:]:
            current_region_position = chunk_converter.region_position
            if key == current_region_position:
                count += 1
                chunk_converter.place_blocks()
                chunk_converter.place_biomes()
                region_converters[key].add_chunk(chunk_converter.chunk)
                chunk_converters.remove(chunk_converter)
                pbar.update()
        save_region(region_converters[key])
        del region_converters[key]

    # disable threads
    """
    ThreadPoolExecutor = DummyPoolExecutor
    with ThreadPoolExecutor() as executor:
        for current_region_position, chunk in tqdm(
            executor.map(convert_chunk, chunk_converters),
            total=len(chunk_converters),
            desc="Converting chunks",
            unit="chunk",
        ):
            region_converter = region_converters[current_region_position]
            region_converter.add_chunk(chunk)
            # chunk_converters = chunk_regions[current_region_position]
            # chunk_converters.append(chunk)
        # tuple(
        #     tqdm(
        #         executor.map(
        #             lambda keyvalue: process_region(*keyvalue), chunk_regions.items()
        #         ),
        #         total=len(chunk_regions),
        #         desc="Adding chunks to regions",
        #         unit="region",
        #     )
        # )

        for region_converter in tqdm(
            region_converters.values(), desc="Saving regions", unit="region"
        ):
            save_region(region_converter)
    """