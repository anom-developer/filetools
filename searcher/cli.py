"""CLI interface for the file searcher."""
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

from searcher.core import SearchOptions, parse_relative_time, parse_size, search
from searcher.output import Printer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="searcher",
        description="FileTools Searcher — find files by name or content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_EXAMPLES,
    )

    parser.add_argument(
        "pattern",
        nargs="?",
        default=None,
        help="Filename mask (e.g. '*.py') or regex (with --regex). Defaults to '*' if --content is used.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Directory to search (default: current directory)",
    )

    parser.add_argument(
        "-r", "--regex",
        action="store_true",
        help="Treat filename pattern as a regular expression",
    )
    parser.add_argument(
        "-c", "--content",
        metavar="TEXT",
        dest="content_pattern",
        help="Search inside file contents for this text or regular expression",
    )
    parser.add_argument(
        "-C", "--context",
        type=int,
        default=0,
        metavar="N",
        dest="context_lines",
        help="Show N lines of context before and after each content match",
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
        help="Case-insensitive matching for both filename and content",
    )
    parser.add_argument(
        "--min-size",
        metavar="SIZE",
        help="Minimum file size (e.g. 500B, 10KB, 2MB, 1GB)",
    )
    parser.add_argument(
        "--max-size",
        metavar="SIZE",
        help="Maximum file size (e.g. 100KB, 50MB)",
    )
    parser.add_argument(
        "--mtime",
        metavar="TIME",
        help="Filter by modification time: -7d (last 7 days), +30d (older than 30 days), -24h",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        metavar="PATTERN",
        help="Exclude files or directories matching glob patterns (e.g. --exclude '*.tmp' 'backup*')",
    )
    parser.add_argument(
        "-a", "--all", "--hidden",
        action="store_true",
        dest="include_hidden",
        help="Include hidden files and directories (starting with '.')",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output results in JSON format",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        dest="count_only",
        help="Only output the total number of matching files",
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
        help="Save results to FILE",
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
  searcher "*.py" ./src
  searcher --regex "report_\\d{4}\\.pdf" ./documents
  searcher --content "TODO" . --ext .py --verbose
  searcher --content "function" ./src -C 2
  searcher "*.log" /var/log --depth 2 --min-size 1MB
  searcher "*.txt" . --ignore-case --output results.txt
  searcher --mtime -7d ./project --json
"""


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    pattern = args.pattern
    path_arg = args.path

    # Smart pattern and path resolution:
    # 1. searcher --content "TODO" .
    #    -> pattern='.', path_arg=None, but '.' is a dir!
    if pattern and path_arg is None and Path(pattern).is_dir() and (args.content_pattern or args.extensions):
        path_arg = pattern
        pattern = "*"

    # 2. searcher --content "TODO" (no positional args)
    if pattern is None:
        pattern = "*"

    # 3. default path is current directory
    if path_arg is None:
        path_arg = "."

    root = Path(path_arg)
    if not root.exists():
        print(f"Error: directory not found: {root}", file=sys.stderr)
        sys.exit(1)
    if not root.is_dir():
        print(f"Error: not a directory: {root}", file=sys.stderr)
        sys.exit(1)

    # Normalise extensions
    extensions = None
    if args.extensions:
        extensions = [
            e if e.startswith(".") else f".{e}"
            for e in args.extensions
        ]

    # Parse size filters
    min_size = parse_size(args.min_size) if args.min_size else None
    max_size = parse_size(args.max_size) if args.max_size else None

    # Parse time filter
    modified_after = None
    modified_before = None
    if args.mtime:
        mtime_clean = args.mtime.strip()
        ts = parse_relative_time(mtime_clean)
        if mtime_clean.startswith("+"):
            modified_before = ts
        else:
            modified_after = ts

    opts = SearchOptions(
        pattern=pattern,
        root=root,
        use_regex=args.regex,
        content_pattern=args.content_pattern,
        extensions=extensions,
        max_depth=args.depth,
        ignore_case=args.ignore_case,
        min_size=min_size,
        max_size=max_size,
        modified_after=modified_after,
        modified_before=modified_before,
        exclude=args.exclude,
        include_hidden=args.include_hidden,
        context_lines=args.context_lines,
    )

    printer = Printer(
        use_color=not args.no_color,
        verbose=args.verbose,
        output_file=Path(args.output) if args.output else None,
        as_json=args.as_json,
        count_only=args.count_only,
    )

    printer.print_header(opts)

    results = search(opts)
    for result in results:
        printer.print_result(result)

    printer.print_footer(show_stats=args.stats)
    printer.close()

    if not printer.total and not args.as_json:
        sys.exit(1)  # No results → non-zero exit


if __name__ == "__main__":
    main()
