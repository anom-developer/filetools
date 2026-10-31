"""Terminal output, ANSI colors, and result formatting."""
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import IO, Optional

from searcher.core import SearchOptions, SearchResult


# ── ANSI colours ──────────────────────────────────────────────────────────────

class _Color:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    CYAN    = "\033[36m"
    MAGENTA = "\033[35m"
    RED     = "\033[31m"
    WHITE   = "\033[37m"


def _fmt(text: str, *codes: str, use_color: bool = True) -> str:
    if not use_color:
        return text
    return "".join(codes) + text + _Color.RESET


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024  # type: ignore[assignment]
    return f"{size:.1f} TB"


# ── Printer ────────────────────────────────────────────────────────────────────

class Printer:
    """
    Formats and prints search results to stdout (and optionally a plain-text file).
    """

    def __init__(
        self,
        *,
        use_color: bool = True,
        verbose: bool = False,
        output_file: Optional[Path] = None,
    ) -> None:
        self.use_color = use_color and sys.stdout.isatty()
        self.verbose = verbose
        self.total = 0
        self._start = time.perf_counter()
        self._fh: Optional[IO[str]] = None

        if output_file:
            self._fh = output_file.open("w", encoding="utf-8")

    # ── Public interface ───────────────────────────────────────────────────────

    def print_header(self, opts: SearchOptions) -> None:
        mode = "regex" if opts.use_regex else "mask"
        msg = (
            f"\n🔍  Searching for "
            f"{_fmt(repr(opts.pattern), _Color.BOLD, _Color.CYAN, use_color=self.use_color)} "
            f"({mode}) in "
            f"{_fmt(str(opts.root), _Color.BOLD, use_color=self.use_color)} …\n"
        )
        self._print(msg, plain=f"Searching '{opts.pattern}' in {opts.root}\n")

    def print_result(self, result: SearchResult) -> None:
        self.total += 1

        path_str = str(result.path)
        colored_path = _fmt(path_str, _Color.GREEN, use_color=self.use_color)

        if self.verbose:
            size_str = _fmt(_human_size(result.size), _Color.DIM, use_color=self.use_color)
            date_str = _fmt(
                datetime.fromtimestamp(result.modified).strftime("%Y-%m-%d %H:%M"),
                _Color.DIM,
                use_color=self.use_color,
            )
            line = f"  📄 {colored_path:<60}  {size_str:<12}  {date_str}"
            plain_line = f"  {path_str}  ({_human_size(result.size)}, {datetime.fromtimestamp(result.modified).strftime('%Y-%m-%d')})"
        else:
            line = f"  📄 {colored_path}"
            plain_line = f"  {path_str}"

        self._print(line, plain=plain_line)

        # Content matches
        for m in result.content_matches:
            self._print_content_match(m)

    def print_footer(self, *, show_stats: bool = False) -> None:
        elapsed = time.perf_counter() - self._start
        sep = _fmt("  " + "─" * 50, _Color.DIM, use_color=self.use_color)
        self._print(f"\n{sep}")

        count_str = _fmt(str(self.total), _Color.BOLD, _Color.YELLOW, use_color=self.use_color)
        time_str  = _fmt(f"{elapsed:.3f}s", _Color.DIM, use_color=self.use_color)
        msg = f"  Found: {count_str} file(s) in {time_str}\n"
        self._print(msg, plain=f"  Found: {self.total} file(s) in {elapsed:.3f}s\n")

        if show_stats and self.total == 0:
            self._print("  No files matched the search criteria.\n")

    def close(self) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None

    # ── Internals ─────────────────────────────────────────────────────────────

    def _print_content_match(self, m) -> None:
        """Print a highlighted content match line."""
        before = m.line[: m.match_start]
        match  = m.line[m.match_start : m.match_end]
        after  = m.line[m.match_end :]

        highlighted = (
            _fmt(before, _Color.DIM, use_color=self.use_color)
            + _fmt(match, _Color.BOLD, _Color.MAGENTA, use_color=self.use_color)
            + _fmt(after, _Color.DIM, use_color=self.use_color)
        )
        lineno_str = _fmt(f"L{m.line_number:<5}", _Color.CYAN, use_color=self.use_color)
        self._print(
            f"      {lineno_str}  {highlighted}",
            plain=f"      L{m.line_number}: {m.line}",
        )

    def _print(self, colored: str, *, plain: Optional[str] = None) -> None:
        """Print to stdout (with color) and optionally to the plain-text file."""
        print(colored)
        if self._fh:
            self._fh.write((plain or colored) + "\n")
