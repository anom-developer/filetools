"""CLI interface for the file converter."""
import argparse
import sys
from pathlib import Path

# Safe console configuration on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from converter.core import convert_file, convert_directory, SUPPORTED_CONVERSIONS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="converter",
        description="FileTools Converter — convert files between formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_build_examples(),
    )

    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("output", help="Output file or directory")

    parser.add_argument(
        "-f", "--format",
        dest="fmt",
        help="Target format when converting a directory (e.g. jpg, png, webp, csv, txt)",
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively process subdirectories when input is a directory",
    )
    parser.add_argument(
        "-q", "--quality",
        type=int,
        default=90,
        metavar="1-100",
        help="Image quality for lossy formats JPEG/WebP (default: 90)",
    )
    parser.add_argument(
        "--resize",
        metavar="WxH|P%",
        help="Resize image: WIDTHxHEIGHT (e.g. 800x600) or PERCENT%% (e.g. 50%%)",
    )
    parser.add_argument(
        "--rotate",
        type=int,
        choices=[90, 180, 270],
        help="Rotate image clockwise by 90, 180, or 270 degrees",
    )
    parser.add_argument(
        "--grayscale",
        action="store_true",
        help="Convert image to grayscale",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=12,
        dest="font_size",
        help="Font size for TXT → PDF conversion (default: 12)",
    )
    parser.add_argument(
        "--font",
        dest="font_path",
        help="Custom .ttf font file for TXT → PDF conversion",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Text file encoding (default: utf-8)",
    )
    parser.add_argument(
        "--parse-types",
        action="store_true",
        help="Automatically convert numbers and booleans when converting CSV to JSON",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Skip conversion if output file already exists",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output",
    )

    return parser


def _build_examples() -> str:
    lines = [
        "examples:",
        "  converter photo.png photo.jpg",
        "  converter icon.png favicon.ico",
        "  converter ./images/ ./output/ --format webp --recursive",
        "  converter photo.jpg thumb.jpg --resize 300x200",
        "  converter data.json data.csv",
        "  converter data.csv data.json --parse-types",
        "  converter notes.txt notes.pdf --font-size 14",
        "  converter document.html document.txt",
        "",
        "supported categories:",
        "  Images:    png, jpg, jpeg, webp, bmp, gif, tiff, ico (all pairs)",
        "  Documents: txt → pdf",
        "  Data:      json ↔ csv, md → txt, html → txt",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: input path does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    options = {
        "quality": args.quality,
        "font_size": args.font_size,
        "encoding": args.encoding,
        "resize": args.resize,
        "rotate": args.rotate,
        "grayscale": args.grayscale,
        "parse_types": args.parse_types,
        "font_path": Path(args.font_path) if args.font_path else None,
        "overwrite": not args.no_overwrite,
        "verbose": args.verbose,
    }

    try:
        if input_path.is_dir():
            if not args.fmt:
                print(
                    "Error: --format is required when converting a directory.",
                    file=sys.stderr,
                )
                sys.exit(1)
            count = convert_directory(
                input_path,
                output_path,
                args.fmt,
                recursive=args.recursive,
                **options,
            )
            print(f"Done. Converted {count} file(s).")
        else:
            out = convert_file(input_path, output_path, **options)
            print(f"Saved: {out}")
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
