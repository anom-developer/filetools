# FileTools v1.0.0 🎉

Official production release of **FileTools** — high-performance CLI toolkit for file conversion and lightning-fast recursive searching.

---

## ⬇️ Downloads & Release Assets

| Platform | File | Description |
|----------|------|-------------|
| 🖥️ Windows x86-64 | [`filetools-windows-x86_64.zip`](https://github.com/anom-developer/filetools/releases/download/v1.0.0/filetools-windows-x86_64.zip) | Standalone `.exe` applications (`filetools.exe`, `converter.exe`, `searcher.exe`) + `install.bat` |
| 🐧 Linux x86-64 | `filetools-linux-x86_64.tar.gz` | Standalone Linux binaries (no Python required) |
| 🍎 macOS x86-64 / ARM | `filetools-macos-x86_64.tar.gz` | Standalone macOS binaries |
| 📦 All platforms | [`filetools-source.zip`](https://github.com/anom-developer/filetools/releases/download/v1.0.0/filetools-source.zip) | Full source code with automated installer scripts |

---

## 🚀 Quick Start

### Windows (No installation needed)
1. Download [`filetools-windows-x86_64.zip`](https://github.com/anom-developer/filetools/releases/download/v1.0.0/filetools-windows-x86_64.zip)
2. Extract the archive.
3. Run directly from PowerShell or Command Prompt:
```cmd
filetools.exe --help
converter.exe photo.png photo.jpg --resize 800x600
searcher.exe --content "TODO" .\src -C 2
```

### From Python (pip)
```bash
pip install git+https://github.com/anom-developer/filetools.git
```

---

## ✨ What's New in v1.0.0

### 🔄 Converter
- **Image Formats**: Full matrix support for PNG, JPG, JPEG, WebP, BMP, GIF, TIFF, and Windows ICO.
- **Icon Generation**: Convert any image to multi-resolution `.ico` icon file with standard icon sizes.
- **Image Editing**: Added `--resize WIDTHxHEIGHT` (or `PERCENT%`), `--rotate 90/180/270`, and `--grayscale`.
- **Recursive Directory Mode**: Batch convert entire directory trees while preserving folder structure (`-r` / `--recursive`).
- **Documents & Data**:
  - TXT → PDF with full Unicode / Cyrillic font auto-discovery and word wrapping.
  - JSON ↔ CSV with support for single objects, nested structures, and auto-sniffed delimiters.
  - CSV → JSON with automatic type inference (`--parse-types`).
  - HTML → TXT stripping tags and decoding HTML entities.
  - Markdown → TXT with robust multi-line header stripping.

### 🔍 Searcher
- **Context Lines**: View matching context with `-C N` / `--context N` (lines before and after match).
- **Size Filtering**: Filter by `--min-size` and `--max-size` (e.g. `10KB`, `2MB`).
- **Time Filtering**: Filter by `--mtime` (e.g. `-7d` for last 7 days, `+30d` for older files).
- **JSON & Count**: Machine-readable JSON output (`--json`) and quick match counting (`--count`).
- **Smart Directory Traversal**: Automatically skips `.git`, `.venv`, and `node_modules` by default (use `-a` / `--hidden` to include).
- **Fixed Windows Encoding**: Reconfigured stdout/stderr to prevent cp1251/cp866 terminal crashes.

---

**Full changelog:** [CHANGELOG.md](https://github.com/anom-developer/filetools/blob/main/CHANGELOG.md)

