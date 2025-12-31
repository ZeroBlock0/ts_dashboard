@echo off
setlocal
cd /d %~dp0

echo Checking environment...

REM Check for uv
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: 'uv' is not installed.
    exit /b 1
)

REM Ensure dependencies
if not exist ".venv" (
    echo Virtual environment not found. Running 'uv sync'...
    uv sync
)

set "PYTHON_EXE=.venv\Scripts\python.exe"

REM Check Nuitka
"%PYTHON_EXE%" -c "import nuitka" 2>nul
if %errorlevel% neq 0 (
    echo Nuitka not found. Running 'uv sync'...
    uv sync
    if %errorlevel% neq 0 exit /b 1
)

echo Starting Nuitka Build...

if exist build_nuitka rmdir /s /q build_nuitka
if exist dist_nuitka rmdir /s /q dist_nuitka

REM Run Nuitka Build
"%PYTHON_EXE%" -m nuitka ^
    --assume-yes-for-downloads ^
    --onefile ^
    --enable-plugin=pyside6 ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=app.ico ^
    --include-data-file=app.ico=app.ico ^
    --include-package-data=qfluentwidgets ^
    --include-package=websockets ^
    --output-dir=dist_nuitka ^
    --company-name="TS Dashboard" ^
    --product-name="TS Dashboard" ^
    --file-version=1.0.0.0 ^
    --product-version=1.0.0.0 ^
    --output-filename=TS_Dashboard.exe ^
    --remove-output ^
    main.py

if %errorlevel% equ 0 (
    echo Build Success!
    echo Output: dist_nuitka\TS_Dashboard.exe
) else (
    echo Build Failed!
    exit /b 1
)