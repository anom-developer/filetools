"""Document conversions: TXT → PDF."""
from pathlib import Path

try:
    from fpdf import FPDF
except ImportError as exc:
    raise ImportError("fpdf2 is required. Run: pip install fpdf2") from exc


def txt_to_pdf(
    input_path: Path,
    output_path: Path,
    *,
    font_size: int = 12,
    encoding: str = "utf-8",
) -> None:
    """
    Convert a plain-text file to a PDF document.

    Parameters
    ----------
    input_path  : source .txt file
    output_path : destination .pdf file
    font_size   : body text size in points (default 12)
    encoding    : text file encoding (default utf-8)
    """
    text = input_path.read_text(encoding=encoding, errors="replace")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=font_size)

    # Line height: 1.5× font size in document units (mm)
    line_height = font_size * 0.45 + 1.5

    for line in text.splitlines():
        if line.strip():
            pdf.cell(0, line_height, line, new_x="LMARGIN", new_y="NEXT")
        else:
            # Empty line — just advance vertical position
            pdf.ln(line_height)

    pdf.output(str(output_path))
