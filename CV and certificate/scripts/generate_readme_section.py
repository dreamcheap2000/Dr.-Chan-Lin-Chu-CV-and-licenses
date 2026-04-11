from __future__ import annotations

import re
from pathlib import Path

try:
    import yaml  # pyyaml
except Exception as e:
    raise SystemExit(
        "Missing dependency: pyyaml. Install: pip install pyyaml"
    ) from e


REPO_ROOT = Path(__file__).resolve().parents[2]
CV_FOLDER = REPO_ROOT / "CV and certificate"
README_PATH = REPO_ROOT / "README.md"
DICT_PATH = REPO_ROOT / ".github" / "translations.yml"

START_MARK = "<!-- AUTO-GENERATED:START -->"
END_MARK = "<!-- AUTO-GENERATED:END -->"

EXT_TO_STRIP = {".jpg", ".jpeg", ".png", ".pdf"}

# Emoji color circles matching the original badge color palette (01–09)
CAT_EMOJIS = ["🔵", "🟠", "🟢", "🔴", "🟣", "🟤", "🩷", "⚫", "🔷"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def strip_ext(filename: str) -> str:
    p = Path(filename)
    return p.stem


def strip_numeric_prefix(stem: str) -> str:
    """Remove a leading NN_ numeric sort prefix (e.g. '01_') from a stem."""
    return re.sub(r"^\d{2}_", "", stem)


def humanize_fallback(key: str) -> str:
    s = key.replace("_", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return f"{s}（未翻譯）"


def load_yaml(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_dict() -> dict:
    data = load_yaml(DICT_PATH)
    return data if isinstance(data, dict) else {}


def save_dict(data: dict) -> None:
    DICT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Always write pending first so untranslated keys appear at the top of the file
    ordered: dict = {}
    if "pending" in data:
        ordered["pending"] = data["pending"]
    for k, v in data.items():
        if k != "pending":
            ordered[k] = v
    with DICT_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(ordered, f, allow_unicode=True, sort_keys=False)


def list_certificate_dirs() -> list[Path]:
    """Return certificate category dirs matching 01_… to 09_…"""
    dirs = []
    for p in sorted(CV_FOLDER.iterdir()):
        if p.is_dir() and re.match(r"^0[1-9]_", p.name):
            dirs.append(p)
    return dirs


def split_bilingual(title: str) -> tuple[str, str]:
    """Split 'Chinese / English' into (zh, en) on the first ASCII slash.
    Handles both '中文 / English' and '中文/ English' spacing variants.
    Returns (title, '') if no ASCII slash separator found.
    """
    m = re.search(r'\s*/\s*', title)
    if m:
        return title[:m.start()].strip(), title[m.end():].strip()
    return title.strip(), ""


def find_category_title(categories: dict, dir_name: str) -> str:
    """Map a directory name to the bilingual title in translations.yml.

    Prefers exact match first (fast, no false positives).  If the exact key is
    not found, falls back to a suffix match by stripping the leading two-digit
    numeric prefix (e.g. '02_') from both the directory name and each category
    key.  This is a safeguard against regression if folder numbers and
    translation-key numbers drift apart over time — it is not intended to
    support intentional numbering mismatches.
    """
    # 1) Exact match (fast path, no false positives)
    if dir_name in categories:
        return categories[dir_name]

    # 2) Suffix match: strip leading NN_ prefix and compare
    suffix = re.sub(r"^\d{2}_", "", dir_name)
    for k, v in categories.items():
        if re.sub(r"^\d{2}_", "", k) == suffix:
            return v

    # 3) Fallback: return raw dir name (will render as-is)
    return dir_name


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def build_certificates_section(data: dict) -> tuple[str, list[str]]:
    categories = data.get("categories", {})
    translations = data.get("files", {})
    pending = data.setdefault("pending", {})

    missing: list[str] = []
    rows = []

    for idx, d in enumerate(list_certificate_dirs()):
        cat_title = find_category_title(categories, d.name)
        zh_name, en_name = split_bilingual(cat_title)

        emoji = CAT_EMOJIS[idx % len(CAT_EMOJIS)]
        if en_name:
            cat_cell = f"{emoji} **{zh_name}**<br><sub>{en_name}</sub>"
        else:
            cat_cell = f"{emoji} **{zh_name}**"

        files = [p for p in sorted(d.iterdir()) if p.is_file()]
        items = []
        for fp in files:
            base = strip_numeric_prefix(strip_ext(fp.name))
            # Promote from pending to files if the user has filled in a translation
            if base in pending and pending[base]:
                translations[base] = pending.pop(base)
            zh = translations.get(base)
            if not zh:
                missing.append(base)
                if base not in pending:
                    pending[base] = None
                zh = humanize_fallback(base)
            items.append(zh)

        content = "<br>".join(f"• {item}" for item in items) if items else "（無）"
        rows.append(f"| {cat_cell} | {content} |")

    section = "\n".join([
        "## 📋 專業證照與訓練（Professional Certifications & Training）",
        "",
        "| 分類 Category | 項目 Items |",
        "|:---|:---|",
        *rows,
        "",
    ])
    return section, missing


def build_work_experience_section() -> str:
    data_path = CV_FOLDER / "10_Work_Experience" / "work_experience.yml"
    data = load_yaml(data_path)
    if not data or not isinstance(data, list):
        return ""

    rows = []
    for item in data:
        period = item.get("period", "")
        institution = item.get("institution", "")
        role = item.get("role", "")
        url = item.get("url", "")
        note = item.get("note", "")

        inst_text = f"[{institution}]({url})" if url else institution
        note_text = f"<br><sub>{note}</sub>" if note else ""
        rows.append(f"| **{period}** | {inst_text} | {role}{note_text} |")

    return "\n".join([
        "## 💼 工作經歷（Work Experience）",
        "",
        "| 期間 Period | 機構 Institution | 職稱 Role |",
        "|:---|:---|:---|",
        *rows,
        "",
    ])


def build_publications_section() -> str:
    data_path = CV_FOLDER / "publications" / "publications.yml"
    data = load_yaml(data_path)
    if not data or not isinstance(data, list):
        return ""

    lines = [
        "## 📚 發表論文（Publications）",
        "",
    ]
    for i, pub in enumerate(data, 1):
        authors = pub.get("authors", "")
        title = pub.get("title", "")
        journal = pub.get("journal", "")
        year = pub.get("year", "")
        detail = pub.get("detail", "")
        doi = pub.get("doi", "")
        url = pub.get("url", "")
        image = pub.get("image", "")
        note = pub.get("note", "")

        link = url if url else (f"https://doi.org/{doi}" if doi else "")
        title_text = f"[{title}]({link})" if link else title

        citation = f"{i}. {authors} {title_text} *{journal}*."
        if detail:
            citation += f" {detail}."
        if note:
            citation += f" {note}."

        if image:
            lines.append(f'<img src="{image}" width="100" align="right" style="margin-left:8px">')
        lines.append(citation)
        lines.append("")

    return "\n".join(lines)


def build_projects_section() -> str:
    data_path = CV_FOLDER / "projects" / "projects.yml"
    data = load_yaml(data_path)
    if not data or not isinstance(data, list):
        return ""

    lines = [
        "## 🔬 研究與 AI 專案（Research & AI Projects）",
        "",
    ]
    for proj in data:
        title = proj.get("title", "")
        description = proj.get("description", "")
        url = proj.get("url", "")
        image = proj.get("image", "")
        tags = proj.get("tags", [])
        status = proj.get("status", "")
        note = proj.get("note", "")

        title_text = f"**[{title}]({url})**" if url else f"**{title}**"
        header_parts = [title_text]
        if status:
            header_parts.append(f"`{status}`")
        lines.append("### " + " ".join(header_parts) if not url else title_text)

        if status and url:
            lines.append(f"`{status}`")

        if image:
            lines.append(f'<img src="{image}" width="200" align="right">')
        if description:
            desc = str(description).strip()
            lines.append(desc)
        if note:
            lines.append(f"*{note}*")
        if tags:
            lines.append("**Tags:** " + " ".join(f"`{t}`" for t in tags))
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# README updater
# ---------------------------------------------------------------------------

def upsert_readme_section(readme_text: str, new_section: str) -> str:
    if START_MARK in readme_text and END_MARK in readme_text:
        before, rest = readme_text.split(START_MARK, 1)
        _, after = rest.split(END_MARK, 1)
        return before + START_MARK + "\n\n" + new_section + "\n" + END_MARK + after
    insert = f"{START_MARK}\n\n{new_section}\n{END_MARK}\n\n"
    return insert + readme_text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    data = load_dict()
    data.setdefault("pending", {})
    data.setdefault("categories", {})
    data.setdefault("files", {})

    default_categories = {
        "01_Core_Licensure_and_Specialty": "核心執照與專科資格 / Core Licensure & Specialty",
        "02_Neurovascular_Endovascular": "腦血管與介入 / Neurovascular & Endovascular",
        "03_Ultrasound_Multisystem": "超音波（多系統）/ Ultrasound (Multisystem)",
        "04_Home_Care_LongTermCare_Community": "居家照護／長照／社區 / Home Care / LTC / Community",
        "05_Neuromodulation_TMS_VNS_tPBM": "神經調控 / Neuromodulation / TMS / VNS / tPBM",
        "06_Acute_Care_Emergency": "急性照護 / Acute Care & Emergency",
        "07_Regulatory": "法規與管制 / Regulatory",
        "08_Advanced_Therapies_Cell_Therapy": "進階治療 / Advanced Therapies & Cell Therapy",
        "09_Education_and_Service": "學歷與服務 / Education & Service",
    }
    for k, v in default_categories.items():
        data["categories"][k] = v  # always keep in sync with defaults

    cert_section, missing = build_certificates_section(data)
    work_section = build_work_experience_section()
    pub_section = build_publications_section()
    proj_section = build_projects_section()

    parts = [cert_section]
    if work_section:
        parts.append(work_section)
    if pub_section:
        parts.append(pub_section)
    if proj_section:
        parts.append(proj_section)
    full_section = "\n".join(parts)

    if not README_PATH.exists():
        README_PATH.write_text("# Dr. Chan Lin Chu - CV and licenses\n\n", encoding="utf-8")

    old = README_PATH.read_text(encoding="utf-8")
    updated = upsert_readme_section(old, full_section)
    README_PATH.write_text(updated, encoding="utf-8")

    save_dict(data)

    if missing:
        unique_missing = sorted(set(missing))
        print("Missing translations (add to .github/translations.yml under files:):")
        for k in unique_missing:
            print(f" - {k}")
    else:
        print("All filenames translated.")


if __name__ == "__main__":
    main()

