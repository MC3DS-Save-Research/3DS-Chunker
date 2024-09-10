# XNBT
A simple and fast implementation of NBT written in Python 3.

## Getting started
### Prerequisites
To use XNBT you need to have `Python >= 3.7.x` pre-installed.

### Installation
To install XNBT, download or clone the repository:
```shell
git clone https://github.com/MCPI-Devs/xnbt.git
```
There are no aditional requirements.

## Features
+ 100% NBT compatible
+ Basic pretty-print as JSON
+ Zlib and GZip compression support
+ Big- and Little-endian support

## Usage
You can use the [API](#api) and, additionally, you can run the `xnbt.py` file in the root of the repo as:
```
xnbt.py file mode
```
Where `file` is a NBT file and `mode` is a [data mode](#data-modes). It will pretty-print the parsed file as JSON.

## API

### `class xnbt.XNBT(mode="lzr")`
Constructor of the `XNBT` main class. The `mode` argument is a [data mode](#data-modes).

### `def xnbt.XNBT.parse(data)`
Parses `data` and returns a `dict` object containing all the tags in the following format:
```
{
    "type": TAG_Type,
    "name": TAG_Name | None,
    "content": [TAG_Childs] | TAG_Content
}
```

### `def xnbt.XNBT.build(tag)`
Returns `tag` packed into binary format.

### `exception xnbt.NBTParsingError`
An exception raised when a parsing error occurs. Other exceptions such as `OSError`, `gzip.BadGZipFile`, `EOFError` and `zlib.error` can be raised if a compression/decompression error occurs.

## Data modes
A mode is a combination of the following characters:

**Enidanness**
+ `l`: Little-endian
+ `b`: Big-endian
+ `n`: Network default (big-endian)

**Compression:**
+ `u`: Uncompressed
+ `z`: Zlib compression (DEFLATE)
+ `g`: GZip compression (DEFLATE)

**Container format:**
+ `r`: Raw
+ `o`: Old level.dat
+ `e`: Old entities.dat

For an example, a `xnbt.XNBT(mode="bgo")` class manipulates the data as a big-endian, GZip-compressed `level.dat` file.

## Licensing
All the code of this project is licensed under the [GNU General Public License version 2.0](https://github.com/MCPI-Devs/xnbt/blob/master/LICENSE) (GPL-2.0).

All the documentation of this project is licensed under the [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/) (CC BY-SA 4.0) license.

![CC BY-SA 4.0](https://i.creativecommons.org/l/by-sa/4.0/88x31.png)

