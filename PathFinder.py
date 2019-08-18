from pathlib import Path

def check_file_exists(path: str):
    p = Path(path)
    return p.exists()