"""Core conversion dispatch logic."""
from pathlib import Path
from typing import Optional, Set, Tuple

from converter.formats.images import convert_image
from converter.formats.documents import txt_to_pdf
from converter.formats.data import json_to_csv, csv_to_json, md_to_txt, html_to_txt

_IMAGE_FORMATS: Set[str] = {"png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"}

# Build set of supported (source_ext, target_ext) pairs — all lowercase, no dot
SUPPORTED_CONVERSIONS: Set[Tuple[str, str]] = set()

# Add all image-to-image conversions (including same-format for resize/rotate/effects)
for _src in _IMAGE_FORMATS:
    for _dst in _IMAGE_FORMATS:
        SUPPORTED_CONVERSIONS.add((_src, _dst))

# Document and data conversions
SUPPORTED_CONVERSIONS.update({
    ("txt", "pdf"),
    ("json", "csv"),
    ("csv", "json"),
    ("md", "txt"),
    ("html", "txt"),
    ("htm", "txt"),
})


def convert_file(
    input_path: Path,
    output_path: Path,
    *,
    quality: int = 90,
    font_size: int = 12,
    encoding: str = "utf-8",
    resize: Optional[str] = None,
    rotate: Optional[int] = None,
    grayscale: bool = False,
    parse_types: bool = False,
    font_path: Optional[Path] = None,
    overwrite: bool = True,
    verbose: bool = False,
) -> Path:
    """
    Convert *input_path* to *output_path*.
    The conversion is determined by the file extensions.
    Returns the resolved output path.
    """
    src_ext = input_path.suffix.lstrip(".").lower()
    dst_ext = output_path.suffix.lstrip(".").lower()

    if (src_ext, dst_ext) not in SUPPORTED_CONVERSIONS:
        raise ValueError(
            f"Unsupported conversion: .{src_ext} → .{dst_ext}. "
            f"Run with --help to see supported pairs."
        )

    if output_path.exists() and not overwrite:
        if verbose:
            print(f"  ⏭  Skipping {output_path.name} (file already exists)")
        return output_path

    if verbose:
        print(f"  Converting {input_path.name}  →  {output_path.name}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Images ──────────────────────────────────────────────────────────────
    if src_ext in _IMAGE_FORMATS and dst_ext in _IMAGE_FORMATS:
        convert_image(
            input_path,
            output_path,
            quality=quality,
            resize=resize,
            rotate=rotate,
            grayscale=grayscale,
        )

    # ── TXT → PDF ────────────────────────────────────────────────────────────
    elif src_ext == "txt" and dst_ext == "pdf":
        txt_to_pdf(
            input_path,
            output_path,
            font_size=font_size,
            encoding=encoding,
            font_path=font_path,
        )

    # ── JSON ↔ CSV ────────────────────────────────────────────────────────────
    elif src_ext == "json" and dst_ext == "csv":
        json_to_csv(input_path, output_path, encoding=encoding)

    elif src_ext == "csv" and dst_ext == "json":
        csv_to_json(input_path, output_path, encoding=encoding, parse_types=parse_types)

    # ── MD / HTML → TXT ───────────────────────────────────────────────────────
    elif src_ext == "md" and dst_ext == "txt":
        md_to_txt(input_path, output_path, encoding=encoding)

    elif src_ext in ("html", "htm") and dst_ext == "txt":
        html_to_txt(input_path, output_path, encoding=encoding)

    return output_path


def convert_directory(
    input_dir: Path,
    output_dir: Path,
    target_fmt: str,
    *,
    recursive: bool = False,
    quality: int = 90,
    font_size: int = 12,
    encoding: str = "utf-8",
    resize: Optional[str] = None,
    rotate: Optional[int] = None,
    grayscale: bool = False,
    parse_types: bool = False,
    font_path: Optional[Path] = None,
    overwrite: bool = True,
    verbose: bool = False,
) -> int:
    """
    Convert all files in *input_dir* to *target_fmt* and save them in *output_dir*.
    If *recursive* is True, preserves directory structure.
    Returns the number of successfully converted files.
    """
    target_fmt = target_fmt.lstrip(".").lower()
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    if recursive:
        file_iterator = [p for p in input_dir.rglob("*") if p.is_file()]
    else:
        file_iterator = [p for p in input_dir.iterdir() if p.is_file()]

    for src in sorted(file_iterator):
        src_ext = src.suffix.lstrip(".").lower()
        if (src_ext, target_fmt) not in SUPPORTED_CONVERSIONS:
            if verbose:
                print(f"  ⚠  Skipping {src.name} (no .{src_ext}→.{target_fmt} converter)")
            continue

        if recursive:
            rel_path = src.relative_to(input_dir)
            dst = output_dir / rel_path.with_suffix(f".{target_fmt}")
        else:
            dst = output_dir / src.with_suffix(f".{target_fmt}").name

        try:
            convert_file(
                src,
                dst,
                quality=quality,
                font_size=font_size,
                encoding=encoding,
                resize=resize,
                rotate=rotate,
                grayscale=grayscale,
                parse_types=parse_types,
                font_path=font_path,
                overwrite=overwrite,
                verbose=verbose,
            )
            count += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  ⚠  Failed to convert {src.name}: {exc}")

    return count
