from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
CONTENT = ROOT / "content" / "ja"
PACK = DATA / "packs" / "ja" / "pack.sqlite"
USERS = DATA / "users.sqlite"
