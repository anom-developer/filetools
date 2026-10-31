"""Terminal output, ANSI colors, and result formatting."""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import IO, List, Optional

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

# Enable VT100 on Windows console if available
if sys.platform == "win32":
    try:
        import colorama
        colorama.just_fix_windows_console()
    except Exception:
        os.system("")

from searcher.core import ContentMatch, SearchOptions, SearchResult


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
    s = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if s < 1024:
            return f"{s:.1f} {unit}"
        s /= 1024
    return f"{s:.1f} TB"


# ── Printer ────────────────────────────────────────────────────────────────────

class Printer:
    """
    Formats and prints search results to stdout (and optionally a plain-text or JSON file).
    """

    def __init__(
        self,
        *,
        use_color: bool = True,
        verbose: bool = False,
        output_file: Optional[Path] = None,
        as_json: bool = False,
        count_only: bool = False,
    ) -> None:
        self.use_color = use_color and sys.stdout.isatty() and not as_json
        self.verbose = verbose
        self.as_json = as_json
        self.count_only = count_only
        self.total = 0
        self._start = time.perf_counter()
        self._fh: Optional[IO[str]] = None
        self._json_records: List[dict] = []

        if output_file:
            self._fh = output_file.open("w", encoding="utf-8")

    # ── Public interface ───────────────────────────────────────────────────────

    def print_header(self, opts: SearchOptions) -> None:
        if self.as_json or self.count_only:
            return
        mode = "regex" if opts.use_regex else "mask"
        content_info = f", content='{opts.content_pattern}'" if opts.content_pattern else ""
        msg = (
            f"\n🔍  Searching for "
            f"{_fmt(repr(opts.pattern), _Color.BOLD, _Color.CYAN, use_color=self.use_color)} "
            f"({mode}{content_info}) in "
            f"{_fmt(str(opts.root), _Color.BOLD, use_color=self.use_color)} …\n"
        )
        self._print(msg, plain=f"Searching '{opts.pattern}' in {opts.root}\n")

    def print_result(self, result: SearchResult) -> None:
        self.total += 1

        if self.as_json:
            self._json_records.append({
                "path": str(result.path),
                "size": result.size,
                "modified": result.modified,
                "modified_iso": datetime.fromtimestamp(result.modified).isoformat(),
                "content_matches": [
                    {
                        "line_number": m.line_number,
                        "line": m.line,
                        "match_start": m.match_start,
                        "match_end": m.match_end,
                    }
                    for m in result.content_matches
                ],
            })
            return

        if self.count_only:
            return

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
            plain_line = f"  {path_str}  ({_human_size(result.size)}, {datetime.fromtimestamp(result.modified).strftime('%Y-%m-%d %H:%M')})"
        else:
            line = f"  📄 {colored_path}"
            plain_line = f"  {path_str}"

        self._print(line, plain=plain_line)

        # Content matches with context
        for m in result.content_matches:
            self._print_content_match(m)

    def print_footer(self, *, show_stats: bool = False) -> None:
        if self.as_json:
            json_text = json.dumps(self._json_records, ensure_ascii=False, indent=2)
            print(json_text)
            if self._fh:
                self._fh.write(json_text + "\n")
            return

        if self.count_only:
            print(str(self.total))
            if self._fh:
                self._fh.write(str(self.total) + "\n")
            return

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

    def _print_content_match(self, m: ContentMatch) -> None:
        """Print a highlighted content match line with optional context lines."""
        # Context before
        for ctx_no, ctx_line in m.context_before:
            ctx_no_str = _fmt(f"L{ctx_no:<5}", _Color.DIM, use_color=self.use_color)
            ctx_colored = _fmt(f"  |  {ctx_line}", _Color.DIM, use_color=self.use_color)
            self._print(f"      {ctx_no_str}{ctx_colored}", plain=f"      L{ctx_no} | {ctx_line}")

        # The matched line
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

        # Context after
        for ctx_no, ctx_line in m.context_after:
            ctx_no_str = _fmt(f"L{ctx_no:<5}", _Color.DIM, use_color=self.use_color)
            ctx_colored = _fmt(f"  |  {ctx_line}", _Color.DIM, use_color=self.use_color)
            self._print(f"      {ctx_no_str}{ctx_colored}", plain=f"      L{ctx_no} | {ctx_line}")

    def _print(self, colored: str, *, plain: Optional[str] = None) -> None:
        """Print to stdout safely and optionally to the plain-text file."""
        try:
            print(colored)
        except UnicodeEncodeError:
            safe = (plain or colored).encode("ascii", "replace").decode("ascii")
            print(safe)

        if self._fh:
            self._fh.write((plain or colored) + "\n")
