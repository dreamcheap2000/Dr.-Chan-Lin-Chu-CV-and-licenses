"""normalize_new_files.py – Move & rename newly added certificate files.

When a file is added to a ``02_*`` folder *without* a ``NN_`` numeric sort
prefix it is treated as a freshly uploaded file that still needs to be
normalised.  This script:

1. Finds every such file inside all folders matching
   :data:`SOURCE_FOLDER_PATTERN` (default: ``^02_``).
2. Moves the file to :data:`DEST_FOLDER_NAME` (default: auto-detected first
   ``03_*`` folder) using ``git mv`` so Git history is preserved.
3. Prepends the next available two-digit prefix (``NN_``) to the filename so
   it slots into the sort order of the destination folder without collisions.
4. Adds the new translation key to the ``pending:`` section of
   ``.github/translations.yml`` so the README generator can produce a
   placeholder and the owner can fill in the Chinese label later.

Configuration
-------------
Edit the two constants near the top of this file:

* :data:`SOURCE_FOLDER_PATTERN` – regex applied to **folder names** inside
  ``CV and certificate/``.  Any folder whose name matches becomes a source.
  Default: ``^02_`` (all ``02_*`` folders).

* :data:`DEST_FOLDER_NAME` – exact **folder name** (not full path) inside
  ``CV and certificate/`` to move files into.  Set to ``None`` to
  auto-detect the first ``03_*`` folder alphabetically.

Usage
-----
::

    python "CV and certificate/scripts/normalize_new_files.py"

Called automatically by the GitHub Actions workflow
``.github/workflows/update-readme.yml`` *before* README generation so that
the freshly normalised files are visible to ``generate_readme_section.py``.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit(
        "Missing dependency: pyyaml.  Install with: pip install pyyaml"
    )

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
CV_FOLDER = REPO_ROOT / "CV and certificate"
DICT_PATH = REPO_ROOT / ".github" / "translations.yml"

# ---------------------------------------------------------------------------
# Configuration – edit these two values to customise the behaviour
# ---------------------------------------------------------------------------

# Regex matched against *folder* names under CV and certificate/.
# Files without a NN_ prefix inside any matching folder will be normalised.
SOURCE_FOLDER_PATTERN: str = r"^02_"

# Exact folder name (not full path) of the move destination.
# Set to None to auto-detect the first 03_* folder found.
DEST_FOLDER_NAME: str | None = None

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_NUMERIC_PREFIX_RE = re.compile(r"^\d{2}_")


def _get_dest_folder() -> Path:
    """Return the Path of the destination folder, creating it if needed."""
    if DEST_FOLDER_NAME:
        dest = CV_FOLDER / DEST_FOLDER_NAME
        if not dest.exists():
            dest.mkdir(parents=True)
            print(f"Created destination folder: {dest}")
        return dest

    # Auto-detect the first 03_* folder alphabetically
    for p in sorted(CV_FOLDER.iterdir()):
        if p.is_dir() and re.match(r"^03_", p.name):
            return p

    raise SystemExit(
        "No 03_* destination folder found under 'CV and certificate/'.\n"
        "Set DEST_FOLDER_NAME in normalize_new_files.py to an explicit folder."
    )


def _next_prefix(dest: Path) -> str:
    """Return the next available two-digit ``NN_`` prefix for *dest*.

    Reads the *current* filesystem state of *dest* so that each successive
    call within a single run yields a strictly incremented number.
    """
    taken = [
        int(_NUMERIC_PREFIX_RE.match(p.name).group(0)[:2])
        for p in dest.iterdir()
        if p.is_file() and _NUMERIC_PREFIX_RE.match(p.name)
    ]
    return f"{(max(taken, default=0) + 1):02d}_"


def _git_mv(src: Path, dst: Path) -> None:
    """Rename/move *src* to *dst* via ``git mv``."""
    result = subprocess.run(
        ["git", "mv", "--", str(src), str(dst)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"git mv failed ({result.returncode}):\n{result.stderr.strip()}"
        )
    print(f"  Moved: '{src.relative_to(CV_FOLDER)}'"
          f"  →  '{dst.relative_to(CV_FOLDER)}'")


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save_yaml(path: Path, data: dict) -> None:
    """Write *data* to *path*, always placing ``pending`` first."""
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered: dict = {}
    if "pending" in data:
        ordered["pending"] = data["pending"]
    for k, v in data.items():
        if k != "pending":
            ordered[k] = v
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(ordered, f, allow_unicode=True, sort_keys=False)


def _translation_key(filename: str) -> str:
    """Derive the translations.yml key from a normalised filename.

    Strips the leading ``NN_`` prefix and file extension, matching the logic
    in ``generate_readme_section.py``.
    """
    stem = Path(filename).stem                         # strip extension
    return re.sub(r"^\d{2}_", "", stem)                # strip NN_ prefix


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    source_dirs = [
        p for p in sorted(CV_FOLDER.iterdir())
        if p.is_dir() and re.match(SOURCE_FOLDER_PATTERN, p.name)
    ]

    if not source_dirs:
        print(f"No source folders matching '{SOURCE_FOLDER_PATTERN}' found – nothing to do.")
        return

    dest = _get_dest_folder()
    translations = _load_yaml(DICT_PATH)
    translations.setdefault("pending", {})

    moved_count = 0
    for src_dir in source_dirs:
        unnumbered = sorted(
            p for p in src_dir.iterdir()
            if p.is_file() and not _NUMERIC_PREFIX_RE.match(p.name)
        )
        if not unnumbered:
            continue

        print(f"\n[{src_dir.name}] {len(unnumbered)} unnumbered file(s) to normalise:")
        for fp in unnumbered:
            prefix = _next_prefix(dest)
            new_name = prefix + fp.name
            dst_path = dest / new_name

            # Perform the git move
            _git_mv(fp, dst_path)

            # Register a placeholder translation so README doesn't show raw key
            key = _translation_key(new_name)
            if key not in translations["pending"] and key not in translations.get("files", {}):
                translations["pending"][key] = None
                print(f"  Registered pending translation key: '{key}'")

            moved_count += 1

    if moved_count == 0:
        print("No unnumbered files found – nothing to normalise.")
        return

    _save_yaml(DICT_PATH, translations)
    print(
        f"\nNormalised {moved_count} file(s) into '{dest.name}'.\n"
        "Run generate_readme_section.py to rebuild the README."
    )


if __name__ == "__main__":
    main()
