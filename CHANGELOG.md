# Changelog

All notable changes to FileTools are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) · Versioning: [SemVer](https://semver.org/).

---

## [Unreleased]

---

## [0.1.0] — 2024-01-15

### Added

#### converter
- PNG ↔ JPG / JPEG image conversion via Pillow
- PNG / JPG → WebP, WebP → PNG / JPG conversion
- Alpha-channel flattening when saving as JPEG (transparent → white background)
- TXT → PDF via fpdf2 with configurable `--font-size`
- JSON → CSV (root must be an array of objects; column order preserved)
- CSV → JSON round-trip
- Markdown → plain TXT (strips headings, bold, italic, links, code blocks)
- Batch directory conversion: `converter ./in/ ./out/ --format webp`
- `--quality` flag for lossy formats (JPEG, WebP)
- `--encoding` flag for all text-based conversions (default: utf-8)
- `--verbose` flag for per-file progress output

#### searcher
- File search by glob mask (`*.py`, `report_*.xlsx`)
- File search by regular expression (`--regex`)
- Recursive directory traversal via `os.walk`
- Content search inside files (`--content TEXT`)
- Extension filter (`--ext .py .txt`)
- Max recursion depth (`--depth N`)
- Case-insensitive mode (`--ignore-case`)
- ANSI color output with highlighted content matches
- Results export to plain-text file (`--output FILE`)
- Summary statistics (`--stats`): file count, elapsed time
- Non-zero exit code when no files are found (useful in shell scripts)

#### Infrastructure
- `pyproject.toml` packaging (PEP 517 / 518)
- `py.typed` markers for PEP 561 type checking support
- 35 automated tests (pytest)
- GitHub Actions CI matrix: Python 3.8 / 3.10 / 3.12
- GitHub Actions Release workflow: builds Linux / Windows / macOS binaries on tag push
- `install.bat` — Windows auto-installer (avoids Microsoft Store Python issues)
- `install.sh` — Linux / macOS auto-installer with optional PATH setup
- `create_release.sh` — publishes a GitHub Release via `gh` CLI

[Unreleased]: https://github.com/your-username/filetools/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-username/filetools/releases/tag/v0.1.0
