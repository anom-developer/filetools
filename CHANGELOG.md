# Changelog

All notable changes to FileTools are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) · Versioning: [SemVer](https://semver.org/).

---

## [1.0.0] — 2026-11-01

### Added
- **Unified CLI (`filetools`)**: All-in-one command with `filetools converter ...` and `filetools searcher ...` subcommands, `--version`, and interactive help.
- **Searcher enhancements**:
  - Context lines display (`-C N` / `--context N`) showing lines before and after content matches.
  - File size filtering (`--min-size` and `--max-size` with human units `500B`, `10KB`, `2MB`, `1GB`).
  - Modification time filtering (`--mtime -7d` for last 7 days, `+30d` for older than 30 days, `-24h`).
  - JSON output mode (`--json`) for automated pipelines and scripting.
  - Match count mode (`--count`) to quickly count matching files.
  - Glob exclusion filters (`--exclude PATTERN...`).
  - Automatic filtering of hidden and virtualenv directories (`.git`, `.venv`, `node_modules`, `__pycache__`) by default, with `-a` / `--hidden` option to include them.
  - Smart CLI argument parsing: allows searching with `--content "text" .` without requiring dummy pattern.
- **Converter enhancements**:
  - Full image conversion matrix supporting PNG, JPG, JPEG, WebP, BMP, GIF, TIFF, and ICO.
  - Multi-resolution Windows ICO icon creation with standard sizes (16, 32, 48, 64, 128, 256).
  - Image transformations: `--resize WIDTHxHEIGHT` or `PERCENT%`, `--rotate 90/180/270`, and `--grayscale`.
  - Recursive directory conversion (`-r`, `--recursive`) preserving directory hierarchy.
  - Overwrite control (`--no-overwrite`).
  - HTML to plain text conversion (`html_to_txt`) with entity decoding and formatting preservation.
  - Single JSON object conversion to CSV (automatic row wrapping).
  - Nested JSON object/array serialization in CSV export.
  - CSV delimiter auto-sniffing (comma, semicolon, tab, pipe).
  - CSV to JSON automatic type conversion (`--parse-types`).
- **Packaging & Distribution**:
  - Standalone compiled `.exe` binaries for Windows: `filetools.exe`, `converter.exe`, `searcher.exe`.
  - Ready-to-download `filetools-windows-x86_64.zip` release archive.
  - Updated GitHub Actions workflow building and publishing releases across Windows, Linux, and macOS.
  - Extended `install.bat` and `install.sh` supporting Python 3.8 through Python 3.14.

### Fixed
- **Windows Unicode Console Crash**: Resolved `UnicodeEncodeError` on non-UTF-8 Windows consoles (cp1251, cp866, etc.) by reconfiguring standard streams and adding graceful glyph fallbacks.
- **Searcher CLI Parameter Bug**: Fixed issue where `searcher --content "text" .` captured the dot directory as the filename mask.
- **PDF Unicode / Cyrillic Support**: Fixed `txt_to_pdf` crashing on Cyrillic/non-Latin text with automatic system TrueType font detection and fallback.
- **Markdown Header Regex**: Fixed multiline header stripping in `md_to_txt` by applying `re.M` flag.

### Removed
- Removed legacy repository URLs and account references.

---

## [0.1.0] — 2024-01-15

### Added
- Initial release with `converter` and `searcher` tools.
- Basic image and data conversions.
- Initial test suite and installation scripts.

[1.0.0]: https://github.com/anom-developer/filetools/releases/tag/v1.0.0
[0.1.0]: https://github.com/anom-developer/filetools/releases/tag/v0.1.0
