from __future__ import annotations

import os
import re
from pathlib import Path

try:
    import yaml  # pyyaml
except Exception as e:
    raise SystemExit(
        "Missing dependency: pyyaml. Add it by creating requirements, or vendor a tiny YAML reader.\n"
        "Fast fix: create scripts/requirements.txt with 'pyyaml' and install in workflow."
    ) from e


REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"
DICT_PATH = REPO_ROOT / ".github" / "translations.yml"

START_MARK = "<!-- AUTO-GENERATED:START -->"
END_MARK = "<!-- AUTO-GENERATED:END -->"

EXT_TO_STRIP = {".jpg", ".jpeg", ".png", ".pdf"}  # display: no extension anyway


def strip_ext(filename: str) -> str:
    p = Path(filename)
    if p.suffix.lower() in EXT_TO_STRIP:
        return p.stem
    # if unknown extension, still strip for display consistency
    return p.stem


def humanize_fallback(key: str) -> str:
    # Replace underscores with spaces; keep common acronyms readable.
    s = key.replace("_", " ").strip()
    # minor cleanup
    s = re.sub(r"\s+", " ", s)
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
    # expect 01_... to 09_...
    dirs = []
    for p in sorted(REPO_ROOT.iterdir()):
        if p.is_dir() and re.match(r"^(0[1-9])_", p.name):
            dirs.append(p)
    return dirs


def build_markdown_section(data: dict) -> tuple[str, list[str]]:
    categories = data.get("categories", {})
    translations = data.get("files", {})

    # A fixed color palette (badge colors)
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

    rows = []
    cat_dirs = list_category_dirs()

    for idx, d in enumerate(cat_dirs):
        cat_key = d.name
        cat_title = categories.get(cat_key, cat_key)  # chinese title preferred

        # Collect file names (non-recursive for now)
        files = [p for p in sorted(d.iterdir()) if p.is_file()]
        items_zh = []
        for fp in files:
            base = strip_ext(fp.name)
            zh = translations.get(base)
            if not zh:
                missing.append(base)
                zh = humanize_fallback(base)
            items_zh.append(zh)

        color = colors[idx % len(colors)]
        # Use shields badge (stable on GitHub)
        badge_label = "分類"
        badge_msg = cat_title
        # shields expects URL-escaped pieces; keep it simple by replacing spaces with %20
        def esc(s: str) -> str:
            return (
                s.replace("-", "--")
                 .replace("_", "__")
                 .replace(" ", "%20")
                 .replace("/", "%2F")
                 .replace("（", "%EF%BC%88")
                 .replace("）", "%EF%BC%89")
            )

        badge = f"![{cat_title}](https://img.shields.io/badge/{esc(badge_label)}-{esc(badge_msg)}-{color})"
        content = "；".join(items_zh) if items_zh else "（無）"
        rows.append(f"| {badge} | {content} |")

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
        middle, after = rest.split(END_MARK, 1)
        return before + START_MARK + "\n\n" + new_section + "\n" + END_MARK + after

    # If markers not found, append them at top
    insert = f"{START_MARK}\n\n{new_section}\n{END_MARK}\n\n"
    return insert + readme_text


def main() -> None:
    data = load_dict()

    # Ensure base structure exists
    data.setdefault("categories", {})
    data.setdefault("files", {})

    # Auto-fill category titles if missing (you can edit later)
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

    new_section, missing = build_markdown_section(data)

    if not README_PATH.exists():
        README_PATH.write_text("# Dr. Chan Lin Chu - CV and licenses\n\n", encoding="utf-8")

    old = README_PATH.read_text(encoding="utf-8")
    updated = upsert_readme_section(old, new_section)
    README_PATH.write_text(updated, encoding="utf-8")

    # Save dictionary (keeps categories normalized)
    save_dict(data)

    # Print missing translations in CI logs
    if missing:
        unique_missing = sorted(set(missing))
        print("Missing translations (add to .github/translations.yml under files:):")
        for k in unique_missing:
            print(f" - {k}")
        # Do not fail; just inform.
    else:
        print("All filenames translated.")


if __name__ == "__main__":
    main()
