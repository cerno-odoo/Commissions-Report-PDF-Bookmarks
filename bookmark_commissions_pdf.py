"""Add per-client bookmarks to a commissions report PDF.

Scans every page for the pair of headers `Prepared for: <client>` and
`Report Period: <period>`. Each page that contains both gets a top-level
bookmark titled `<client> - <period>`. Repeat labels are skipped so only
the first page producing a given label is bookmarked.

Run with no arguments — a file dialog asks for the input PDF, and the
output is saved next to it as `<name>_bookmarked.pdf`.
"""

from __future__ import annotations

import re
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError

PREPARED_RE = re.compile(r"Prepared for:\s*(.+)")
PERIOD_RE = re.compile(r"Report Period:\s*(.+)")
TRIM_MARKERS = ("Prepared for:", "Report Period:")


def _clean(value: str) -> str:
    """Trim a capture at the next labeled field in case pypdf's text
    extraction concatenated visually-separate lines without a newline."""
    cut = len(value)
    for marker in TRIM_MARKERS:
        idx = value.find(marker)
        if idx != -1 and idx < cut:
            cut = idx
    return value[:cut].strip()


def pick_input_pdf() -> Path | None:
    root = tk.Tk()
    root.withdraw()
    chosen = filedialog.askopenfilename(
        title="Select commissions report PDF",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
    )
    root.destroy()
    return Path(chosen) if chosen else None


def unique_output_path(input_path: Path) -> Path:
    candidate = input_path.with_name(f"{input_path.stem}_bookmarked.pdf")
    n = 1
    while candidate.exists():
        candidate = input_path.with_name(f"{input_path.stem}_bookmarked ({n}).pdf")
        n += 1
    return candidate


def find_bookmarks(reader: PdfReader) -> list[tuple[str, int]]:
    """Return [(label, page_index), ...] in page order, deduped by label."""
    bookmarks: list[tuple[str, int]] = []
    seen: set[str] = set()
    for page_index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        prepared = PREPARED_RE.search(text)
        period = PERIOD_RE.search(text)
        if not (prepared and period):
            continue
        client = _clean(prepared.group(1))
        report_period = _clean(period.group(1))
        if not client or not report_period:
            continue
        label = f"{client} - {report_period}"
        if label in seen:
            continue
        seen.add(label)
        bookmarks.append((label, page_index))
    return bookmarks


def main() -> int:
    input_path = pick_input_pdf()
    if input_path is None:
        return 0

    try:
        reader = PdfReader(str(input_path))
    except (PdfReadError, OSError) as exc:
        messagebox.showerror("Could not open PDF", f"{input_path.name}\n\n{exc}")
        return 1

    if reader.is_encrypted and not reader.decrypt(""):
        messagebox.showerror(
            "Encrypted PDF",
            f"{input_path.name} is password-protected. Remove the password and try again.",
        )
        return 1

    bookmarks = find_bookmarks(reader)
    page_count = len(reader.pages)

    if not bookmarks:
        messagebox.showinfo(
            "No headers found",
            "No pages contained both 'Prepared for:' and 'Report Period:'.\n"
            "No output file was written.",
        )
        return 0

    writer = PdfWriter(clone_from=reader)
    for label, page_index in bookmarks:
        writer.add_outline_item(title=label, page_number=page_index)

    output_path = unique_output_path(input_path)
    with output_path.open("wb") as fh:
        writer.write(fh)

    summary = (
        f"Added {len(bookmarks)} bookmark(s) across {page_count} page(s).\n\n"
        f"Saved to:\n{output_path}"
    )
    print(summary)
    messagebox.showinfo("Bookmarks added", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
