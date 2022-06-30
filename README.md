# .tmod Extraction tools

Simple utilities for extracting content from tModLoader Mod files (`.tmod`)

## Utilities

`tmod_extract.py`
- Extract all content from a `.tmod` file.

`tmod_decompress.py`
- Decompress files from the `.tmod` archive.

`rawimg_to_png.py`
- Convert `.rawimg` files to `.png` (note: files must be decompressed first!)

## Example usage

Automatically using only `tmod_extract.py`:

```sh
# Automatically extract files, decompress them, convert images, AND replace the old files.
$ python tmod_extract.py -ar SomeMod.tmod
```

Manually extracting, decompressing files and converting images:

```sh
# Extract the mod contents.
# This will also write the file `entries.txt` to the extracted mod folder
# which can be used to decompress the contents (`entries.txt` will _not_ be written if `-a` is used.)
# (Contents will be written to `out/$MODNAME/`, in this case, `out/SomeMod/`)
$ python tmod_extract.py SomeMod.tmod

# Decompress the resulting files (using the `entries.txt` file)
# Use `-r` to replace the original uncompressed files, and `-e` to specify the `entries.txt` file.
$ python tmod_decompress.py -r -e out/SomeMod/entries.txt

# Convert the `.rawimg` files to usable png files.
# (Use the same command line arguments as last time.)
$ python rawimg_to_png.py -r -e out/SomeMod/entries.txt
```

## Dependencies

- Pillow (`for` image read/writing)