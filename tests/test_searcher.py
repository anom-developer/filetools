"""Tests for the searcher module."""
import time
from pathlib import Path

import pytest

from searcher.core import SearchOptions, parse_relative_time, parse_size, search


def collect(opts: SearchOptions):
    """Helper: return list of result paths."""
    return [r.path for r in search(opts)]


# ── Glob mask ──────────────────────────────────────────────────────────────────

class TestGlobSearch:
    def test_finds_py_files(self, file_tree):
        opts = SearchOptions(pattern="*.py", root=file_tree)
        results = collect(opts)
        names = {p.name for p in results}
        assert names == {"a.py", "c.py", "e.py"}

    def test_finds_txt_files(self, file_tree):
        opts = SearchOptions(pattern="*.txt", root=file_tree)
        results = collect(opts)
        assert len(results) == 1
        assert results[0].name == "b.txt"

    def test_no_match_returns_empty(self, file_tree):
        opts = SearchOptions(pattern="*.xyz", root=file_tree)
        assert collect(opts) == []

    def test_star_matches_all(self, file_tree):
        opts = SearchOptions(pattern="*", root=file_tree)
        results = collect(opts)
        assert len(results) >= 6  # all files in tree


# ── Regex mode ─────────────────────────────────────────────────────────────────

class TestRegexSearch:
    def test_regex_pattern(self, file_tree):
        opts = SearchOptions(pattern=r"[a-c]\.py", root=file_tree, use_regex=True)
        results = collect(opts)
        names = {p.name for p in results}
        assert "a.py" in names
        assert "c.py" in names
        assert "e.py" not in names

    def test_regex_log_files(self, file_tree):
        opts = SearchOptions(pattern=r".*\.log$", root=file_tree, use_regex=True)
        results = collect(opts)
        assert len(results) == 1
        assert results[0].name == "d.log"


# ── Depth limit ────────────────────────────────────────────────────────────────

class TestDepthLimit:
    def test_depth_0_top_only(self, file_tree):
        opts = SearchOptions(pattern="*.py", root=file_tree, max_depth=0)
        results = collect(opts)
        assert all(p.parent == file_tree for p in results)

    def test_depth_1_includes_sub(self, file_tree):
        opts = SearchOptions(pattern="*.py", root=file_tree, max_depth=1)
        names = {p.name for p in collect(opts)}
        assert "a.py" in names
        assert "c.py" in names
        # e.py is 2 levels deep → excluded
        assert "e.py" not in names

    def test_no_depth_limit(self, file_tree):
        opts = SearchOptions(pattern="*.py", root=file_tree)
        assert len(collect(opts)) == 3


# ── Extension filter ───────────────────────────────────────────────────────────

class TestExtensionFilter:
    def test_ext_filter_py(self, file_tree):
        opts = SearchOptions(pattern="*", root=file_tree, extensions=[".py"])
        names = {p.name for p in collect(opts)}
        assert all(n.endswith(".py") for n in names)

    def test_ext_filter_multiple(self, file_tree):
        opts = SearchOptions(pattern="*", root=file_tree, extensions=[".py", ".txt"])
        names = {p.name for p in collect(opts)}
        assert "d.log" not in names
        assert "a.py" in names
        assert "b.txt" in names


# ── Case-insensitive ───────────────────────────────────────────────────────────

class TestCaseInsensitive:
    def test_case_insensitive_glob(self, tmp_path):
        (tmp_path / "README.TXT").write_text("hi")
        opts = SearchOptions(pattern="*.txt", root=tmp_path, ignore_case=True)
        assert len(collect(opts)) == 1

    def test_case_sensitive_misses(self, tmp_path):
        (tmp_path / "README.TXT").write_text("hi")
        opts = SearchOptions(pattern="*.txt", root=tmp_path, ignore_case=False)
        assert len(collect(opts)) == 0


# ── Content search ─────────────────────────────────────────────────────────────

