"""Tests for CLI entrypoints and output formatting."""
import json
import sys
from pathlib import Path

import pytest

from converter.cli import build_parser as build_converter_parser, main as converter_main
from searcher.cli import build_parser as build_searcher_parser, main as searcher_main
from filetools.cli import main as filetools_main
from searcher.output import Printer
from searcher.core import SearchOptions, SearchResult, ContentMatch


def test_filetools_cli_version(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filetools", "--version"])
    with pytest.raises(SystemExit) as excinfo:
        filetools_main()
    assert excinfo.value.code == 0
    assert "FileTools v" in capsys.readouterr().out


def test_filetools_cli_help(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filetools", "--help"])
    filetools_main()
    captured = capsys.readouterr().out
    assert "Modern high-performance converter & searcher" in captured


def test_filetools_cli_delegates_converter(tmp_path, capsys, monkeypatch):
    src = tmp_path / "in.json"
    src.write_text('[{"a": 1}]', encoding="utf-8")
    dst = tmp_path / "out.csv"
    monkeypatch.setattr(sys, "argv", ["filetools", "converter", str(src), str(dst)])
    filetools_main()
    assert dst.exists()


def test_converter_cli_help(capsys):
    parser = build_converter_parser()
    assert parser.prog == "converter"
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["--help"])
    assert excinfo.value.code == 0


def test_searcher_cli_help(capsys):
    parser = build_searcher_parser()
    assert parser.prog == "searcher"
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["--help"])
    assert excinfo.value.code == 0


def test_searcher_cli_content_only_execution(tmp_path, monkeypatch, capsys):
    f = tmp_path / "hello.py"
    f.write_text("print('needle')\n", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["searcher", "--content", "needle", str(tmp_path)])
    searcher_main()
    captured = capsys.readouterr().out
    assert "hello.py" in captured
    assert "needle" in captured


def test_searcher_cli_json_mode(tmp_path, monkeypatch, capsys):
    f = tmp_path / "data.txt"
    f.write_text("test data\n", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["searcher", "*.txt", str(tmp_path), "--json"])
    searcher_main()
    captured = capsys.readouterr().out
    records = json.loads(captured)
    assert len(records) == 1
    assert "data.txt" in records[0]["path"]


def test_searcher_cli_count_mode(tmp_path, monkeypatch, capsys):
    (tmp_path / "f1.txt").write_text("a")
    (tmp_path / "f2.txt").write_text("b")

    monkeypatch.setattr(sys, "argv", ["searcher", "*.txt", str(tmp_path), "--count"])
    searcher_main()
    captured = capsys.readouterr().out.strip()
    assert captured == "2"


def test_converter_cli_single_file(tmp_path, monkeypatch, capsys):
    src = tmp_path / "data.json"
    src.write_text('[{"id": 1, "val": "x"}]', encoding="utf-8")
    dst = tmp_path / "data.csv"

    monkeypatch.setattr(sys, "argv", ["converter", str(src), str(dst)])
    converter_main()
    captured = capsys.readouterr().out
    assert "Saved:" in captured
    assert dst.exists()


def test_printer_file_output(tmp_path):
    out_file = tmp_path / "report.txt"
    printer = Printer(use_color=False, verbose=True, output_file=out_file)

    opts = SearchOptions(pattern="*.py", root=tmp_path)
    printer.print_header(opts)

    sample_res = SearchResult(
        path=tmp_path / "test.py",
        size=1024,
        modified=1700000000.0,
        content_matches=[
            ContentMatch(
                line_number=5,
                line="foo()",
                match_start=0,
                match_end=3,
                context_before=[(4, "# comment")],
                context_after=[(6, "bar()")],
            )
        ],
    )
    printer.print_result(sample_res)
    printer.print_footer(show_stats=True)
    printer.close()

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "test.py" in content
    assert "foo()" in content
    assert "Found: 1 file" in content
