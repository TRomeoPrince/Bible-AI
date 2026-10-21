"""Install optional openly licensed local study datasets.

Run from the repository root:
    python scripts/install_open_data.py thayer

The script intentionally installs data locally rather than committing large
third-party datasets into Bible-AI.
"""

from pathlib import Path
from urllib.request import urlopen
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
LEXICONS = ROOT / "data" / "lexicons"

THAYER_URL = (
    "https://raw.githubusercontent.com/nigelmsipa/"
    "thayers-greek-lexicon-dataset/master/data/thayer_lexicon.jsonl"
)


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}")
    with urlopen(url, timeout=120) as response, destination.open("wb") as target:
        shutil.copyfileobj(response, target)
    print(f"Installed: {destination}")


def install_thayer() -> None:
    download(THAYER_URL, LEXICONS / "thayer_lexicon.jsonl")
    print("License: original Thayer (1889) Public Domain; digitized dataset CC0 1.0.")


def main() -> None:
    choice = sys.argv[1].lower() if len(sys.argv) > 1 else "thayer"
    if choice == "thayer":
        install_thayer()
    else:
        raise SystemExit("Available dataset: thayer")


if __name__ == "__main__":
    main()
