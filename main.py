from tkinter import filedialog, messagebox
from os import getcwd, system
from mc3ds.nbt import NBT
import tkinter as tk
import subprocess
import sys

BLANK_WORLD_PATH = f"{getcwd()}\\mc3ds\\worlds\\blankWorld"
print(BLANK_WORLD_PATH)
DEP_LIST = ["dissect.cstruct", "anvil-new", "click", "nbtlib", "p_tqdm"]

def startConversion(worldName:str):
    system(f'py -m mc3ds -c "{folder_path}" -o ".\\output" -b "{BLANK_WORLD_PATH}" -w "{worldName}"')

def getWorldName(byteData:bytes):
    return str(NBT(byteData).get("LevelName"))

def getWorld():
    global folder_path, levelDatPath
    folder_path = filedialog.askdirectory()
    if folder_path:
        folder_entry.config(state=tk.NORMAL)
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, folder_path)
        folder_entry.config(state=tk.DISABLED)
        levelDatPath = f"{folder_path}/level.dat"

def beforeConvert():
    try: import p_tqdm
    except ImportError:
        answer = messagebox.askyesno("Module Notice", "3DS-Chunker needs some modules to opperate.\nMay it install them now?")
        if answer:
            for module in DEP_LIST:system(f'pip install {module}')
        else:sys.exit(1)
    with open(levelDatPath, 'rb+') as f:
        worldName = getWorldName(f.read())
    startConversion(worldName)

root = tk.Tk()
root.title("MC3DS Chunker - GUI")
root.geometry("600x200")
root.resizable(False, False)
root.config(background='black')

frame = tk.Frame(root)
frame.config(background='black')
frame.pack(pady=20, padx=10)
folder_entry = tk.Entry(frame, width=80)
folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
import_button = tk.Button(frame, text="...", command=getWorld, border=0)
import_button.pack(side=tk.RIGHT, padx=5)

bottom_frame = tk.Frame(root, bg='black')
bottom_frame.pack(side=tk.BOTTOM, pady=10)
center_button = tk.Button(bottom_frame, text="Convert 3DS to Java", command=beforeConvert)
center_button.pack(side=tk.BOTTOM, pady=10)

root.mainloop()