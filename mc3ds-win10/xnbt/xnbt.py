#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  xnbt.py
#
#  Copyright 2020 Alvarito050506 <donfrutosgomez@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 2 of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import sys
import struct
import zlib
import gzip
import json
from collections import OrderedDict


class NBTParsingError(Exception):
    pass


class XNBT:
    def __init__(self, mode="lzr"):
        # Endianness constants
        self.BIG = "b"
        self.LITTLE = "l"
        self.NET = "n"
        self.__endianness = "bln"

        # Compression constants
        self.UNCOMPRESSED = "u"
        self.ZLIB = "z"
        self.GZIP = "g"
        self.__compression = "uzg"

        # Conteiner constants
        self.OLD_LEVEL = "o"
        self.LEVELDB = "l"
        # Currently unsupported. TODO.
        self.ENTITIIES = "e"
        self.RAW = "r"
        self.__containers = "oer"

        # Tag ids
        self.__tags = [
            "TAG_End",
            "TAG_Byte",
            "TAG_Short",
            "TAG_Int",
            "TAG_Long",
            "TAG_Float",
            "TAG_Double",
            "TAG_Byte_Array",
            "TAG_String",
            "TAG_List",
            "TAG_Compound",
        ]

        # Warning: Hacky code :)
        self.__reverse_tags = {
            "TAG_End": 0,
            "TAG_Byte": 1,
            "TAG_Short": 2,
            "TAG_Int": 3,
            "TAG_Long": 4,
            "TAG_Float": 5,
            "TAG_Double": 6,
            "TAG_Byte_Array": 7,
            "TAG_String": 8,
            "TAG_List": 9,
            "TAG_Compound": 10,
        }

        self.__level = 0
        self.__lists = []
        self.__list_level = 0
        self.__levels = [0]

        if (
            mode[0] in self.__endianness
            and mode[1] in self.__compression
            and mode[2] in self.__containers
        ):
            self.__mode = mode
        else:
            raise ValueError("invalid mode: " + mode)

        if self.__mode[0] == "b" or self.__mode[0] == "n":
            self.__pack = lambda format, data: struct.pack(">" + format, data)
            self.__unpack = lambda format, data: struct.unpack(">" + format, data)[0]
        elif self.__mode[0] == "l":
            self.__pack = lambda format, data: struct.pack("<" + format, data)
            self.__unpack = lambda format, data: struct.unpack("<" + format, data)[0]

    def parse(self, data):
        if self.__mode[2] == "o":
            if data[:4] != self.__pack("I", 0x03) and data[:4] != self.__pack(
                "I", 0x02
            ):
                raise NBTParsingError("invalid magic number.")
            lenght = self.__unpack("I", data[4:8])
            data = data[8:]
        elif self.__mode[2] == "e":
            if data[:8] != b"ENT\x00" + self.__pack("I", 0x01):
                raise NBTParsingError("invalid magic number.")
            lenght = self.__unpack("I", data[8:12])
            data = data[12:]
        elif self.__mode[2] == "r":
            lenght = len(data)

        if self.__mode[1] == "z":
            data = zlib.decompress(data[:lenght])
        elif self.__mode[1] == "g":
            data = gzip.decompress(data[:lenght])

        if data[0] != 10 or data[-1] != 0:
            raise NBTParsingError("invalid file.")

        return self.__parse_tag(data)[0]

    def build(self, tag):
        data = self.__build_tag(tag)
        if self.__mode[1] == "z":
            data = zlib.compress(data)
        elif self.__mode[1] == "g":
            data = gzip.compress(data)

        if self.__mode[2] == "o":
            data = self.__pack("I", 0x03) + self.__pack("I", len(data)) + data
            data = data
        elif self.__mode[2] == "e":
            data = (
                b"ENT\x00" + self.__pack("I", 0x01) + self.__pack("I", len(data)) + data
            )
        return data

    def __parse_tag(self, data):
        if self.__levels[-1] == 1:
            tag_type = self.__lists[-1]["type"]
        else:
            tag_type = data[0]

        tag = dict()
        tag["type"] = self.__tags[tag_type]
        end = 0

        if tag_type != 0:
            if self.__levels[-1] == 0:
                tag["name"] = data[3 : 3 + self.__unpack("H", data[1:3])].decode(
                    "utf-8"
                )
                start = 3 + len(tag["name"])
            else:
                tag["name"] = None
                start = 0

        if tag_type == 0:
            self.__level -= 1
            end = 1
        elif tag_type == 1:
            end = start + 1
            tag["content"] = data[start]
        elif tag_type == 2:
            end = start + 2
            tag["content"] = self.__unpack("H", data[start:end])
        elif tag_type == 3:
            end = start + 4
            tag["content"] = self.__unpack("I", data[start:end])
        elif tag_type == 4:
            end = start + 8
            tag["content"] = self.__unpack("Q", data[start:end])
        elif tag_type == 5:
            end = start + 4
            tag["content"] = self.__unpack("f", data[start:end])
        elif tag_type == 6:
            end = start + 8
            tag["content"] = self.__unpack("d", data[start:end])
        elif tag_type == 7:
            lenght = self.__unpack("I", data[start : start + 4])
            end = start + 4 + lenght
            tag["content"] = data[start + 4 : end].hex()
        elif tag_type == 8:
            lenght = self.__unpack("H", data[start : start + 2])
            end = start + 2 + lenght
            tag["content"] = data[start + 2 : end].decode("utf-8")
        elif tag_type == 9:
            array_lenght = self.__unpack("I", data[start + 1 : start + 5])
            tag["content"] = []
            sub_end = 0
            i = 0
            self.__lists.append({"type": data[start]})
            tag["list_type"] = data[start]
            start = start + 5
            lenght = 0
            self.__list_level += 1
            self.__levels.append(1)
            while i < array_lenght:
                sub_tag, sub_end = self.__parse_tag(data[start + lenght :])
                tag["content"].append(sub_tag)
                lenght += sub_end
                i += 1
            end = start + lenght
            self.__list_level -= 1
            self.__lists.pop()
            self.__levels.pop()
        elif tag_type == 10:
            self.__level += 1
            tag["content"] = []
            sub_end = 0
            lenght = 0
            self.__levels.append(0)
            while True:
                sub_tag, sub_end = self.__parse_tag(data[start + lenght :])
                if sub_tag["type"] == "TAG_End":
                    lenght += sub_end
                    break
                else:
                    tag["content"].append(sub_tag)
                    lenght += sub_end
            end = start + lenght
            self.__levels.pop()
        return (tag, end)

    def __build_tag(self, tag):
        data = bytes()
        if self.__levels[-1] == 1:
            tag_type = self.__lists[-1]["type"]
        else:
            tag_type = self.__reverse_tags[tag["type"]]
            data = bytes([tag_type])

        if tag_type != 0 and self.__levels[-1] == 0:
            tag_name = bytes(tag["name"], "utf-8")
            data = data + self.__pack("H", len(tag_name)) + tag_name

        if tag_type == 0:
            self.__level -= 1
        elif tag_type == 1:
            data = data + bytes([tag["content"]])
        elif tag_type == 2:
            data = data + self.__pack("H", tag["content"])
        elif tag_type == 3:
            print(tag["content"])
            data = data + self.__pack("I", tag["content"])
        elif tag_type == 4:
            data = data + self.__pack("Q", tag["content"])
        elif tag_type == 5:
            data = data + self.__pack("f", tag["content"])
        elif tag_type == 6:
            data = data + self.__pack("d", tag["content"])
        elif tag_type == 7:
            data = (
                data
                + self.__pack("I", len(bytes.fromhex(tag["content"])))
                + bytes.fromhex(tag["content"])
            )
        elif tag_type == 8:
            data = (
                data
                + self.__pack("H", len(tag["content"]))
                + bytes(tag["content"], "utf-8")
            )
        elif tag_type == 9:
            data = (
                data + bytes([tag["list_type"]]) + self.__pack("I", len(tag["content"]))
            )
            i = 0
            self.__lists.append({"type": tag["list_type"]})
            self.__list_level += 1
            self.__levels.append(1)
            while i < len(tag["content"]):
                sub_data = self.__build_tag(tag["content"][i])
                data = data + sub_data
                i += 1
            self.__list_level -= 1
            self.__lists.pop()
            self.__levels.pop()
        elif tag_type == 10:
            self.__level += 1
            self.__levels.append(0)
            i = 0
            while i < len(tag["content"]):
                sub_data = self.__build_tag(tag["content"][i])
                data = data + sub_data
                i += 1
            data = data + b"\x00"
            self.__levels.pop()
        return data


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Error: Missing required argument.")
        print("Usage: " + sys.argv[0] + " file mode")
        print("Where mode is a combination of the following:")
        print("Enidanness:")
        print("\tl:\tLittle-endian")
        print("\tb:\tBig-endian")
        print("\tn:\tNetwork default (big-endian)\n")
        print("Compression:")
        print("\tu:\tUncompressed")
        print("\tz:\tZlib compression (DEFLATE)")
        print("\tg:\tGZip compression (DEFLATE)\n")
        print("Container format:")
        print("\tr:\tRaw")
        print("\to:\tOld level.dat")
        print("\te:\tOld entities.dat\n")
        sys.exit(1)
    tmp_file = open(sys.argv[1], "rb")
    nbt = XNBT(sys.argv[2])
    parsed = nbt.parse(tmp_file.read())
    print(json.dumps(parsed, indent=4, separators=(", ", ": ")))
    tmp_file.close()
    sys.exit(0)
