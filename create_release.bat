@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

set VERSION=%1
if "%VERSION%"=="" set VERSION=v1.0.0

echo.
echo ╔══════════════════════════════════════════╗
echo ║   FileTools — Публикация релиза %VERSION%  ║
echo ╚══════════════════════════════════════════╝
echo.

:: 1. Прогон тестов
echo [..] Запуск тестов pytest ...
if exist .venv\Scripts\pytest.exe (
    .venv\Scripts\pytest.exe -q
    if errorlevel 1 (
        echo [ERR] Тесты завершились с ошибкой!
        exit /b 1
    )
    echo [OK] Все тесты успешно пройдены!
)

:: 2. Создание git-тега
echo.
echo [..] Создание git тега %VERSION% ...
git tag -a "%VERSION%" -m "Release %VERSION%" 2>nul
git push origin "%VERSION%" 2>nul
echo [OK] Тег отправлен в репозиторий. GitHub Actions начнет автоматическую сборку релиза!

echo.
echo [OK] Готово! Релиз доступен на:
echo     https://github.com/anom-developer/filetools/releases/tag/%VERSION%
echo.
pause

