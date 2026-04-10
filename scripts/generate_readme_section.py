from __future__ import annotations

import re
from pathlib import Path

try:
    import yaml  # pyyaml
except ImportError as e:
    raise SystemExit(
        "Missing dependency: pyyaml. "
        "Run: pip install -r scripts/requirements.txt"
    ) from e


REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"
DICT_PATH = REPO_ROOT / ".github" / "translations.yml"

START_MARK = "<!-- AUTO-GENERATED:START -->"
END_MARK = "<!-- AUTO-GENERATED:END -->"


def strip_ext(filename: str) -> str:
    return Path(filename).stem


def humanize_fallback(key: str) -> str:
    s = re.sub(r"\s+", " ", key.replace("_", " ").strip())
    return f"{s}（未翻譯）"


def load_dict() -> dict:
    if not DICT_PATH.exists():
        return {}
    with DICT_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_dict(data: dict) -> None:
    DICT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DICT_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def list_category_dirs() -> list[Path]:
    dirs = []
    for p in sorted(REPO_ROOT.iterdir()):
        if p.is_dir() and re.match(r"^0[1-9]_", p.name):
            dirs.append(p)
    return dirs


def parse_readme_names(readme_text: str) -> dict[str, list[str]]:
    """Parse README.md outside auto-generated markers to extract per-category
    Traditional Chinese item names in their listed order.

    Returns {folder_name: [zh_name, ...]} where each zh_name corresponds
    positionally to the sorted files in that folder.
    """
    # Strip auto-generated block so we only read manually maintained content
    if START_MARK in readme_text and END_MARK in readme_text:
        before, rest = readme_text.split(START_MARK, 1)
        _, after = rest.split(END_MARK, 1)
        outside = before + after
    else:
        outside = readme_text

    result: dict[str, list[str]] = {}
    current_folder: str | None = None
    current_items: list[str] = []

    for line in outside.splitlines():
        if re.match(r"^## ", line):
            # Flush previous section
            if current_folder is not None:
                result[current_folder] = current_items
            # Detect folder name inside full-width parentheses e.g. （0N_FolderName）
            m = re.search(r"（(0[1-9]_\w+)）", line)
            if m:
                current_folder = m.group(1)
                current_items = []
            else:
                current_folder = None
                current_items = []
        elif current_folder is not None and line.startswith("- "):
            item = line[2:].strip()
            if item:
                current_items.append(item)

    # Flush last section
    if current_folder is not None:
        result[current_folder] = current_items

    return result


def build_markdown_section(
    data: dict, readme_names: dict[str, list[str]]
) -> tuple[str, list[str]]:
    categories = data.get("categories", {})
    translations = data.get("files", {})

    # Fixed color palette (one per category, cycling if needed)
    colors = [
        "1f77b4",  # blue
        "ff7f0e",  # orange
        "2ca02c",  # green
        "d62728",  # red
        "9467bd",  # purple
        "8c564b",  # brown
        "e377c2",  # pink
        "7f7f7f",  # gray
        "17becf",  # cyan
    ]

    missing: list[str] = []
    rows: list[str] = []
    cat_dirs = list_category_dirs()

    for idx, d in enumerate(cat_dirs):
        cat_key = d.name
        cat_title = categories.get(cat_key, cat_key)

        files = [p for p in sorted(d.iterdir()) if p.is_file()]
        readme_items = readme_names.get(cat_key, [])

        items_zh: list[str] = []
        for pos, fp in enumerate(files):
            base = strip_ext(fp.name)
            # 1. README-derived name (positional match, authoritative source)
            zh = readme_items[pos] if pos < len(readme_items) else None
            # 2. Fall back to translations.yml
            if not zh:
                zh = translations.get(base)
            # 3. Fall back to clearly-marked auto-humanize
            if not zh:
                missing.append(base)
                zh = humanize_fallback(base)
            items_zh.append(zh)

        color = colors[idx % len(colors)]

        # Left column: bold category title (no badge – more readable)
        cat_cell = f"**{cat_title}**"

        # Right column: content colored by category using inline HTML
        content_raw = "；".join(items_zh) if items_zh else "（無）"
        content_cell = f'<span style="color:#{color}">{content_raw}</span>'

        rows.append(f"| {cat_cell} | {content_cell} |")

    section = "\n".join(
        [
            "## 專業證照與訓練（重點一覽）",
            "",
            "| 分類 | 內容（重點） |",
            "|---|---|",
            *rows,
            "",
        ]
    )
    return section, missing


def upsert_readme_section(readme_text: str, new_section: str) -> str:
    if START_MARK in readme_text and END_MARK in readme_text:
        before, rest = readme_text.split(START_MARK, 1)
        _middle, after = rest.split(END_MARK, 1)
        return before + START_MARK + "\n\n" + new_section + "\n" + END_MARK + after

    # Markers not found: prepend them at the top
    insert = f"{START_MARK}\n\n{new_section}\n{END_MARK}\n\n"
    return insert + readme_text


def main() -> None:
    data = load_dict()
    data.setdefault("categories", {})
    data.setdefault("files", {})

    # Auto-fill category titles if missing (can be edited in translations.yml)
    default_categories_zh = {
        "01_Core_Licensure_and_Specialty": "核心執照與專科資格",
        "02_Neuromodulation_TMS_VNS_tPBM": "神經調控",
        "03_Neurovascular_Endovascular": "腦血管與介入",
        "04_Ultrasound_Multisystem": "超音波（多系統）",
        "05_Acute_Care_Emergency": "急性照護",
        "06_Home_Care_LongTermCare_Community": "居家照護／長照／社區／慢性病防治",
        "07_Regulatory": "法規與管制",
        "08_Advanced_Therapies_Cell_Therapy": "進階治療",
        "09_Education_and_Service": "學歷與服務",
    }
    for k, v in default_categories_zh.items():
        data["categories"].setdefault(k, v)

    if not README_PATH.exists():
        README_PATH.write_text(
            "# Dr. Chan Lin Chu - CV and licenses\n\n", encoding="utf-8"
        )

    readme_text = README_PATH.read_text(encoding="utf-8")

    # Parse README's manually-maintained sections for authoritative Chinese names
    readme_names = parse_readme_names(readme_text)

    new_section, missing = build_markdown_section(data, readme_names)

    updated = upsert_readme_section(readme_text, new_section)
    README_PATH.write_text(updated, encoding="utf-8")

    # Keep translations.yml normalized
    save_dict(data)

    if missing:
        unique_missing = sorted(set(missing))
        print(
            "Missing translations (add to .github/translations.yml under files:):"
        )
        for k in unique_missing:
            print(f"  - {k}")
    else:
        print("All filenames translated.")


if __name__ == "__main__":
    main()
