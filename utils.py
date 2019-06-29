
from pathlib import Path

def make_path_absolute(relative_path: str) -> Path:
    return get_project_dir() / relative_path

def get_project_dir() -> Path:
    p = Path(__file__) 
    return p.parent.resolve()


def create_dir(dirname):
    p = get_project_dir() / dirname
    if not (p.exists() and p.is_dir()):
        p.mkdir(parents=True)
    else:
        print("Folder already exists")
    return p