"""Core file search logic."""
import fnmatch
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, List, Optional, Tuple


@dataclass
class SearchOptions:
    pattern: str = "*"
    root: Path = field(default_factory=lambda: Path("."))
    use_regex: bool = False
    content_pattern: Optional[str] = None
    extensions: Optional[List[str]] = None  # e.g. ['.py', '.txt']
    max_depth: Optional[int] = None
    ignore_case: bool = False
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    modified_after: Optional[float] = None
    modified_before: Optional[float] = None
    exclude: Optional[List[str]] = None
    include_hidden: bool = False
    context_lines: int = 0


@dataclass
class ContentMatch:
    line_number: int
    line: str
    match_start: int
    match_end: int
    context_before: List[Tuple[int, str]] = field(default_factory=list)  # (lineno, line)
    context_after: List[Tuple[int, str]] = field(default_factory=list)   # (lineno, line)


@dataclass
class SearchResult:
    path: Path
    size: int
    modified: float
    content_matches: List[ContentMatch] = field(default_factory=list)


def parse_size(size_str: str) -> int:
    """Parse size string like '500B', '10KB', '5MB', '1GB' into bytes."""
    s = size_str.strip().upper()
    units = {
        "B": 1,
        "KB": 1024,
        "K": 1024,
        "MB": 1024**2,
        "M": 1024**2,
        "GB": 1024**3,
        "G": 1024**3,
        "TB": 1024**4,
    }
    for unit, mult in sorted(units.items(), key=lambda x: -len(x[0])):
        if s.endswith(unit):
            try:
                num = float(s[:-len(unit)].strip())
                return int(num * mult)
            except ValueError as exc:
                raise ValueError(f"Invalid size value: '{size_str}'") from exc
    try:
        return int(s)
    except ValueError as exc:
        raise ValueError(f"Invalid size format: '{size_str}'") from exc


def parse_relative_time(time_str: str) -> float:
    """
    Parse time relative to now.
    e.g. '-7d' (within last 7 days), '+30d' (older than 30 days), '-24h', '-60m'.
    Returns timestamp threshold.
    """
    s = time_str.strip()
    sign = 1
    if s.startswith("-"):
        sign = -1
        s = s[1:]
    elif s.startswith("+"):
        sign = 1
        s = s[1:]

    unit_multipliers = {
        "d": 86400,
        "day": 86400,
        "days": 86400,
        "h": 3600,
        "hour": 3600,
        "hours": 3600,
        "m": 60,
        "min": 60,
        "mins": 60,
        "s": 1,
        "sec": 1,
    }

    unit = "d"
    for u in sorted(unit_multipliers.keys(), key=lambda x: -len(x)):
        if s.endswith(u):
            unit = u
            s = s[:-len(u)]
            break

    try:
        val = float(s)
    except ValueError as exc:
        raise ValueError(f"Invalid time format: '{time_str}'. Expected e.g. -7d, +24h") from exc

    delta = val * unit_multipliers[unit]
    now = time.time()
    # If -7d: modified in last 7 days (>= now - delta)
    # If +7d: modified older than 7 days (<= now - delta)
    return now - delta if sign < 0 else now - delta


def _compile_pattern(opts: SearchOptions) -> re.Pattern:
    """Return a compiled regex for the *filename* pattern."""
    flags = re.IGNORECASE if opts.ignore_case else 0
    if opts.use_regex:
        return re.compile(opts.pattern, flags)
    # Glob → regex
    return re.compile(fnmatch.translate(opts.pattern), flags)


def _compile_content(opts: SearchOptions) -> Optional[re.Pattern]:
    if not opts.content_pattern:
        return None
    flags = re.IGNORECASE if opts.ignore_case else 0
    return re.compile(opts.content_pattern, flags)


def _matches_extension(path: Path, extensions: Optional[List[str]]) -> bool:
    if not extensions:
        return True
    return path.suffix.lower() in {e.lower() for e in extensions}


