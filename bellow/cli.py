import sys
import tomllib
from pathlib import Path

from .checker import check_source


def main(argv):
    if len(argv) != 3 or argv[1] != "check":
        print("USAGE: bellow check FILE", file=sys.stderr)
        return 2

    path = Path(argv[2])
    manifest = path.with_name(path.name + ".bellow.toml")
    if not manifest.exists():
        print(f"{path}: NO MANIFEST. I'M NOT GUESSING WHAT THIS IS, RUDE.", file=sys.stderr)
        return 1

    with manifest.open("rb") as fh:
        ftype = tomllib.load(fh).get("type")
    if ftype != "bellow":
        print(f"{path}: TYPE IS {ftype!r}, NOT BELLOW. SKIPPING.")
        return 0

    problems = check_source(path.read_text(encoding="utf-8"))
    for p in problems:
        where = f"{path}:{p.line}" if p.line else f"{path}"
        print(f"{where}: {p.message}", file=sys.stderr)
    if problems:
        return 1
    print(f"{path}: PASSED. THANK YOU.")
    return 0
