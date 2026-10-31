"""Document conversions: TXT → PDF."""
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from fpdf import FPDF
except ImportError as exc:
    raise ImportError("fpdf2 is required. Run: pip install fpdf2") from exc


def _find_system_unicode_font() -> Optional[Path]:
    """Search for common system TrueType fonts supporting Unicode/Cyrillic."""
    candidates = []
    if sys.platform == "win32":
        windir = os.environ.get("WINDIR", "C:\\Windows")
        fonts_dir = Path(windir) / "Fonts"
        candidates.extend([
            fonts_dir / "arial.ttf",
            fonts_dir / "calibri.ttf",
            fonts_dir / "segoeui.ttf",
        ])
    elif sys.platform == "darwin":
        candidates.extend([
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/Library/Fonts/Arial.ttf"),
            Path("/System/Library/Fonts/Helvetica.ttc"),
        ])
    else:
        # Linux / BSD
        candidates.extend([
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
            Path("/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf"),
            Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
        ])

    for p in candidates:
        if p.exists() and p.is_file():
            return p
    return None


def txt_to_pdf(
    input_path: Path,
    output_path: Path,
    *,
    font_size: int = 12,
    encoding: str = "utf-8",
    font_path: Optional[Path] = None,
) -> None:
    """
    Convert a plain-text file to a PDF document with full Unicode support.

    Parameters
    ----------
    input_path  : source .txt file
    output_path : destination .pdf file
    font_size   : body text size in points (default 12)
    encoding    : text file encoding (default utf-8)
    font_path   : optional path to custom .ttf font file
    """
    text = input_path.read_text(encoding=encoding, errors="replace")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Determine font to use
    selected_font_path = font_path if (font_path and font_path.exists()) else _find_system_unicode_font()

    font_family = "Helvetica"
    if selected_font_path:
        try:
            pdf.add_font("CustomUnicodeFont", "", str(selected_font_path))
            font_family = "CustomUnicodeFont"
        except Exception:
            font_family = "Helvetica"

    pdf.set_font(font_family, size=font_size)

    # Line height: 1.4x font size in document units (mm)
    line_height = max(5.0, font_size * 0.45 + 1.5)

    for line in text.splitlines():
        if line.strip():
            try:
                pdf.multi_cell(0, line_height, line, new_x="LMARGIN", new_y="NEXT")
            except Exception:
                # If font still fails on specific glyph, replace unsupported chars
                safe_line = line.encode("latin-1", "replace").decode("latin-1")
                pdf.multi_cell(0, line_height, safe_line, new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.ln(line_height)

    pdf.output(str(output_path))
