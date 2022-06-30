#!/usr/bin/env python3

import sys
import os
from pathlib import Path
import argparse
from io import BufferedReader
from collections import namedtuple

from tmod_decompress import decompress, decomp_entries
from rawimg_to_png import convert_image

# Adapted from: https://github.com/dotnet/runtime/blob/cbed235943395746786e4854f558a50d3b29033b/src/libraries/System.Private.CoreLib/src/System/IO/BinaryReader.cs#L562
# Note: 'The .NET Foundation licenses this file to you under the MIT license.'
def _read_7bit_int(file: BufferedReader) -> int:
    result = 0
    curr_byte: int
    MAX_BYTES_WITHOUT_OVERFLOW = 9  # This will probably never happen in the context of `.tmod` files.

    for i in range(MAX_BYTES_WITHOUT_OVERFLOW):
        shift = i * 7

        curr_byte = int.from_bytes(file.read(1), "little")
        result |= (curr_byte & 0x7f) << shift

        if curr_byte <= 0x7f:
            return result

    curr_byte = int.from_bytes(file.read(1), "little")
    if (curr_byte > 1):
        raise Exception("Invalid 7bit int format.")

    result |= curr_byte << (MAX_BYTES_WITHOUT_OVERFLOW * 7)
    return result


def _read_str(file: BufferedReader) -> str:
    str_len = _read_7bit_int(file)
    ret_str = file.read(str_len).decode()
    return ret_str


def _read_int32(file: BufferedReader) -> int:
    return int.from_bytes(file.read(4), "little", signed=True)


def _read_uint32(file: BufferedReader) -> int:
    return int.from_bytes(file.read(4), "little", signed=False)


def extract(filename: str, write_entries: bool = True) -> (str, tuple):
    with open(filename, "rb") as file:
        header = file.read(4)
        if header != b"TMOD":
            raise RuntimeError(
                f"Invalid header: '{header.decode()}', expected: 'TMOD'.")

        version = _read_str(file)
        hash = file.read(20)
        sig = file.read(256)
        data_len = _read_uint32(file)
        mod_name = _read_str(file)
        mod_ver = _read_str(file)

        file_count = _read_int32(file)
        entry = namedtuple("entry", "filename raw_size comp_size")
        file_entries = [entry(_read_str(file), _read_int32(file), _read_int32(file)) for _ in range(file_count)]

        file_data = [file.read(entry.comp_size) for entry in file_entries]

    print(f"Header: {header.decode()} (valid)") # Must be valid, else RuntimeError (what if `--skip` option?)
    print(f"Hash: {int.from_bytes(hash, 'big'):040x}")
    # print(f"Sig: {int.from_bytes(sig, 'big'):0512x}")
    print(f"File data length: {data_len}")
    print(f"Mod name: {mod_name}")
    print(f"Mod version: {mod_ver}")
    print(f"File count: {file_count}")
    print(f"File entries:")
    print(f"    File n: Filename, Raw size (bytes), Compressed size (bytes)")
    for i, entry in enumerate(file_entries):
        print(f"    File {i}: {entry.filename}, {entry.raw_size}, {entry.comp_size}")

    if not os.path.exists(f"out/{mod_name}"):
        os.makedirs(f"out/{mod_name}")

    print("\nExtracting files...")
    for i in range(len(file_entries)):
        fe = file_entries[i]
        fd = file_data[i]
        print(f"    Writing file {i + 1}: {fe.filename} (size: {fe.comp_size}b)...")

        mod_dir = Path(f"out/{mod_name}/")
        full_path = mod_dir / fe.filename
        if not full_path.parent.exists():
            os.makedirs(full_path.parent)

        with open(full_path, "wb") as f:
            f.write(fd)

    return (mod_name, file_entries)


def write_entryfile(mod_path: str, entries: tuple) -> None:
    with open(mod_path, "w") as entry_file:
        for entry in entries:
            entry_file.write(f"{entry.filename} {entry.raw_size} {entry.comp_size}\n")
    print(f"Wrote entries.txt to {str(mod_path)} (use with `tmod_decompress.py` and `rawimg_to_png.py`.)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="tmod_extract", description="Extract the contents of `tmod` files.")
    parser.add_argument(
        "-d",
        "--decompress",
        action=argparse.BooleanOptionalAction,
        default=False,
        dest="decompress_files",
        help="Decompress files after extracting.")
    parser.add_argument(
        "-i",
        "--convert-images",
        action=argparse.BooleanOptionalAction,
        default=False,
        dest="image_convert",
        help="Convert images after extracting and decompressing.")
    parser.add_argument(
        "-a",
        "--auto",
        action=argparse.BooleanOptionalAction,
        default=False,
        dest="auto",
        help="Automatically extract, decompress, and convert files, then remove the old files. Equivalent to as using `-d -i -r`")
    parser.add_argument(
        "-r",
        "--replace",
        action=argparse.BooleanOptionalAction,
        default=False,
        dest="replace",
        help="Replace the original files after decompressing/converting images.")
    parser.add_argument("file", nargs="*",
                        help="File(s) to extract the contents of.")
    args = parser.parse_args()

    auto = args.auto
    decompress_files = args.decompress_files or auto
    image_convert = args.image_convert or auto
    replace = args.replace
    files = args.file

    if len(sys.argv) < 2:
        parser.print_help()
        exit()

    for i, file in enumerate(files):
        # Don't bother printing '1 of 1'
        if (len(files) != 1):
            print(f"Extracting file {i+1} of {len(files)}")
            print(f"    Extracting file: {file}")
        else:
            print(f"Extracting file: {file}")
        mod_name, entries = extract(file)
        mod_path = Path(f"out/{mod_name}/")
        print(f"Finished extracting files from {file}.")
        print(#"Note: auto flag (`-a`) not set!"
              "Since most of the extracted files are probably compressed,"
              "use `tmod_decompress.py` to decompress them.")

    if decompress_files:
        decomp_entries(mod_path, entries, False, True)
    else:
        if not image_convert:
            write_entryfile(mod_path, entries)
    if image_convert:
        if not decompress_files:
            print("Images have not been decompressed, so they can not be converted.")
            print("Use `tmod_decompress.py` to decompress the files.")
            write_entryfile(mod_path, entries)
        else:
            entries = [x[0] for x in entries if x[0].endswith(".rawimg")]
            for i, filename in enumerate(entries):
                print(f"Processing image {i+1} of {len(entries)}")
                filename = mod_path / filename
                convert_image(filename, False, replace)
