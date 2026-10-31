"""Tests for the converter module."""
import csv
import json
from pathlib import Path

import pytest

from converter.core import convert_file, convert_directory, SUPPORTED_CONVERSIONS
from converter.formats.data import json_to_csv, csv_to_json, md_to_txt, html_to_txt
from converter.formats.images import parse_resize


# ── Supported pairs ────────────────────────────────────────────────────────────

def test_supported_conversions_not_empty():
    assert len(SUPPORTED_CONVERSIONS) > 0


def test_supported_conversions_are_tuples():
    for pair in SUPPORTED_CONVERSIONS:
        assert isinstance(pair, tuple) and len(pair) == 2


# ── Data conversions ────────────────────────────────────────────────────────────

class TestJsonToCsv:
    def test_basic(self, sample_json, tmp_path):
        out = tmp_path / "out.csv"
        json_to_csv(sample_json, out)
        assert out.exists()
        rows = list(csv.DictReader(out.read_text(encoding="utf-8").splitlines()))
        assert len(rows) == 3
        assert rows[0]["name"] == "Alice"

    def test_single_object(self, tmp_path):
        src = tmp_path / "single.json"
        src.write_text(json.dumps({"name": "Alice", "role": "admin"}), encoding="utf-8")
        out = tmp_path / "out.csv"
        json_to_csv(src, out)
        assert out.exists()
        rows = list(csv.DictReader(out.read_text(encoding="utf-8").splitlines()))
        assert len(rows) == 1
        assert rows[0]["name"] == "Alice"
        assert rows[0]["role"] == "admin"

    def test_preserves_column_order(self, sample_json, tmp_path):
        out = tmp_path / "out.csv"
        json_to_csv(sample_json, out)
        header = out.read_text().splitlines()[0]
        assert header == "name,age,city"

    def test_empty_array(self, tmp_path):
        src = tmp_path / "empty.json"
        src.write_text("[]", encoding="utf-8")
        out = tmp_path / "out.csv"
        json_to_csv(src, out)
        assert out.read_text() == ""

    def test_nested_json(self, tmp_path):
        src = tmp_path / "nested.json"
        src.write_text(json.dumps([{"id": 1, "meta": {"role": "dev"}}]), encoding="utf-8")
        out = tmp_path / "out.csv"
        json_to_csv(src, out)
        rows = list(csv.DictReader(out.read_text(encoding="utf-8").splitlines()))
        assert len(rows) == 1
        assert "role" in rows[0]["meta"]

    def test_non_array_or_dict_raises(self, tmp_path):
        src = tmp_path / "invalid.json"
        src.write_text('"just a string"', encoding="utf-8")
        out = tmp_path / "out.csv"
        with pytest.raises(ValueError, match="object or array"):
            json_to_csv(src, out)


