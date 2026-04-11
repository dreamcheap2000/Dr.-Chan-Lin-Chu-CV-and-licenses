"""
fetch_project_files.py
~~~~~~~~~~~~~~~~~~~~~~
Downloads the PhD project files from their public URLs and stores them
in the projects/ folder so they are preserved in the repository.

Files fetched:
  - PhD Colab notebook (.ipynb JSON) → projects/phd_colab_notebook.ipynb
  - Mathematical framework (published Google Doc HTML) → projects/mathematical_framework.html

Run this script as part of the CI pipeline (requires internet access).

Usage:
    python "CV and certificate/scripts/fetch_project_files.py"
"""
from __future__ import annotations

from pathlib import Path

try:
    import requests
except ImportError as e:
    raise SystemExit("Missing dependency: requests.  Install: pip install requests") from e

REPO_ROOT = Path(__file__).resolve().parents[2]
CV_FOLDER = REPO_ROOT / "CV and certificate"
PROJECTS_DIR = CV_FOLDER / "projects"

COLAB_FILE_ID = "18Vb686m8W-1KtSwoDlT4e3jXcTAsK24Q"
COLAB_DOWNLOAD_URL = f"https://drive.google.com/uc?export=download&id={COLAB_FILE_ID}"
COLAB_OUTPUT = PROJECTS_DIR / "phd_colab_notebook.ipynb"

GDOC_PUB_URL = (
    "https://docs.google.com/document/d/e/"
    "2PACX-1vRRRrZBt85Vmtg0t2EueoAy1NiQol5JJhMzYMfYSmrtd3-Ce0ty1oO0u1awGTHCMUTBA8BW3VGloy2U/pub"
)
GDOC_OUTPUT = PROJECTS_DIR / "mathematical_framework.html"


def fetch_and_save(url: str, dest: Path, label: str) -> bool:
    print(f"Fetching {label} …")
    try:
        r = requests.get(url, timeout=60, allow_redirects=True)
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
        print(f"  Saved {len(r.content):,} bytes → {dest.relative_to(REPO_ROOT)}")
        return True
    except Exception as exc:
        print(f"  Warning: could not fetch {label}: {exc}")
        return False


def main() -> None:
    fetch_and_save(COLAB_DOWNLOAD_URL, COLAB_OUTPUT, "PhD Colab notebook")
    fetch_and_save(GDOC_PUB_URL, GDOC_OUTPUT, "Mathematical framework (Google Doc)")


if __name__ == "__main__":
    main()
