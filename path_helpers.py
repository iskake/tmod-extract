from pathlib import Path

def path_append_extension(path: Path, extension: str) -> Path:
    """
    Append an extension to the specified path.
    For example: 
    ``Path(file.txt)``
    """
    return path.parent / f"{path.name}.{extension}"