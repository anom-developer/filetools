"""Tests for the converter module."""
import csv
import json
from pathlib import Path

import pytest

from converter.core import convert_file, convert_directory, SUPPORTED_CONVERSIONS
from converter.formats.data import json_to_csv, csv_to_json, md_to_txt


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

    def test_non_array_raises(self, tmp_path):
        src = tmp_path / "obj.json"
        src.write_text('{"key": "value"}', encoding="utf-8")
        out = tmp_path / "out.csv"
        with pytest.raises(ValueError, match="array"):
            json_to_csv(src, out)


class TestCsvToJson:
    def test_basic(self, sample_csv, tmp_path):
        out = tmp_path / "out.json"
        csv_to_json(sample_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data, list)
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
    def test_removes_headings(self, sample_md, tmp_path):
        out = tmp_path / "out.txt"
        md_to_txt(sample_md, out)
        text = out.read_text(encoding="utf-8")
        assert "# " not in text
        assert "Title" in text

    def test_removes_bold(self, sample_md, tmp_path):
        out = tmp_path / "out.txt"
        md_to_txt(sample_md, out)
        text = out.read_text(encoding="utf-8")
        assert "**" not in text
        assert "bold" in text


# ── TXT → PDF ──────────────────────────────────────────────────────────────────

class TestTxtToPdf:
    def test_creates_pdf(self, sample_txt, tmp_path):
        pytest.importorskip("fpdf")
        out = tmp_path / "out.pdf"
        convert_file(sample_txt, out)
        assert out.exists()
        assert out.stat().st_size > 0
        # PDF magic bytes
        assert out.read_bytes()[:4] == b"%PDF"


# ── Image conversions ──────────────────────────────────────────────────────────

class TestImageConversion:
    @pytest.fixture()
    def tiny_png(self, tmp_path):
        PIL_Image = pytest.importorskip("PIL.Image")
        img = PIL_Image.new("RGB", (10, 10), color=(255, 0, 0))
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

    def test_skips_unsupported(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "readme.txt").write_text("hi")  # txt→jpg not supported

        count = convert_directory(src, tmp_path / "dst", "jpg")
        assert count == 0
