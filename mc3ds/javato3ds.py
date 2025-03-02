from pathlib import Path
import json
import logging

from anvil import Region, Chunk, Block

from .convert import parse_block_json

logger = logging.getLogger(__name__)

OVERWORLD = 0
NETHER = 1
END = 2


class RegionJavaConverter:
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
        with open(self.region_file, "rb") as region_handle:
            self.region = Region.from_file(region_handle)

        chunk = self.region.get_chunk(1, 1)
        for block in chunk.stream_chunk():
            if block.name() != "minecraft:air":
                logger.debug(block)


def convert_java(world_3ds: Path, java_world: Path, delete_out: bool) -> None:
    with open(Path(__file__).parent / "data" / "blocks.json") as blocks_file:
        raw_blocks = json.load(blocks_file)
    blocks = parse_block_json(raw_blocks)
    test_converter = RegionJavaConverter(java_world, (0, 0, 0))
