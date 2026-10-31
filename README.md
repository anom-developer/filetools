# 🛠️ filetools

[![CI](https://github.com/AceAnomDev/filetools/actions/workflows/ci.yml/badge.svg)](https://github.com/AceAnomDev/filetools/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/AceAnomDev/filetools)](https://github.com/AceAnomDev/filetools/releases/latest)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A command-line toolkit with two utilities:

| Tool | What it does |
|------|-------------|
| `converter` | Converts files between formats: PNG↔JPG, TXT→PDF, JSON↔CSV and more |
| `searcher` | Searches files by glob mask or regex with content search and color output |

---

## ⬇️ Installation

### Option 1 — Download binary (no Python needed)

Go to [Releases](https://github.com/AceAnomDev/filetools/releases/latest) and download for your platform:

| Platform | File |
|----------|------|
| 🐧 Linux | `filetools-linux-x86_64.tar.gz` |
| 🖥️ Windows | `filetools-windows-x86_64.zip` |
| 🍎 macOS | `filetools-macos-x86_64.tar.gz` |

```bash
# Linux / macOS
tar -xzf filetools-linux-x86_64.tar.gz
./converter --help
./searcher --help
```

```
# Windows — extract zip, then:
converter.exe --help
searcher.exe  --help
```

### Option 2 — Installer script (Python required)

```bash
# Windows — double-click or run in cmd:
install.bat

# Linux / macOS:
bash install.sh
```

### Option 3 — pip

```bash
# From GitHub:
pip install git+https://github.com/your-username/filetools.git

# From source:
git clone https://github.com/your-username/filetools.git
cd filetools
pip install -e .
```

---

## 🔄 Converter

### Supported conversions

| From | To |
|------|----|
| PNG  | JPG / JPEG / WebP |
| JPG / JPEG | PNG / WebP |
| WebP | PNG / JPG |
| TXT  | PDF |
| JSON | CSV |
| CSV  | JSON |
| MD   | TXT |

### Usage

```bash
# Single file
converter input.png output.jpg
converter data.json data.csv
converter notes.txt notes.pdf

# Whole directory
converter ./images/ ./output/ --format webp

# Options
converter photo.png photo.jpg --quality 85
converter report.txt report.pdf --font-size 14
converter data.csv data.json --encoding utf-8
```

### Options

```
positional:
  input               Input file or directory
  output              Output file or directory

optional:
  -f, --format        Target format for directory conversion (jpg, png, webp…)
  -q, --quality       Image quality 1-100 (default: 90)
  --font-size N       Font size for TXT→PDF (default: 12)
  --encoding ENC      Text encoding (default: utf-8)
  -v, --verbose       Show per-file progress
  -h, --help          Show this help
```

---

## 🔍 Searcher

### Usage

```bash
# By glob mask
searcher "*.py" ./src

# By regex
searcher --regex "report_\d{4}\.pdf" ./documents

# Search inside file contents
searcher --content "TODO" . --ext .py

# Limit recursion depth
searcher "*.log" /var/log --depth 2

# Case-insensitive + save results to file
searcher "*.txt" . --ignore-case --output results.txt

# Verbose with stats
searcher "*.json" . --verbose --stats
```

### Options

```
positional:
  pattern             Glob mask or regex pattern
  path                Directory to search (default: .)

optional:
  -r, --regex         Treat pattern as regular expression
  -c, --content TEXT  Search inside file contents
  -e, --ext EXT…      Filter by extension(s): --ext .py .txt
  -d, --depth N       Max recursion depth (default: unlimited)
  -i, --ignore-case   Case-insensitive matching
  --no-color          Disable ANSI colors
  -o, --output FILE   Save results to file
  -v, --verbose       Show file size and modification date
  -s, --stats         Print summary statistics
  -h, --help          Show this help
```

### Output example

```
🔍  Searching for '*.py' (mask) in ./project …

  📄 ./project/main.py                    1.2 KB   2024-01-15 10:30
      L12    # TODO: refactor this
  📄 ./project/utils/helpers.py           3.4 KB   2024-01-14 09:15
  📄 ./project/tests/test_main.py         2.1 KB   2024-01-13 18:42

  ──────────────────────────────────────────────────
  Found: 3 file(s) in 0.008s
```

---

## 🧪 Tests

```bash
pip install -e ".[dev]"
pytest                        # run all 35 tests
pytest tests/test_converter.py
pytest tests/test_searcher.py
pytest --cov=converter --cov=searcher
```

---

## 📁 Project structure

```
filetools/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── install.bat                ← Windows installer
├── install.sh                 ← Linux / macOS installer
├── create_release.sh          ← publishes GitHub Release via gh CLI
├── .github/
│   └── workflows/
│       ├── ci.yml             ← tests on every push/PR
│       └── release.yml        ← builds binaries + publishes release on tag
├── converter/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── core.py
│   └── formats/
│       ├── images.py          ← PNG/JPG/WebP via Pillow
│       ├── documents.py       ← TXT→PDF via fpdf2
│       └── data.py            ← JSON↔CSV, MD→TXT
├── searcher/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── core.py                ← os.walk + fnmatch + re
│   └── output.py              ← ANSI colors, stats
└── tests/
    ├── conftest.py
    ├── test_converter.py
    └── test_searcher.py
```

---

## 🤝 Contributing

```bash
git clone https://github.com/your-username/filetools.git
cd filetools
pip install -e ".[dev]"
pytest
```

1. Fork the repo
2. Create a branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m "feat: add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

MIT — see [LICENSE](LICENSE).
