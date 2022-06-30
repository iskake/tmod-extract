#!/usr/bin/env python3

import sys
import os
import argparse
from PIL import Image
from tmod_decompress import decompress
from pathlib import Path
from path_helpers import path_append_extension

RAWIMG_SUPPORTED_VERSION = 1


def rawimg_to_png(filename: Path, outname: Path = None) -> bool:
    # ext = filename.suffix
    # if ext != "rawimg":
    #     if not ignore_errors:
    #         raise RuntimeError(f"Invalid file extension `{ext}` (should be `rawimg`)")

    try:
        with open(filename, 'rb') as f:
            file = f.read()
    except FileNotFoundError as e:
        message = f"An exception occurred: {e}"
        if ignore_errors:
            print(message)
            return False
        else:
            raise RuntimeError(message)

    file_version = int.from_bytes(list(file)[:4], 'little')
    if (file_version != RAWIMG_SUPPORTED_VERSION):
        raise Exception(f"""Invalid rawimg version: {file_version} (supported version: {RAWIMG_SUPPORTED_VERSION})
Are you sure this is a (decompressed) rawimg file?""")
    file_w = int.from_bytes(list(file)[4:8], 'little')
    file_h = int.from_bytes(list(file)[8:12], 'little')

    try:
        image = Image.frombytes(
            'RGBA', (file_w, file_h), bytes(list(file)[12:]))
        if outname is None:
            outname = filename.with_suffix("")
        image.save(outname.with_suffix(".png"), "PNG")

        return True
    except Exception as e:
        message = f"""An exception occurred: {e}
Did you forget to decompress the image? (use `decompress.py` or the `-d` command line argument)"""

        if ignore_errors:
            print(message)
        else:
            raise RuntimeError(message)

        return False


def convert_image(image: Path, decompress: bool = False, replace: bool = False) -> None:
    if decompress:
        image_in = path_append_extension(image, ".tmp")
        image_out = image.with_suffix(".png")
        print(f"    Decompressing image...")
        decompress(image, image_in, ignore_errors)
    else:
        image_in = image
        image_out = image.with_suffix(".png")

    print(f"    Converting image: {image}")

    success = rawimg_to_png(
        image_in,
        image_out
    )

    if success:
        print(f"    Image saved as: {image_out.with_suffix('.png')}")
        if replace:
            os.remove(image_in)
    else:
        print(f"    Could not save image.")

    if decompress:
        try:
            os.remove(path_append_extension(image, ".tmp"))
        except Exception as e:
            print(f"    Could not remove the file {image_out}: {e}")


def _entryfile_handle(file: Path) -> None:
    if file.name != ("entries.txt"):
        raise RuntimeError(f"File `{file}` is not `entries.txt`")
    else:
        file_dir = file.parent

    with open(file) as entry_file:
        file_entries = [entry.split(" ")[0]
                        for entry in entry_file.readlines()]

    file_entries = [x for x in file_entries if x.endswith(".rawimg")]
    for i, filename in enumerate(file_entries):
        print(f"Processing file {i+1} of {len(file_entries)}")
        filename = file_dir + filename
        convert_image(filename, decompress, replace)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="rawimg_to_png", description="Convert rawimg files to png.")
    # parser.add_argument(
    #     "-s",
    #     "--silent",
    #     action=argparse.BooleanOptionalAction,
    #     default=False,
    #     dest="silent",
    #     help="Silenty process files.")
    parser.add_argument(
        "-i",
        "--ignore",
        action=argparse.BooleanOptionalAction,
        default=False,
        dest="ignore",
        help="Ignore errors.")
    parser.add_argument(
        "-d",
        "--decompress",
        action=argparse.BooleanOptionalAction,
        default=False,
        dest="decompress",
        help="Decompress files before converting.")
    parser.add_argument(
        "-r",
        "--replace",
        action=argparse.BooleanOptionalAction,
        default=False,
        dest="replace",
        help="Replace the original rawimg file with the png file.")
    parser.add_argument(
        "-e",
        "--entries",
        action=argparse.BooleanOptionalAction,
        default=False,
        dest="use_entryfile",
        help="Decompress all files according to the entry.txt file.")
    parser.add_argument("image", nargs="*", help="Image(s) to convert.")
    args = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        exit()

    # silent = args.silent
    replace = args.replace
    ignore_errors = args.ignore
    decompress = args.decompress
    use_entryfile = args.use_entryfile
    images = args.image

    if use_entryfile:
        for file in images:
            _entryfile_handle(file)
    else:
        for i, image in enumerate(images):
            print(f"Converting image {i+1} of {len(images)}")
            convert_image(Path(image), decompress, replace)
