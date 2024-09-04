from pathlib import Path

from dissect.cstruct import cstruct

parser = cstruct()
parser.loadfile(Path(__file__).parent / "minecraft3ds.h")
