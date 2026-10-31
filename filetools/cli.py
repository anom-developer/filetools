"""Unified CLI for FileTools."""
import argparse
import sys

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

from filetools import __version__
from converter.cli import main as converter_main
from searcher.cli import main as searcher_main


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in ("-V", "--version", "version"):
        print(f"FileTools v{__version__}")
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] in ("converter", "convert"):
        sys.argv.pop(1)
        converter_main()
        return

    if len(sys.argv) > 1 and sys.argv[1] in ("searcher", "search", "find"):
        sys.argv.pop(1)
        searcher_main()
        return

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    FileTools v{__version__}                          ║
║    Modern high-performance converter & searcher CLI toolkit   ║
╚══════════════════════════════════════════════════════════════╝

Usage:
  filetools converter [OPTIONS] INPUT OUTPUT
  filetools searcher  [OPTIONS] [PATTERN] [PATH]

Direct utilities:
  converter [OPTIONS] INPUT OUTPUT
  searcher  [OPTIONS] [PATTERN] [PATH]

Commands:
  converter, convert  Convert images, documents, and data files
  searcher, search    Search files by glob mask, regex, or content

General options:
  -h, --help          Show this help message and exit
  -V, --version       Show FileTools version and exit

Run 'filetools converter --help' or 'filetools searcher --help' for details.
""")
    if len(sys.argv) > 1 and sys.argv[1] not in ("-h", "--help"):
        print(f"Unknown command: '{sys.argv[1]}'. Use 'converter' or 'searcher'.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

