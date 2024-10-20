from io import BytesIO
from typing import Any

from .xnbt import XNBT
from pynbt import NBTFile

BEDROCK_HEADER_SIZE: int = 0x8


class NewNBT:
    def __init__(self, buffer: bytes) -> None:
        self.buffer = buffer
        self._parse(buffer)

    def _parse(self, buffer: bytes) -> None:
        self.nbt = NBTFile(BytesIO(self.buffer), little_endian=True)


class NBT:
    def __init__(self, buffer: bytes) -> None:
        self.xnbt = XNBT("lur")
        self._parse(buffer)

    def _parse(self, buffer: bytes) -> None:
        self.raw = self.xnbt.parse(buffer[BEDROCK_HEADER_SIZE:])
        self.__cached = False
        self.__value_cache = None

    @classmethod
    def process(cls, value: dict) -> Any:
        content = value["content"]
        if isinstance(content, list):
            result = {}
            fake_list = False  # some lists are just dicts, but they use the name attribute as the key
            for value in content:
                key = value["name"]
                if key:
                    # input(f"result[{repr(key)}] = {repr(cls.process(value))}")
                    result[key] = cls.process(value)
                    fake_list = True
            if result and not fake_list:
                raise ValueError("combined list and dict")
            elif fake_list:
                return result
            else:
                result = []
                for value in content:
                    result.append(cls.process(value))
                return result
        elif isinstance(content, dict):
            result = {}
            for key, value in content:
                result[key] = cls.process(value)
            return result
        else:
            return content

    @property
    def value(self) -> dict | list:
        if not self.__cached:
            self.__value_cache = self.process(self.raw)
            self.__cached = True
        return self.__value_cache

    def get(self, key: Any, default: Any = None) -> Any:
        return self.value.get(key, default)

    def __getitem__(self, key: Any) -> Any:
        return self.value[key]

    def buffer(self, value: bytes) -> None:
        self._parse(value)

    # write-only
    buffer = property(fset=buffer)
