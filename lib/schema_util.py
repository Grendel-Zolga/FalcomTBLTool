import fsspec
import os

from pathlib import Path


def update_schema(game: str):
    destination = Path("schemas")
    os.makedirs(destination / "common", exist_ok=True)
    os.makedirs(destination / game, exist_ok=True)

    fs = fsspec.filesystem("github", org="Trails-Research-Group", repo="FalcomSchema")
    fs.get(fs.ls("common"), (destination / "common").as_posix())
    fs.get(fs.ls(game), (destination / game).as_posix())
