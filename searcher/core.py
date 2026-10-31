"""Core file search logic."""
import fnmatch
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, List, Optional


@dataclass
class SearchOptions:
    pattern: str
    root: Path
    use_regex: bool = False
    content_pattern: Optional[str] = None
    extensions: Optional[List[str]] = None  # e.g. ['.py', '.txt']
    max_depth: Optional[int] = None
    ignore_case: bool = False


@dataclass
class ContentMatch:
    line_number: int
    line: str
    match_start: int
    match_end: int


@dataclass
class SearchResult:
    path: Path
    size: int
    modified: float
    content_matches: List[ContentMatch] = field(default_factory=list)


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


def _search_content(path: Path, content_re: re.Pattern) -> List[ContentMatch]:
    """Search inside file for regex matches. Returns list of matching lines."""
    matches: List[ContentMatch] = []
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, start=1):
                stripped = line.rstrip("\n")
                for m in content_re.finditer(stripped):
                    matches.append(
                        ContentMatch(
                            line_number=lineno,
                            line=stripped,
                            match_start=m.start(),
                            match_end=m.end(),
                        )
                    )
    except (OSError, PermissionError):
        pass
    return matches


def search(opts: SearchOptions) -> Generator[SearchResult, None, None]:
    """
    Walk *opts.root* and yield :class:`SearchResult` for every matching file.
    """
    name_re = _compile_pattern(opts)
    content_re = _compile_content(opts)

    root_depth = len(opts.root.parts)

    for dirpath, dirnames, filenames in os.walk(opts.root, followlinks=False):
        current = Path(dirpath)

        # Depth limiting: prune subdirectories in-place
        if opts.max_depth is not None:
            current_depth = len(current.parts) - root_depth
            if current_depth >= opts.max_depth:
                dirnames.clear()

        # Sort for deterministic output
        dirnames.sort()

        for filename in sorted(filenames):
            file_path = current / filename

            # 1. Filename pattern match
            if not name_re.search(filename):
                continue

            # 2. Extension filter
            if not _matches_extension(file_path, opts.extensions):
                continue

            # 3. Content search (optional)
            content_matches: List[ContentMatch] = []
            if content_re is not None:
                content_matches = _search_content(file_path, content_re)
                if not content_matches:
                    continue  # content pattern required but not found

            try:
                stat = file_path.stat()
                size = stat.st_size
                modified = stat.st_mtime
            except OSError:
                size = 0
                modified = time.time()

            yield SearchResult(
                path=file_path,
                size=size,
                modified=modified,
                content_matches=content_matches,
            )
