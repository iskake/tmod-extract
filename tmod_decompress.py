#!/usr/bin/env python3

import os
import sys
import argparse
import zlib
from pathlib import Path
from path_helpers import path_append_extension


def decompress(filename: str or Path, outname: str or Path = None, ignore_errors: bool = False) -> None:
    """
    Function to decompress files using the DEFLATE algorithm.
    """
    if outname is None:
        outname = filename + ".out" if type(outname) is str else path_append_extension(filename, ".out")

    with open(filename, "rb") as comp_file:
        file_data = comp_file.read()

    # Compressed files use the DEFLATE format, so we have to set wbits like so.
    try:
        file_data_decomp = zlib.decompress(file_data, -zlib.MAX_WBITS)

        with open(outname, "wb") as decomp_file:
            decomp_file.write(file_data_decomp)
    except Exception as e:
        if ignore_errors:
            print("An exception occurred: ", e)
            print("Ignoring...")
        else:
            raise e


def decomp_entries(file_dir: Path, file_entries: (str, int, int), ignore_errors: bool, replace_files: bool) -> None:
    for i, entry in enumerate(file_entries):
        print(f"Decompressing file {i+1} of {len(file_entries)}")

        if type(entry) is str:
            entry = entry.strip().split(" ")

        filename, raw_size, compressed_size = entry
        filename = file_dir + filename if type(file_dir) is str else file_dir / filename
        raw_size, compressed_size = int(raw_size), int(compressed_size)

        should_decompress = True if raw_size > compressed_size else False
        if should_decompress:
            print(f"    Decompressing file: {filename}")
            filename_tmp = filename + ".out" if type(filename) is str else path_append_extension(filename, ".out")
            decompress(filename, filename_tmp, ignore_errors)
            if replace_files:
                os.replace(filename_tmp, filename)
                print(f"    Saved file as {filename}")
            else:
                print(f"    Saved file as {filename}{ext}")
        else:
            print(f"    File should not be decompressed: {filename}")


def _entryfile_handle(file: str) -> None:
    if not file.endswith("entries.txt"):
        raise RuntimeError(f"File `{file}` is not `entries.txt`")
    else:
        file_dir = file.strip("entries.txt")

    with open(file) as entry_file:
        file_entries = entry_file.readlines()

    decomp_entries(file_dir, file_entries, ignore_errors, replace_files)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="tmod_decompress", description="Decompress compressed files from extracted `tmod` files.")
    parser.add_argument(
        "-i",
        "--ignore",
        action=argparse.BooleanOptionalAction,
        default=False,
        dest="ignore",
        help="Ignore errors.")
    parser.add_argument(
        "-r",
        "--replace",
        action=argparse.BooleanOptionalAction,
        default=False,
        dest="replace",
        help="Replace the original file after decompressing.")
    parser.add_argument(
        "-e",
        "--entries",
        action=argparse.BooleanOptionalAction,
        default=False,
        dest="use_entryfile",
        help="Decompress all files according to the entry.txt file.")
    parser.add_argument("file", nargs="*", help="File(s) to decompress.")
    args = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        exit()

    ignore_errors = args.ignore
    replace_files = args.replace
    use_entryfile = args.use_entryfile
    files = args.file

    if (use_entryfile):
        print("Using entries.txt file(s)...")
        for file in files:
            _entryfile_handle(file)
    else:
        for i, file in enumerate(files):
            print(f"Decompressing file {i+1} of {len(files)}")
            print(f"    Decompressing file: {file}")
            filename = file
            ext = ".out"
            decompress(filename, filename + ext, ignore_errors)
            if replace_files:
                os.replace(filename + ext, filename)
                print(f"    Saved file as {filename}")
            else:
                print(f"    Saved file as {filename}{ext}")
