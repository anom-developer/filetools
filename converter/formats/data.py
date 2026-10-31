"""Data format conversions: JSON ↔ CSV, MD → TXT, HTML → TXT."""
import csv
import html
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def _detect_csv_dialect(text: str) -> csv.Dialect:
    """Attempt to sniff delimiter, default to excel (comma)."""
    try:
        sample = "\n".join(text.splitlines()[:10])
        return csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
    except Exception:
        return csv.excel  # default to standard comma delimiter


def _auto_convert_value(val: str) -> Any:
    """Convert string to int, float, or bool if applicable."""
    val_clean = val.strip()
    if val_clean.lower() == "true":
        return True
    if val_clean.lower() == "false":
        return False
    if val_clean.lower() in ("null", "none"):
        return None
    try:
        if "." in val_clean or "e" in val_clean.lower():
            return float(val_clean)
        return int(val_clean)
    except ValueError:
        return val


def json_to_csv(
    input_path: Path,
    output_path: Path,
    *,
    encoding: str = "utf-8",
) -> None:
    """
    Convert a JSON file to CSV.

    Supports:
      - Array of objects: [{"a": 1}, {"a": 2}]
      - Single object: {"a": 1, "b": 2} -> converted as 1-row CSV
      - Nested objects/arrays are serialized to JSON strings.
    """
    raw = json.loads(input_path.read_text(encoding=encoding))

    if isinstance(raw, dict):
        raw = [raw]
    elif not isinstance(raw, list):
        raise ValueError(
            "JSON → CSV conversion requires the root element to be a JSON object or array."
        )

    if not raw:
        output_path.write_text("", encoding=encoding)
        return

    # Normalize rows: ensure all rows are dicts
    normalized_rows: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw):
        if isinstance(item, dict):
            row_dict = {}
            for k, v in item.items():
                if isinstance(v, (dict, list)):
                    row_dict[k] = json.dumps(v, ensure_ascii=False)
                else:
                    row_dict[k] = v
            normalized_rows.append(row_dict)
        else:
            normalized_rows.append({"value": item})

    # Collect all keys preserving insertion order
    fieldnames: List[str] = list(dict.fromkeys(k for row in normalized_rows for k in row))

    with output_path.open("w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(normalized_rows)


def csv_to_json(
    input_path: Path,
    output_path: Path,
    *,
    encoding: str = "utf-8",
    parse_types: bool = False,
    indent: int = 2,
) -> None:
    """Convert a CSV file to a JSON array of objects with automatic delimiter detection."""
    content = input_path.read_text(encoding=encoding)
    if not content.strip():
        output_path.write_text("[]", encoding=encoding)
        return

    dialect = _detect_csv_dialect(content)
    reader = csv.DictReader(content.splitlines(), dialect=dialect)

    rows: List[Dict[str, Any]] = []
    for row in reader:
        if parse_types:
            clean_row = {k: _auto_convert_value(v) if v is not None else None for k, v in row.items()}
            rows.append(clean_row)
        else:
            rows.append(dict(row))

    output_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=indent if indent > 0 else None),
        encoding=encoding,
    )


# Patterns to strip common Markdown syntax
_MD_PATTERNS = [
    (re.compile(r"^#{1,6}\s+", re.M), ""),            # headings (multiline enabled)
    (re.compile(r"\*\*(.+?)\*\*"), r"\1"),             # bold **text**
    (re.compile(r"__(.+?)__"), r"\1"),                 # bold __text__
    (re.compile(r"\*(.+?)\*"), r"\1"),                  # italic *text*
    (re.compile(r"_(.+?)_"), r"\1"),                   # italic _text_
    (re.compile(r"~~(.+?)~~"), r"\1"),                 # strikethrough ~~text~~
    (re.compile(r"`{3}.*?`{3}", re.S), ""),            # fenced code blocks
    (re.compile(r"`(.+?)`"), r"\1"),                    # inline code
    (re.compile(r"!\[.*?\]\(.*?\)"), ""),               # images
    (re.compile(r"\[(.+?)\]\(.*?\)"), r"\1"),          # links
    (re.compile(r"^\s*[-*+]\s+", re.M), "• "),         # unordered list
    (re.compile(r"^\s*(\d+)\.\s+", re.M), r"\1. "),    # ordered list (preserves number)
    (re.compile(r"^\s*>\s+", re.M), ""),               # blockquotes
    (re.compile(r"^---+$", re.M), "─" * 40),          # horizontal rules
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


def html_to_txt(
    input_path: Path,
    output_path: Path,
    *,
    encoding: str = "utf-8",
) -> None:
    """Convert HTML document to plain text by stripping tags and formatting breaks."""
    raw_html = input_path.read_text(encoding=encoding, errors="replace")

    # Remove script and style elements
    clean = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw_html, flags=re.S | re.I)
    # Convert <br>, <hr>, <p>, <div>, <li>, <tr> to newlines
    clean = re.sub(r"<br\s*/?>", "\n", clean, flags=re.I)
    clean = re.sub(r"</?(p|div|tr|li|h[1-6])[^>]*>", "\n", clean, flags=re.I)
    # Strip remaining HTML tags
    clean = re.sub(r"<[^>]+>", "", clean)
    # Unescape HTML entities (&nbsp;, &amp;, etc.)
    text = html.unescape(clean)
    # Normalize multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"

    output_path.write_text(text, encoding=encoding)
