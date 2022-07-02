#!/usr/bin/env python3

import sys
import os
import argparse
from PIL import Image
from tmod_decompress import decompress, decomp_entries
from pathlib import Path
from path_helpers import path_append_extension, dir_append_file

RAWIMG_SUPPORTED_VERSION = 1


def rawimg_to_png(filename: str | Path, outname: str | Path = None) -> bool:
    filename = Path(filename)
    outname = Path(outname)

    try:
        with open(filename, 'rb') as f:
            file_version = int.from_bytes(f.read(4), 'little')
            if (file_version != RAWIMG_SUPPORTED_VERSION):
                raise RuntimeError(f"""Invalid rawimg version: {file_version} (supported version: {RAWIMG_SUPPORTED_VERSION})
Did you forget to decompress the image? (use `decompress.py` or the `-d` command line argument)""")
            file_w = int.from_bytes(f.read(4), 'little')
            file_h = int.from_bytes(f.read(4), 'little')
            file = f.read()
    except FileNotFoundError as e:
        if ignore_errors:
            print(f"An exception occurred: {e}")
            print("    Ignore flag is set! Continuing...")
            return False
        else:
            raise e


    try:
        image = Image.frombytes('RGBA', (file_w, file_h), file)
        if outname is None:
            outname = filename.with_suffix("")
        image.save(outname.with_suffix(".png"), "PNG")

        return True
    except Exception as e:
        message = f"""An exception occurred: {e}
Did you forget to decompress the image? (use `decompress.py` or the `-d` command line argument)"""
        if ignore_errors:
            print(message)
            print("    Ignore flag is set! Continuing...")
        else:
            raise type(e)(message)

        return False


def convert_image(image: Path, decompress_img: bool = False, ignore_errors: bool = False, replace: bool = False) -> None:
    if decompress_img:
        image_in = path_append_extension(image, ".tmp")
        image_out = image.with_suffix(".png")
        print(f"    Decompressing image...")
        decompress(image, image_in, ignore_errors)
    else:
        image_in = image
        image_out = image.with_suffix(".png")

    print(f"    Converting image: {image}")

    success = rawimg_to_png(image_in, image_out)

    if success:
        print(f"    Image saved as: {image_out.with_suffix('.png')}")
        if replace:
            os.remove(image_in)
    else:
        print(f"    Could not save image.")

    if decompress_img:
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
        file_entries = [entry.split(" ")
                        for entry in entry_file.readlines()]

    file_entries = [x for x in file_entries if x[0].endswith(".rawimg")]

    if (decompress_imgs):
        decomp_entries(file_dir, file_entries, ignore_errors, True)

    for i, entry in enumerate(file_entries):
        print(f"Processing file {i+1} of {len(file_entries)}")
        filename = dir_append_file(file_dir, entry[0])
        convert_image(filename, False, ignore_errors, replace)  # False, since we have (presumably) already decompressed the files.


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
        help="Convert all files according to the entry.txt file.\n"
             "(Note: using `-d` with this will replace the compressed files.)")
    parser.add_argument("image", nargs="*", help="Image(s) to convert.")
    args = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        exit()

    # silent = args.silent
    replace = args.replace
    ignore_errors = args.ignore
    decompress_imgs = args.decompress
    use_entryfile = args.use_entryfile
    images = args.image

    if use_entryfile:
        for file in images:
            _entryfile_handle(Path(file))
    else:
        for i, image in enumerate(images):
            print(f"Converting image {i+1} of {len(images)}")
            convert_image(Path(image), decompress_imgs, ignore_errors, replace)
