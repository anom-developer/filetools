"""CLI interface for the file converter."""
import argparse
import sys
from pathlib import Path

from converter.core import convert_file, convert_directory, SUPPORTED_CONVERSIONS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="converter",
        description="🔄 FileTools Converter — convert files between formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_build_examples(),
    )

    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("output", help="Output file or directory")

    parser.add_argument(
        "-f", "--format",
        dest="fmt",
        help="Target format when converting a directory (e.g. jpg, png, csv)",
    )
    parser.add_argument(
        "-q", "--quality",
        type=int,
        default=90,
        metavar="1-100",
        help="Image quality for lossy formats (default: 90)",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=12,
        dest="font_size",
        help="Font size for TXT → PDF conversion (default: 12)",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Text file encoding (default: utf-8)",
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
        "  python -m converter photo.png photo.jpg",
        "  python -m converter ./images/ ./output/ --format webp",
        "  python -m converter data.json data.csv",
        "  python -m converter notes.txt notes.pdf --font-size 14",
        "",
        "supported conversions:",
    ]
    for (src, dst) in sorted(SUPPORTED_CONVERSIONS):
        lines.append(f"  .{src:<8} → .{dst}")
    return "\n".join(lines)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"❌  Error: input path does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    options = {
        "quality": args.quality,
        "font_size": args.font_size,
        "encoding": args.encoding,
        "verbose": args.verbose,
    }

    try:
        if input_path.is_dir():
            if not args.fmt:
                print(
                    "❌  Error: --format is required when converting a directory.",
                    file=sys.stderr,
                )
                sys.exit(1)
            count = convert_directory(input_path, output_path, args.fmt, **options)
            print(f"✅  Done. Converted {count} file(s).")
        else:
            out = convert_file(input_path, output_path, **options)
            print(f"✅  Saved: {out}")
    except (ValueError, OSError) as exc:
        print(f"❌  {exc}", file=sys.stderr)
        sys.exit(1)
