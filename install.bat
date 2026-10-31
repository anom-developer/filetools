@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

echo.
echo ╔══════════════════════════════════════════╗
echo ║       FileTools — Установщик            ║
echo ║   Converter + Searcher CLI utilities    ║
echo ╚══════════════════════════════════════════╝
echo.

:: ── 1. Найти Python ──────────────────────────────────────────────────────────
set PYTHON=

:: Сначала проверяем команду py или python в PATH
py -3 --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do (
        if exist "%%P" (
            set PYTHON=%%P
            goto :found_python
        )
    )
)

python -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do (
        if exist "%%P" (
            set PYTHON=%%P
            goto :found_python
        )
    )
)

for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python38\python.exe"
    "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
    "%LOCALAPPDATA%\Python\pythoncore-3.13-64\python.exe"
    "%LOCALAPPDATA%\Python\pythoncore-3.12-64\python.exe"
    "C:\Python314\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "C:\Program Files\Python314\python.exe"
    "C:\Program Files\Python313\python.exe"
    "C:\Program Files\Python312\python.exe"
    "C:\Program Files\Python311\python.exe"
) do (
    if exist %%P (
        set PYTHON=%%~P
        goto :found_python
    )
)

:: Fallback — where python
for /f "tokens=*" %%P in ('where python 2^>nul') do (
    "%%P" -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set PYTHON=%%P
        goto :found_python
    )
)

goto :no_python

:found_python
echo [OK] Python: !PYTHON!
for /f "tokens=2" %%V in ('"!PYTHON!" --version 2^>^&1') do echo [OK] Version: %%V

:: ── 2. Виртуальное окружение ──────────────────────────────────────────────────
echo.
if exist .venv (
    echo [OK] .venv already exists
) else (
    echo [..] Creating virtual environment ...
    "!PYTHON!" -m venv .venv
    if errorlevel 1 ( echo [ERR] venv failed & goto :error )
    echo [OK] Virtual environment created
)

:: ── 3. Обновить pip ────────────────────────────────────────────────────────────
echo [..] Upgrading pip ...
.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel --quiet
echo [OK] pip upgraded

:: ── 4. Установить пакет ───────────────────────────────────────────────────────
echo.
echo [..] Installing FileTools ...
.venv\Scripts\pip.exe install -e . --quiet
if errorlevel 1 (
    echo [ERR] Installation failed. Retrying with verbose output...
    .venv\Scripts\pip.exe install -e .
    goto :error
)
echo [OK] FileTools installed

:: ── 5. Проверить ──────────────────────────────────────────────────────────────
echo.
echo [..] Verifying ...
.venv\Scripts\python.exe -m converter --help >nul 2>&1
if errorlevel 1 ( echo [ERR] converter check failed & goto :error )
echo [OK] converter OK

.venv\Scripts\python.exe -m searcher --help >nul 2>&1
if errorlevel 1 ( echo [ERR] searcher check failed & goto :error )
echo [OK] searcher OK

:: ── 6. Создать .bat ярлыки ────────────────────────────────────────────────────
echo.
echo [..] Creating shortcuts ...

(echo @echo off
 echo "%~dp0.venv\Scripts\python.exe" -m converter %%*
) > converter.bat

(echo @echo off
 echo "%~dp0.venv\Scripts\python.exe" -m searcher %%*
) > searcher.bat

echo [OK] converter.bat and searcher.bat created

:: ── 7. Финал ──────────────────────────────────────────────────────────────────
echo.
echo ╔══════════════════════════════════════════╗
echo ║      Installation complete!             ║
echo ╚══════════════════════════════════════════╝
echo.
echo   converter input.png output.jpg
echo   converter data.json data.csv
echo   converter notes.txt notes.pdf --font-size 14
echo.
echo   searcher "*.py" .\src
echo   searcher --content "TODO" . --ext .py
echo.
echo   Run via: converter.bat ... or searcher.bat ...
echo   Or activate: .venv\Scripts\activate
echo.
echo   Docs: https://github.com/anom-developer/filetools
echo.
pause
exit /b 0

:no_python
echo.
echo [ERR] Python 3.8+ not found!
echo.
echo   Download from: https://www.python.org/downloads/
echo   Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:error
echo.
echo   If the problem persists, try running as Administrator.
echo   Report issues: https://github.com/anom-developer/filetools/issues
echo.
pause
exit /b 1
