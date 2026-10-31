from pathlib import Path

from store.pack import sample_pack
from store.paths import PACK

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "pack.sqlite"
EVERY = 125


if __name__ == "__main__":
    sample_pack(PACK, FIXTURE, EVERY)
    print(f"written {FIXTURE}")
