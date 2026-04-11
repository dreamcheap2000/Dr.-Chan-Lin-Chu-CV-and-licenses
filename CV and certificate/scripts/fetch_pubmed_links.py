"""
fetch_pubmed_links.py
~~~~~~~~~~~~~~~~~~~~~
Looks up each publication in publications.yml via the PubMed E-utilities API
(by DOI), retrieves the correct PMID, and writes a ``url`` field pointing to
the PubMed record (https://pubmed.ncbi.nlm.nih.gov/{PMID}/).

Run this script before generate_readme_section.py so that the README always
contains working PubMed links.

Usage:
    python "CV and certificate/scripts/fetch_pubmed_links.py"
"""
from __future__ import annotations

import time
from pathlib import Path

try:
    import requests
except ImportError as e:
    raise SystemExit("Missing dependency: requests.  Install: pip install requests") from e

try:
    import yaml
except ImportError as e:
    raise SystemExit("Missing dependency: pyyaml.  Install: pip install pyyaml") from e

REPO_ROOT = Path(__file__).resolve().parents[2]
CV_FOLDER = REPO_ROOT / "CV and certificate"
PUB_PATH = CV_FOLDER / "publications" / "publications.yml"

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
PUBMED_BASE = "https://pubmed.ncbi.nlm.nih.gov/"


def search_pmid_by_doi(doi: str) -> str | None:
    """Return PubMed ID for a given DOI, or None if not found."""
    try:
        r = requests.get(
            f"{EUTILS_BASE}esearch.fcgi",
            params={"db": "pubmed", "term": f"{doi}[DOI]", "retmode": "json"},
            timeout=15,
        )
        r.raise_for_status()
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        return ids[0] if ids else None
    except Exception as exc:
        print(f"  Warning: could not fetch PMID for DOI {doi}: {exc}")
        return None


def main() -> None:
    if not PUB_PATH.exists():
        print(f"publications.yml not found at {PUB_PATH}")
        return

    with PUB_PATH.open("r", encoding="utf-8") as f:
        pubs = yaml.safe_load(f)

    if not isinstance(pubs, list):
        print("Unexpected format in publications.yml")
        return

    changed = False
    for pub in pubs:
        doi = pub.get("doi", "")
        existing_url = pub.get("url", "")

        if not doi:
            continue  # nothing to look up

        # If a manual url is already set, honour it and skip the API call.
        if existing_url and "pubmed" in existing_url:
            print(f"  Already has PubMed URL: {existing_url}")
            continue

        print(f"  Searching PubMed for DOI: {doi}")
        pmid = search_pmid_by_doi(doi)
        time.sleep(0.4)  # be polite to the NCBI API

        if pmid:
            new_url = f"{PUBMED_BASE}{pmid}/"
            print(f"  → PMID {pmid}  URL: {new_url}")
            pub["url"] = new_url
            # Move PMID into note if not already there
            existing_note = pub.get("note", "")
            if f"PMID: {pmid}" not in existing_note:
                pub["note"] = (existing_note + f" PMID: {pmid}").strip()
            changed = True
        else:
            print(f"  → Not found on PubMed; keeping DOI link.")

    if changed:
        with PUB_PATH.open("w", encoding="utf-8") as f:
            yaml.safe_dump(pubs, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print("publications.yml updated with PubMed URLs.")
    else:
        print("No changes needed.")


if __name__ == "__main__":
    main()