class TestContentSearch:
    def test_finds_todo(self, file_tree):
        opts = SearchOptions(
            pattern="*.py",
            root=file_tree,
            content_pattern="TODO",
        )
        results = list(search(opts))
        paths = {r.path.name for r in results}
        assert "a.py" in paths
        assert "e.py" in paths
        assert "c.py" not in paths

    def test_content_match_has_line_info(self, file_tree):
        opts = SearchOptions(
            pattern="*.py",
            root=file_tree,
            content_pattern="TODO",
        )
        results = list(search(opts))
        for r in results:
            assert len(r.content_matches) >= 1
            for m in r.content_matches:
                assert m.line_number >= 1
                assert "TODO" in m.line

    def test_content_context_lines(self, tmp_path):
        test_file = tmp_path / "context.txt"
        test_file.write_text("line 1\nline 2\nTARGET LINE\nline 4\nline 5\n")
        opts = SearchOptions(
            pattern="*.txt",
            root=tmp_path,
            content_pattern="TARGET",
            context_lines=2,
        )
        results = list(search(opts))
        assert len(results) == 1
        match = results[0].content_matches[0]
        assert len(match.context_before) == 2
        assert match.context_before[0][1] == "line 1"
        assert match.context_before[1][1] == "line 2"
        assert len(match.context_after) == 2
        assert match.context_after[0][1] == "line 4"
        assert match.context_after[1][1] == "line 5"

    def test_content_case_insensitive(self, file_tree):
        opts = SearchOptions(
            pattern="*.py",
            root=file_tree,
            content_pattern="todo",
            ignore_case=True,
        )
        results = list(search(opts))
        assert len(results) >= 1

    def test_no_content_match_excluded(self, file_tree):
        opts = SearchOptions(
            pattern="*.py",
            root=file_tree,
            content_pattern="XYZNOTFOUND",
        )
        assert list(search(opts)) == []


# ── Filters: Size, Time, Exclude, Hidden ───────────────────────────────────────

class TestAdvancedFilters:
    def test_parse_size(self):
        assert parse_size("500B") == 500
        assert parse_size("10KB") == 10 * 1024
        assert parse_size("2MB") == 2 * 1024 * 1024
        assert parse_size("1GB") == 1024**3
        with pytest.raises(ValueError):
            parse_size("invalid")

    def test_size_filter(self, tmp_path):
        (tmp_path / "small.txt").write_text("a" * 10)
        (tmp_path / "medium.txt").write_text("b" * 100)
        (tmp_path / "large.txt").write_text("c" * 1000)

        opts_min = SearchOptions(pattern="*.txt", root=tmp_path, min_size=50)
        names_min = {p.name for p in collect(opts_min)}
        assert names_min == {"medium.txt", "large.txt"}

        opts_max = SearchOptions(pattern="*.txt", root=tmp_path, max_size=50)
        names_max = {p.name for p in collect(opts_max)}
        assert names_max == {"small.txt"}

    def test_parse_relative_time(self):
        t1 = parse_relative_time("-7d")
        assert t1 < time.time()
        t2 = parse_relative_time("+24h")
        assert t2 < time.time()

    def test_exclude_patterns(self, file_tree):
        opts = SearchOptions(pattern="*.py", root=file_tree, exclude=["*sub*"])
        names = {p.name for p in collect(opts)}
        assert names == {"a.py"}  # c.py and e.py are under sub/

    def test_hidden_and_venv_ignored_by_default(self, tmp_path):
        (tmp_path / "visible.py").write_text("x = 1")
        hidden_dir = tmp_path / ".venv"
        hidden_dir.mkdir()
        (hidden_dir / "lib.py").write_text("y = 2")
        (tmp_path / ".hidden.py").write_text("z = 3")

        opts_default = SearchOptions(pattern="*.py", root=tmp_path)
        names_default = {p.name for p in collect(opts_default)}
        assert names_default == {"visible.py"}

        opts_all = SearchOptions(pattern="*.py", root=tmp_path, include_hidden=True)
        names_all = {p.name for p in collect(opts_all)}
        assert names_all == {"visible.py", "lib.py", ".hidden.py"}


# ── Result metadata ────────────────────────────────────────────────────────────

class TestResultMetadata:
    def test_has_size(self, file_tree):
        opts = SearchOptions(pattern="*.py", root=file_tree)
        for r in search(opts):
            assert r.size >= 0

    def test_has_modified(self, file_tree):
        opts = SearchOptions(pattern="*.py", root=file_tree)
        for r in search(opts):
            assert r.modified > 0
