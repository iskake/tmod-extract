#!/usr/bin/env python3

import os
import sys
import argparse
import zlib
from pathlib import Path
from path_helpers import path_append_extension, dir_append_file


def _print_or_throw(message: str, e: Exception, ignore_errors: bool = False) -> None:
    if ignore_errors:
        print(message)
        print("    Ignore flag is set! Continuing...")
    else:
        raise type(e)(message)


def decompress(filename: str or Path, outname: str or Path = None, ignore_errors: bool = False) -> bool:
    """
    Function to decompress files using the DEFLATE algorithm.
    """
    filename = Path(filename)
    if outname is None:
        outname = path_append_extension(filename, ".out")
    outname = Path(outname)

    try:
        with open(filename, "rb") as comp_file:
            file_data = comp_file.read()
    except FileNotFoundError or PermissionError as e:
        _print_or_throw(f"Could not decompress the file '{filename}': an exception occurred: {e}\nAre you sure this file is compressed?", e, ignore_errors)
        return False

    # Compressed files use the DEFLATE format, so we have to set wbits like so.
    try:
        file_data_decomp = zlib.decompress(file_data, -zlib.MAX_WBITS)

        with open(outname, "wb") as decomp_file:
            decomp_file.write(file_data_decomp)
            return True
    except Exception as e:
        _print_or_throw(f"Could not decompress the file '{filename}': an exception occurred: {e}\nAre you sure this file is compressed?", e, ignore_errors)
        return False


def decomp_entries(file_dir: str | Path, file_entries: str | tuple[tuple[str, int, int]], ignore_errors: bool, replace_files: bool) -> None:
    for i, entry in enumerate(file_entries):
        print(f"Decompressing file {i+1} of {len(file_entries)}")

        if type(entry) is str:
            entry = entry.strip().split(" ")

        filename, raw_size, compressed_size = entry
        filename = dir_append_file(file_dir, filename)
        raw_size, compressed_size = int(raw_size), int(compressed_size)

        should_decompress = raw_size > compressed_size
        if should_decompress:
            print(f"    Decompressing file: {filename}")
            filename_tmp = path_append_extension(filename, ".out")
            success = decompress(filename, filename_tmp, ignore_errors)

            if success:
                if replace_files:
                    os.replace(filename_tmp, filename)
                    print(f"    Saved file as {filename}")
                else:
                    print(f"    Saved file as {filename_tmp}")
            else:
                print("    An error occurred while decompressing the file.")
        else:
            print(f"    File should not be decompressed: {filename}")


def _entryfile_handle(file: str) -> None:
    if not file.endswith("entries.txt"):
        raise RuntimeError(f"Invalid filename: expected 'entries.txt', got '{file}'")
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
        print("Using 'entries.txt' file(s)...")
        if len(files) < 1:
            raise RuntimeError("No 'entries.txt' file(s) specified.")
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
                try:
                    os.replace(filename + ext, filename)
                    print(f"    Saved file as {filename}")
                except FileNotFoundError as e:
                    message = f"Could not replace the file '{filename}': {e}"
                    if ignore_errors:
                        print(message)
                        print("    Ignore flag is set! Continuing...")
                    else:
                        raise type(e)(message)
            else:
                print(f"    Saved file as {filename}{ext}")