class TestCsvToJson:
    def test_basic(self, sample_csv, tmp_path):
        out = tmp_path / "out.json"
        csv_to_json(sample_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "Alice"

    def test_parse_types(self, tmp_path):
        src = tmp_path / "typed.csv"
        src.write_text("name,age,active,score\nBob,25,true,98.5\n", encoding="utf-8")
        out = tmp_path / "out.json"
        csv_to_json(src, out, parse_types=True)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data[0]["name"] == "Bob"
        assert data[0]["age"] == 25
        assert data[0]["active"] is True
        assert data[0]["score"] == 98.5

    def test_semicolon_delimited_csv(self, tmp_path):
        src = tmp_path / "semi.csv"
        src.write_text("name;age\nAlice;30\nBob;25\n", encoding="utf-8")
        out = tmp_path / "out.json"
        csv_to_json(src, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) == 2
        assert data[0]["name"] == "Alice"

    def test_roundtrip(self, sample_json, tmp_path):
        csv_path = tmp_path / "mid.csv"
        json_out = tmp_path / "out.json"
        json_to_csv(sample_json, csv_path)
        csv_to_json(csv_path, json_out)
        result = json.loads(json_out.read_text())
        original = json.loads(sample_json.read_text())
        assert len(result) == len(original)
        assert result[0]["name"] == original[0]["name"]


class TestMdToTxt:
    def test_removes_headings_multiline(self, tmp_path):
        src = tmp_path / "headings.md"
        src.write_text("# First Header\nBody\n## Second Header\nMore body\n### Third Header", encoding="utf-8")
        out = tmp_path / "out.txt"
        md_to_txt(src, out)
        text = out.read_text(encoding="utf-8")
        assert "#" not in text
        assert "First Header" in text
        assert "Second Header" in text
        assert "Third Header" in text

    def test_removes_bold_and_italic(self, sample_md, tmp_path):
        out = tmp_path / "out.txt"
        md_to_txt(sample_md, out)
        text = out.read_text(encoding="utf-8")
        assert "**" not in text
        assert "*" not in text
        assert "bold" in text
        assert "italic" in text


class TestHtmlToTxt:
    def test_html_stripping(self, tmp_path):
        src = tmp_path / "doc.html"
        src.write_text(
            "<html><head><style>body {color: red;}</style></head>"
            "<body><h1>Title</h1><p>Hello &amp; welcome!<br>Second line.</p></body></html>",
            encoding="utf-8",
        )
        out = tmp_path / "out.txt"
        convert_file(src, out)
        text = out.read_text(encoding="utf-8")
        assert "<style>" not in text
        assert "Title" in text
        assert "Hello & welcome!" in text
        assert "Second line." in text


# ── TXT → PDF ──────────────────────────────────────────────────────────────────

class TestTxtToPdf:
    def test_creates_pdf(self, sample_txt, tmp_path):
        pytest.importorskip("fpdf")
        out = tmp_path / "out.pdf"
        convert_file(sample_txt, out)
        assert out.exists()
        assert out.stat().st_size > 0
        assert out.read_bytes()[:4] == b"%PDF"

    def test_unicode_cyrillic(self, tmp_path):
        pytest.importorskip("fpdf")
        src = tmp_path / "ru.txt"
        src.write_text("Заголовок на русском языке\nТекст с числами 123.\nСпецсимволы: © ® €", encoding="utf-8")
        out = tmp_path / "ru.pdf"
        convert_file(src, out)
        assert out.exists()
        assert out.stat().st_size > 0
        assert out.read_bytes()[:4] == b"%PDF"


# ── Image conversions ──────────────────────────────────────────────────────────

class TestImageConversion:
    @pytest.fixture()
    def tiny_png(self, tmp_path):
        PIL_Image = pytest.importorskip("PIL.Image")
        img = PIL_Image.new("RGB", (100, 100), color=(255, 0, 0))
        p = tmp_path / "test.png"
        img.save(p)
        return p

    def test_png_to_jpg(self, tiny_png, tmp_path):
        out = tmp_path / "out.jpg"
        convert_file(tiny_png, out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_png_to_webp(self, tiny_png, tmp_path):
        out = tmp_path / "out.webp"
        convert_file(tiny_png, out)
        assert out.exists()

    def test_png_to_ico(self, tiny_png, tmp_path):
        out = tmp_path / "favicon.ico"
        convert_file(tiny_png, out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_resize_and_rotate(self, tiny_png, tmp_path):
        PIL_Image = pytest.importorskip("PIL.Image")
        out = tmp_path / "resized.png"
        convert_file(tiny_png, out, resize="50x50", rotate=90, grayscale=True)
        assert out.exists()
        with PIL_Image.open(out) as img:
            assert img.size == (50, 50)
            assert img.mode in ("L", "RGB")

    def test_parse_resize(self):
        assert parse_resize("800x600", (1000, 1000)) == (800, 600)
        assert parse_resize("50%", (200, 100)) == (100, 50)
        with pytest.raises(ValueError):
            parse_resize("invalid", (100, 100))

    def test_unsupported_raises(self, sample_txt, tmp_path):
        out = tmp_path / "out.xyz"
        with pytest.raises(ValueError):
            convert_file(sample_txt, out)


# ── Directory conversion ────────────────────────────────────────────────────────

class TestConvertDirectory:
    def test_converts_multiple(self, tmp_path):
        PIL_Image = pytest.importorskip("PIL.Image")
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        for i in range(3):
            img = PIL_Image.new("RGB", (5, 5), color=(i * 80, 0, 0))
            img.save(src / f"img{i}.png")

        count = convert_directory(src, dst, "jpg")
        assert count == 3
        assert len(list(dst.glob("*.jpg"))) == 3

    def test_recursive_conversion(self, tmp_path):
        PIL_Image = pytest.importorskip("PIL.Image")
        src = tmp_path / "src"
        sub = src / "sub"
        sub.mkdir(parents=True)
        dst = tmp_path / "dst"

        img1 = PIL_Image.new("RGB", (5, 5), color=(255, 0, 0))
        img1.save(src / "top.png")
        img2 = PIL_Image.new("RGB", (5, 5), color=(0, 255, 0))
        img2.save(sub / "nested.png")

        count = convert_directory(src, dst, "jpg", recursive=True)
        assert count == 2
        assert (dst / "top.jpg").exists()
        assert (dst / "sub" / "nested.jpg").exists()

    def test_no_overwrite(self, tmp_path):
        PIL_Image = pytest.importorskip("PIL.Image")
        src = tmp_path / "src"
        src.mkdir()
        img = PIL_Image.new("RGB", (5, 5), color=(255, 0, 0))
        img.save(src / "test.png")

        dst = tmp_path / "dst"
        dst.mkdir()
        (dst / "test.jpg").write_text("existing content")

        convert_file(src / "test.png", dst / "test.jpg", overwrite=False)
        assert (dst / "test.jpg").read_text() == "existing content"

    def test_skips_unsupported(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "readme.txt").write_text("hi")  # txt→jpg not supported

        count = convert_directory(src, tmp_path / "dst", "jpg")
        assert count == 0
