import json
from pathlib import Path
from typing import Iterator, Any

def load_json_stream(path: Path) -> Iterator[Any]:
    """
    Lazily yield each top-level object from a large JSON array file,
    so you don’t have to load the entire file into memory.
    """
    with path.open("r", encoding="utf-8") as f:
        # Assumes the file is: [ obj1, obj2, ..., objN ]
        # Skip initial bracket
        f.readline()
        for line in f:
            line = line.rstrip().rstrip(",")  # trim trailing commas & whitespace
            if line in ("]", ""):
                break
            yield json.loads(line)
