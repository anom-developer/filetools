"""CLI interface for the file searcher."""
import argparse
import sys
from pathlib import Path

from searcher.core import SearchOptions, search
from searcher.output import Printer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="searcher",
        description="🔍 FileTools Searcher — find files by name or content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_EXAMPLES,
    )

    parser.add_argument(
        "pattern",
        help="Filename mask (e.g. '*.py') or regex (with --regex)",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory to search (default: current directory)",
    )

    parser.add_argument(
        "-r", "--regex",
        action="store_true",
        help="Treat pattern as a regular expression",
    )
    parser.add_argument(
        "-c", "--content",
        metavar="TEXT",
        dest="content_pattern",
        help="Also search inside file contents for this text/regex",
    )
    parser.add_argument(
        "-e", "--ext",
        nargs="+",
        metavar="EXT",
        dest="extensions",
        help="Filter by extension(s), e.g. --ext .py .txt",
    )
    parser.add_argument(
        "-d", "--depth",
        type=int,
        default=None,
        metavar="N",
        help="Maximum recursion depth (default: unlimited)",
    )
    parser.add_argument(
        "-i", "--ignore-case",
        action="store_true",
        dest="ignore_case",
        help="Case-insensitive matching",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        dest="no_color",
        help="Disable ANSI color output",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Save plain-text results to FILE",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show file size and modification date",
    )
    parser.add_argument(
        "-s", "--stats",
        action="store_true",
        help="Print summary statistics at the end",
    )

    return parser


_EXAMPLES = """\
examples:
  python -m searcher "*.py" ./src
  python -m searcher --regex "report_\\d{4}\\.pdf" ./documents
  python -m searcher --content "TODO" . --ext .py --verbose
  python -m searcher "*.log" /var/log --depth 2
  python -m searcher "*.txt" . --ignore-case --output results.txt
"""


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"❌  Error: directory not found: {root}", file=sys.stderr)
        sys.exit(1)
    if not root.is_dir():
        print(f"❌  Error: not a directory: {root}", file=sys.stderr)
        sys.exit(1)

    # Normalise extensions
    extensions = None
    if args.extensions:
        extensions = [
            e if e.startswith(".") else f".{e}"
            for e in args.extensions
        ]

    opts = SearchOptions(
        pattern=args.pattern,
        root=root,
        use_regex=args.regex,
        content_pattern=args.content_pattern,
        extensions=extensions,
        max_depth=args.depth,
        ignore_case=args.ignore_case,
    )

    printer = Printer(
        use_color=not args.no_color,
        verbose=args.verbose,
        output_file=Path(args.output) if args.output else None,
    )

    printer.print_header(opts)

    results = search(opts)
    for result in results:
        printer.print_result(result)

    printer.print_footer(show_stats=args.stats)
    printer.close()

    if not printer.total:
        sys.exit(1)  # No results → non-zero exit (useful in shell scripts)
