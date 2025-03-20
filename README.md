# 3DS-Chunker
This is a WIP tool for Converting Worlds to/from 3DS Edition and Java Edition.

### Installation
- Run `pip install git+https://github.com/MC3DS-Save-Research/3DS-Chunker` to install from GitHub.
- Or `pip install -e .` to install from a local copy (for development).

### Usage

To use this, you must have homebrew on your 3DS to decrypt the save files and [Checkpoint](https://github.com/BernardoGiordano/Checkpoint) installed.  If you don't have it installed, follow [3ds.hacks.guide](https://3ds.hacks.guide/), which will also install Checkpoint.

Open Checkpoint from the HOME menu and press X for extdata, then backup "Minecraft: New Nintendo 3DS Edition".  Once you have that backed up, plug your SD card into your computer and go to `3ds/Checkpoint/extdata/<unique id> Minecraft: New Nintendo 3DS Edition` and extract the .zip.  Open a command prompt in `minecraftWorlds` and run the `ls3ds` command.  You should get output similar to the following:

```none
EgAAADRWeJA= - My World
qgAAALvM3e4= - Another World
...
```

Choose the world that you want to convert.  For example, if you want to extract `My World`, run `3dschunker EgAAADRWeJA=`.  If successful, the `Converted` folder should be made, copy this to Minecraft Java Edition 1.16.5 and enjoy!

### Contributors
- [Anonymous941](https://github.com/Anonymous941) - Main Developer of Tool.
- [DexrnZacAttack](https://github.com/DexrnZacAttack) - Contributor.
- [Offroaders123](https://github.com/Offroaders123) - Contributor.
- <ins>Evocated</ins> - Contributor.
- [Cracko298](https://github.com/Cracko298) - GUI Maintainer.

### Note
This is not affiliated with [Chunker](https://chunker.app/), an official tool to convert between Java and Bedrock worlds.  The name is inspired by that, however (hopefully it's fair use)
