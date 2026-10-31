from pathlib import Path


def rows(path: Path) -> list[list[str]]:
    """Tab-separated rows of an authored content file, without comments and blank lines."""
    lines = path.read_text().splitlines()
    return [line.split("\t") for line in lines if line.strip() and not line.startswith("#")]
