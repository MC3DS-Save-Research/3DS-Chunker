# 3DS-Chunker
This is a WIP tool for Converting Worlds to/from 3DS Edition and Java Edition.

### Installation
- Run `pip install git+https://github.com/MC3DS-Save-Research/3DS-Chunker` to install from GitHub.
- Or `pip install -e .` to install from a local copy (for development).

### Usage

To use this, you must have homebrew on your 3DS to decrypt the save files and [Checkpoint](https://github.com/BernardoGiordano/Checkpoint) installed.  If you don't have it installed, follow [3ds.hacks.guide](https://3ds.hacks.guide/), which will also install Checkpoint.

Open Checkpoint from the HOME menu and press X for extdata, then backup "Minecraft: New Nintendo 3DS Edition".  Once you have that backed up, plug your SD card into your computer and go to `3ds/Checkpoint/extdata/<unique id> Minecraft: New Nintendo 3DS Edition` and extract the .zip.  Open a command prompt in `minecraftWorlds` and run the `ls3ds` command.  You should get output similar to the following example:

```none
EgAAADRWeJA= - My World
qgAAALvM3e4= - Another World
...
```

Choose the world that you want to convert.  For example, if you want to extract `My World`, run `3dschunker EgAAADRWeJA=`.  If successful, the `Converted` folder should be made, copy this to Minecraft Java Edition 1.16.5 and enjoy!

### FAQ

**Q:** Can you convert a world from Java Edition to 3DS?  
**A:** This is a very popular request, and I am working on adding that.  Currently there is an issue where when modifying chunks, Minecraft 3DS Edition deletes everything.  Once this issue is resolved, hopefully I can finally make a Java to 3DS option.

**Q:** How do you convert to Bedrock Edition?  
**A:** This program only converts to Java Edition, but you can use the [official Chunker app](https://learn.microsoft.com/en-us/minecraft/creator/documents/chunkeroverview) and convert the output like any other world.

**Q:** Minecraft crashes when trying to open the world!  
**Q:** The world loads, but doesn't look correct.  
**Q:** I'm getting an error, did I do something wrong?  
**A:** Make sure you are using Minecraft Java Edition 1.16.5.  If it still doesn't work, this program is very experimental at the moment, so errors are probably a bug in this program.  To get it fixed, either create an issue or [join the Discord](https://discord.gg/MzHSuHmhsY) and ping Anonymous941, posting the full error message or Minecraft log (if relevant)

**Q:** How can I help with this project?  
**A:** You can help test it even if you're not a programmer, just try converting your worlds and see if it works, and if the converted world looks correct.

### Contributors
- [Anonymous941](https://github.com/Anonymous941) - Main Developer of Tool.
- [DexrnZacAttack](https://github.com/DexrnZacAttack) - Contributor.
- [Offroaders123](https://github.com/Offroaders123) - Contributor.
- <ins>Evocated</ins> - Contributor.
- [Cracko298](https://github.com/Cracko298) - GUI Maintainer.

### Note
This is not affiliated with [Chunker](https://chunker.app/), an official tool to convert between Java and Bedrock worlds.  The name is inspired by that, however (hopefully it's fair use)
