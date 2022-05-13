import sys
from pathlib import Path

from .runner import run

if __name__ == "__main__":
    if not run(Path(sys.argv[1])):
        sys.exit(1)
