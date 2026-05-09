# Commissions Report PDF Bookmarker

A small Windows utility that adds per-client bookmarks to a multi-client commissions
report PDF, turning the bookmarks pane in any PDF reader into a clickable client
index.

## What it does

Cerno's commissions reports are concatenated into a single PDF that contains many
client sections back-to-back. Each section starts with a header that looks like:

```
Prepared for: Sales Rep
Report Period: April 2026
```

Out of the box those PDFs have no bookmarks, so jumping to a specific client means
scrolling. This script reads a chosen PDF, finds every page that contains **both**
of those header lines, and writes a copy with a top-level bookmark on each of those
pages titled:

```
<client> - <period>
```

For the example above, the bookmark label is `Sales Rep - April 2026`.

The original PDF is never modified — the result is saved alongside it as
`<original name>_bookmarked.pdf`.

## Requirements

- Windows with Python 3.10 or newer (uses `from __future__ import annotations` plus
  `X | None` syntax)
- [`pypdf`](https://pypi.org/project/pypdf/) — install once with `pip install pypdf`
- `tkinter` — bundled with the standard Python.org Windows installer; no extra
  install needed

## Usage

Double-click `bookmark_commissions_pdf.py`, or from a terminal:

```
python bookmark_commissions_pdf.py
```

The script opens a file-picker dialog. Choose the commissions PDF and wait for the
"Bookmarks added" confirmation dialog. The output file is written next to the
input — for example, picking `April 2026 Commissions.pdf` produces
`April 2026 Commissions_bookmarked.pdf` in the same folder.

If a file with the target output name already exists, the script appends ` (1)`,
` (2)`, … rather than overwriting it.

## How matching works

For every page, the text layer is extracted with `pypdf` and two regular expressions
look for the marker lines anywhere on the page:

| Regex                       | Captures        |
|-----------------------------|-----------------|
| `Prepared for:\s*(.+)`      | client name     |
| `Report Period:\s*(.+)`     | reporting period|

A page is bookmarked **only when both markers are found**. The captured values are
then run through a small cleanup step that trims either capture at the start of any
subsequent labeled field — this works around a quirk where `pypdf` occasionally
concatenates two visually-separate header lines without a newline between them
(e.g. `Report Period: April 2026Prepared for: Sales Rep`), which would
otherwise leak the next field's text into the bookmark label.

Once a label has been used, later pages that produce the same label are skipped, so
each unique `<client> - <period>` combination is bookmarked exactly once at its
first occurrence.

## Output behavior summary

| Situation                                 | Result                                                    |
|-------------------------------------------|-----------------------------------------------------------|
| File dialog cancelled                     | Exit silently, no output                                  |
| Both markers found on N pages             | Output PDF written with N bookmarks (deduped by label)    |
| Neither marker found on any page          | Info dialog, no output written                            |
| Encrypted PDF (and empty password fails)  | Error dialog, exit                                        |
| Output name already taken                 | Auto-suffix ` (1)`, ` (2)`, …                             |
| Input file is corrupt or not a PDF        | Error dialog with the underlying `pypdf` error            |

## Limitations

- **Text-layer required.** Scanned PDFs without an OCR text layer have nothing for
  `pypdf` to extract, so no bookmarks will be added. Run OCR (Acrobat, ABBYY,
  `ocrmypdf`, etc.) first if needed.
- **`pypdf` extraction quirks.** A small number of PDF generators encode text in
  ways that `pypdf` extracts as garbled or out-of-order strings. If the script
  reports zero bookmarks on a PDF that visibly contains the headers, the next step
  is to swap the extraction backend to PyMuPDF (`pymupdf`/`fitz`). PyMuPDF was not
  chosen here because it is AGPL-licensed.
- **Top-level bookmarks only.** The output bookmarks are flat — there is no
  grouping by month or client. If hierarchical bookmarks are ever needed, the
  `add_outline_item` call in `bookmark_commissions_pdf.py` accepts a `parent`
  argument that can be used to nest items.

## Project layout

```
bookmark_commissions_pdf.py   the entire program — single file, no package
.gitignore                    excludes __pycache__/, virtualenvs, IDE folders,
                              and *_bookmarked.pdf outputs
README.md                     this file
```
