# tools/fs_tools.py
import os
from pathlib import Path
from typing import Union

def ensure_workspace(path: Union[str, Path]):
    Path(path).mkdir(parents=True, exist_ok=True)

def write_file(path: Union[str, Path], content: str, mode='w'):
    ensure_workspace(Path(path).parent)
    with open(path, mode, encoding='utf-8') as f:
        f.write(content)
    return path

def read_file(path: Union[str, Path]) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()
