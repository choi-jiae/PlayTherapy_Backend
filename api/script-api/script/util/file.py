import glob
import os
import re
from pathlib import Path


def extract_number_from_file(file_name: str):
    match = re.search(r'(\d+)\.mp3$', file_name)
    return int(match.group(1)) if match else 0


def get_files(source_path: Path, ext: str):
    if not os.path.exists(source_path):
        raise ValueError(f"The provided path does not exist: {source_path}")
    if not os.path.isdir(source_path):
        raise ValueError(f"The provided path is not a directory: {source_path}")

    files = glob.glob(os.path.join(source_path, f'*.{ext}'))

    files = sorted(files, key=extract_number_from_file)

    return [Path(raw_path) for raw_path in files]
