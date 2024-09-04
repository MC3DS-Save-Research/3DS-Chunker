from io import BytesIO
import typing
import zlib

from parser import *


class BaseParser:
    def __init__(self, stream: BytesIO) -> None:
        self._stream = stream
        self._offset = stream.tell()
        self._load_data()

    def _load_data(self) -> None:
        self._reload_data()

    def _reload_data(self) -> None:
        pass

    def _seek(self, position: int) -> None:
        self._stream.seek(self._offset + position)


class Subfile(BaseParser):
    def __init__(self, stream: BytesIO, subfile_size: int) -> None:
        self._size = subfile_size
        super().__init__(stream)

    # it's a property so it's read only
    @property
    def size(self) -> int:
        return self._size

    def __len__(self) -> int:
        return self.size

    def _reload_data(self) -> None:
        self._seek(0)
        self._header = parser.SubfileHeader(self._stream)

    @property
    def filler(self) -> bool:
        # some subfiles have a header of all zeroes, and this avoids an error when parsing
        return self._header.magic == 0

    @property
    def raw(self) -> bytes | None:
        if self.filler:
            return None
        self._seek(self._header.size)
        content = self._stream.read(self.size - self._header.size)
        return content


class IterDB:
    def __init__(self, db) -> None:
        self._db = db
        self.__index = 0

    def __next__(self) -> tuple[int, typing.Any]:
        while True:
            if self.__index > len(self._db) - 1:
                raise StopIteration
            new_subfile = self._db[self.__index]
            self.__index += 1
            if not new_subfile.filler:
                break
        return self.__index - 1, new_subfile


class DBFile(BaseParser):
    def _reload_data(self) -> None:
        self._header = parser.FileHeader(self._stream)

    @property
    def something(self) -> tuple[int]:
        return (self._header.something0, self._header.something1)

    @property
    def unknown(self) -> tuple[int]:
        return (self._header.unknown0, self._header.unknown1)

    @property
    def subfile_count(self) -> int:
        return self._header.subfileCount

    @property
    def subfile_size(self) -> int:
        return self._header.subfileSize

    def __len__(self) -> int:
        return self.subfile_count

    def _parse(self, subfile: Subfile):
        return subfile

    def __iter__(self) -> IterDB:
        return IterDB(self)

    def __getitem__(self, key: int) -> bytes | None:
        if key > self.subfile_size - 1:
            raise IndexError("index out of range")
        if key < 0:
            key = self.subfile_size + key
            # if it's still negative, it's out of range
            if key < 0:
                raise IndexError("index out of range")

        self._seek(self.subfile_size * key)
        return self._parse(Subfile(self._stream, self.subfile_size))


class Subchunk:
    def __init__(self, compressed: bytes) -> None:
        self._compressed = compressed

    @property
    def compressed(self) -> bytes:
        return self._compressed

    @property
    def decompressed(self) -> bytes:
        return zlib.decompress(self._compressed)


class IterChunk:
    def __init__(self, chunk) -> None:
        self._chunk = chunk
        self.__index = 0

    def __next__(self) -> tuple[int, Subchunk]:
        while True:
            if self.__index > len(self._chunk) - 1:
                raise StopIteration
            new_subchunk = self._chunk[self.__index]
            self.__index += 1
            if new_subchunk is not None:
                break
        return self.__index - 1, new_subchunk


class Chunk:
    def __init__(self, subfile: Subfile) -> None:
        self.__section = 0
        self._subfile = subfile
        self._load_data()

    def _load_data(self) -> None:
        self._reload_data()

    def _reload_data(self) -> None:
        self._raw = self._subfile.raw
        self._header = parser.ChunkHeader(self._raw)

    @property
    def unknown0(self) -> int:
        return self._header.unknown0

    @property
    def unknown1(self) -> int:
        return self._header.unknown1

    @property
    def filler(self) -> bool:
        return self._subfile.filler

    @property
    def sections(self) -> int:
        return 0 if self.filler else len(self._header.sections)

    def __len__(self) -> int:
        return self.sections

    def __iter__(self):
        return IterChunk(self)

    def __getitem__(self, key: int) -> Subchunk:
        if self.filler:
            raise ValueError("cannot read filler")
        if key > self.sections - 1:
            raise IndexError("index out of range")
        if key < 0:
            key = self.subfile_size + key
            # if it's still negative, it's out of range
            if key < 0:
                raise IndexError("index out of range")

        skipped = 0
        start = self._header.size
        decompress_object = zlib.decompressobj()
        for section in self._header.sections:
            if section.index == key:
                size = section.compressedSize
                break
            # skip past the decompressed data
            elif section.index != -1:
                start += section.decompressedSize
        else:
            # doesn't exist
            return None
        subchunk = Subchunk(self._raw[start:])
        try:
            subchunk.decompressed
        except Exception:
            print(repr(self._header))
        return subchunk


class CDBFile(DBFile):
    def _parse(self, subfile: Subfile):
        return Chunk(subfile)
