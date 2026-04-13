# CV and Certificate – Automation Scripts

These Python scripts are run automatically by the GitHub Actions workflow
`.github/workflows/update-readme.yml` on every push to `main`.

---

## Scripts

### `normalize_new_files.py`

**Purpose:** Detect freshly uploaded certificate files that lack a `NN_`
numeric sort-prefix, move them to the correct destination folder, rename them
with the next available prefix, and register a placeholder translation key.

**When it runs:** First step in the workflow, before README generation.

**How "new file" is detected:**
Any file inside a `02_*` folder (configurable via `SOURCE_FOLDER_PATTERN`)
whose name does *not* start with two digits followed by `_` (e.g. `01_`) is
considered unnormalised.

**Default behaviour:**
- Source: all folders matching `^02_` under `CV and certificate/`
- Destination: the first `03_*` folder found (alphabetically)
- Numbering: next sequential `NN_` prefix in the destination folder

**Configuration (edit the two constants at the top of the script):**

| Constant | Default | Description |
|---|---|---|
| `SOURCE_FOLDER_PATTERN` | `^02_` | Regex matched against folder names inside `CV and certificate/`. All matching folders are scanned for unnumbered files. |
| `DEST_FOLDER_NAME` | `None` | Exact folder name to move files into. `None` = auto-detect first `03_*` folder. |

**Example – keep files in the same folder (just add a prefix):**
```python
SOURCE_FOLDER_PATTERN = r"^02_Neurovascular_Endovascular$"
DEST_FOLDER_NAME      = "02_Neurovascular_Endovascular"
```

**Manual run:**
```bash
pip install pyyaml
python "CV and certificate/scripts/normalize_new_files.py"
```

---

### `generate_readme_section.py`

Reads all `01_`–`09_*` category folders, builds the certificates table, work
experience, publications, and projects sections, and upserts them between the
`<!-- AUTO-GENERATED:START -->` / `<!-- AUTO-GENERATED:END -->` markers in
`README.md`.

Also maintains `.github/translations.yml`:
- New filenames without a translation are placed in `pending:` (top of file).
- Once you fill in a translation under `pending:`, the next run promotes it
  to `files:`.

---

### `fetch_pubmed_links.py`

Fetches live DOI / URL data for publications listed in
`CV and certificate/publications/publications.yml`.

---

### `fetch_project_files.py`

Downloads the Colab notebook and Google Doc HTML for the projects section.

---

## Workflow loop prevention

The workflow carries an `if: github.actor != 'github-actions[bot]'` guard on
the job so that the commit pushed by the bot itself does **not** re-trigger
another run.