def _is_excluded(name: str, path_str: str, exclude_patterns: Optional[List[str]]) -> bool:
    if not exclude_patterns:
        return False
    for pat in exclude_patterns:
        if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(path_str, pat):
            return True
    return False


def _search_content(path: Path, content_re: re.Pattern, context_lines: int = 0) -> List[ContentMatch]:
    """Search inside file for regex matches with optional context lines."""
    matches: List[ContentMatch] = []
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            lines = [line.rstrip("\r\n") for line in fh]

        for lineno_zero, line in enumerate(lines):
            found_iter = list(content_re.finditer(line))
            if not found_iter:
                continue

            # Capture context
            ctx_before: List[Tuple[int, str]] = []
            if context_lines > 0:
                start_ctx = max(0, lineno_zero - context_lines)
                for c_idx in range(start_ctx, lineno_zero):
                    ctx_before.append((c_idx + 1, lines[c_idx]))

            ctx_after: List[Tuple[int, str]] = []
            if context_lines > 0:
                end_ctx = min(len(lines), lineno_zero + 1 + context_lines)
                for c_idx in range(lineno_zero + 1, end_ctx):
                    ctx_after.append((c_idx + 1, lines[c_idx]))

            for m in found_iter:
                matches.append(
                    ContentMatch(
                        line_number=lineno_zero + 1,
                        line=line,
                        match_start=m.start(),
                        match_end=m.end(),
                        context_before=ctx_before,
                        context_after=ctx_after,
                    )
                )
    except (OSError, PermissionError):
        pass
    return matches


_DEFAULT_IGNORED_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".tox", ".idea", ".vscode"}


def search(opts: SearchOptions) -> Generator[SearchResult, None, None]:
    """
    Walk *opts.root* and yield :class:`SearchResult` for every matching file.
    """
    name_re = _compile_pattern(opts)
    content_re = _compile_content(opts)

    root_depth = len(opts.root.parts)

    for dirpath, dirnames, filenames in os.walk(opts.root, followlinks=False):
        current = Path(dirpath)

        # Filter out hidden or default-ignored directories unless include_hidden is requested
        if not opts.include_hidden:
            dirnames[:] = [
                d for d in dirnames
                if not d.startswith(".") and d not in _DEFAULT_IGNORED_DIRS
            ]

        # Filter excluded directories
        if opts.exclude:
            dirnames[:] = [
                d for d in dirnames
                if not _is_excluded(d, str(current / d), opts.exclude)
            ]

        # Depth limiting: prune subdirectories in-place
        if opts.max_depth is not None:
            current_depth = len(current.parts) - root_depth
            if current_depth >= opts.max_depth:
                dirnames.clear()

        # Sort for deterministic output
        dirnames.sort()

        for filename in sorted(filenames):
            if not opts.include_hidden and filename.startswith("."):
                continue

            file_path = current / filename
            rel_str = str(file_path)

            if _is_excluded(filename, rel_str, opts.exclude):
                continue

            # 1. Filename pattern match
            if not name_re.search(filename):
                continue

            # 2. Extension filter
            if not _matches_extension(file_path, opts.extensions):
                continue

            # 3. File stat & size/time filters
            try:
                stat = file_path.stat()
                size = stat.st_size
                modified = stat.st_mtime
            except OSError:
                size = 0
                modified = time.time()

            if opts.min_size is not None and size < opts.min_size:
                continue
            if opts.max_size is not None and size > opts.max_size:
                continue
            if opts.modified_after is not None and modified < opts.modified_after:
                continue
            if opts.modified_before is not None and modified > opts.modified_before:
                continue

            # 4. Content search (optional)
            content_matches: List[ContentMatch] = []
            if content_re is not None:
                content_matches = _search_content(file_path, content_re, opts.context_lines)
                if not content_matches:
                    continue  # content pattern required but not found

            yield SearchResult(
                path=file_path,
                size=size,
                modified=modified,
                content_matches=content_matches,
            )
