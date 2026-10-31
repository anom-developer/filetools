"""Shared pytest fixtures."""
import json
import os
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    """Return a fresh temporary directory."""
    return tmp_path


@pytest.fixture()
def sample_json(tmp_path: Path) -> Path:
    data = [
        {"name": "Alice", "age": 30, "city": "Paris"},
        {"name": "Bob",   "age": 25, "city": "Lyon"},
        {"name": "Carol", "age": 35, "city": "Nice"},
    ]
    p = tmp_path / "sample.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


@pytest.fixture()
def sample_csv(tmp_path: Path) -> Path:
    csv_text = "name,age,city\nAlice,30,Paris\nBob,25,Lyon\n"
    p = tmp_path / "sample.csv"
    p.write_text(csv_text, encoding="utf-8")
    return p


@pytest.fixture()
def sample_txt(tmp_path: Path) -> Path:
    p = tmp_path / "sample.txt"
    p.write_text("Hello, world!\nSecond line.\nThird line.", encoding="utf-8")
    return p


@pytest.fixture()
def sample_md(tmp_path: Path) -> Path:
    p = tmp_path / "sample.md"
    p.write_text(
        "# Title\n\nSome **bold** and *italic* text.\n\n- item one\n- item two\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture()
def file_tree(tmp_path: Path) -> Path:
    """
    Creates a directory tree for searcher tests:

    tmp/
      a.py
      b.txt
      notes.md
      sub/
        c.py
        d.log
        deep/
          e.py
    """
    (tmp_path / "a.py").write_text("x = 1\n# TODO: fix this\n")
    (tmp_path / "b.txt").write_text("hello world")
    (tmp_path / "notes.md").write_text("# Notes\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.py").write_text("def foo(): pass\n")
    (sub / "d.log").write_text("error occurred")
    deep = sub / "deep"
    deep.mkdir()
    (deep / "e.py").write_text("# TODO: refactor\nprint('hi')\n")
    return tmp_path
