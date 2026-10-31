"""Data format conversions: JSON ↔ CSV, MD → TXT."""
import csv
import json
import re
from pathlib import Path


def json_to_csv(
    input_path: Path,
    output_path: Path,
    *,
    encoding: str = "utf-8",
) -> None:
    """
    Convert a JSON file containing a list of objects to CSV.

    The JSON root element must be an array of objects (dicts).
    Column order follows the keys of the first object.
    """
    raw = json.loads(input_path.read_text(encoding=encoding))

    if not isinstance(raw, list):
        raise ValueError(
            "JSON → CSV conversion requires the root element to be a JSON array."
        )
    if not raw:
        output_path.write_text("", encoding=encoding)
        return

    # Collect all keys preserving insertion order
    fieldnames: list[str] = list(dict.fromkeys(k for row in raw for k in row))

    with output_path.open("w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(raw)


def csv_to_json(
    input_path: Path,
    output_path: Path,
    *,
    encoding: str = "utf-8",
) -> None:
    """Convert a CSV file to a JSON array of objects."""
    with input_path.open(newline="", encoding=encoding) as f:
        reader = csv.DictReader(f)
        rows = [dict(row) for row in reader]

    output_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding=encoding,
    )


# Patterns to strip common Markdown syntax
_MD_PATTERNS = [
    (re.compile(r"^#{1,6}\s+"), ""),          # headings
    (re.compile(r"\*\*(.+?)\*\*"), r"\1"),    # bold **text**
    (re.compile(r"\*(.+?)\*"), r"\1"),         # italic *text*
    (re.compile(r"`{3}.*?`{3}", re.S), ""),   # fenced code blocks
    (re.compile(r"`(.+?)`"), r"\1"),           # inline code
    (re.compile(r"!\[.*?\]\(.*?\)"), ""),      # images
    (re.compile(r"\[(.+?)\]\(.*?\)"), r"\1"), # links
    (re.compile(r"^[-*+]\s+", re.M), "• "),   # unordered list
    (re.compile(r"^\d+\.\s+", re.M), ""),     # ordered list
    (re.compile(r"^>\s+", re.M), ""),         # blockquotes
    (re.compile(r"^---+$", re.M), "─" * 40), # horizontal rules
]


def md_to_txt(
    input_path: Path,
    output_path: Path,
    *,
    encoding: str = "utf-8",
) -> None:
    """Strip Markdown syntax and save as plain text."""
    text = input_path.read_text(encoding=encoding)
    for pattern, replacement in _MD_PATTERNS:
        text = pattern.sub(replacement, text)
    output_path.write_text(text, encoding=encoding)
