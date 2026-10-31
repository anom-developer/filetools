# filetools v1.0.0 🎉

First public release of **FileTools** — a lightweight, zero-config CLI toolkit.

---

## ⬇️ Downloads

| Platform | File | Notes |
|----------|------|-------|
| 🐧 Linux x86-64 | `filetools-linux-x86_64.tar.gz` | Standalone binaries — no Python needed |
| 🖥️ Windows x86-64 | `filetools-windows-x86_64.zip` | `.exe` binaries + `install.bat` |
| 🍎 macOS x86-64 | `filetools-macos-x86_64.tar.gz` | Standalone binaries — no Python needed |
| 📦 All platforms | `filetools-source.zip` | Source + installers, requires Python 3.8+ |

---

## 🚀 Quick start

### Linux / macOS (binary)
```bash
tar -xzf filetools-linux-x86_64.tar.gz
./converter input.png output.jpg
./searcher "*.py" ./src
```

### Windows (binary)
```
Unzip filetools-windows-x86_64.zip
converter.exe input.png output.jpg
searcher.exe "*.py" .\src
```

### From source (Python 3.8+)
```bash
unzip filetools-source.zip && cd filetools
bash install.sh        # Linux/macOS
install.bat            # Windows
```

### Via pip
```bash
pip install git+https://github.com/your-username/filetools.git
```

---

## ✨ What's included

**converter** — PNG↔JPG↔WebP, TXT→PDF, JSON↔CSV, MD→TXT, batch directory mode

**searcher** — glob masks, regex, content search, depth limit, color output, file export

---

**Full changelog:** [CHANGELOG.md](https://github.com/AceAnomDev/filetools/blob/main/CHANGELOG.md)
