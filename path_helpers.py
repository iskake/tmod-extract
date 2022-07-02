from pathlib import Path


def path_append_extension(path: str | Path, extension: str) -> Path:
    """
    Append an extension to the specified path.
    For example: 
    ``Path("file.txt"), ".tmp"`` returns ``Path("file.txt.tmp")``
    """
    return Path(path + extension) if type(path) is str else path.parent / f"{path.name}{extension}"


def dir_append_file(directory: str | Path, file: str | Path) -> Path:
    """
    Append an extension to the specified path.
    For example: 
    ``Path("file.txt"), ".tmp"`` returns ``Path("file.txt.tmp")``
    """
    return Path(directory) / Path(file)