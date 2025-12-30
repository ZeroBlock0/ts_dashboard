@echo off
setlocal

echo Checking environment...

REM Check for uv
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: 'uv' is not installed. Please install uv first.
    echo Visit https://github.com/astral-sh/uv
    pause
    exit /b 1
)

REM Ensure dependencies are installed
if not exist ".venv" (
    echo Virtual environment not found. Running 'uv sync'...
    uv sync
)

set "PYTHON_EXE=.venv\Scripts\python.exe"

REM Check if Nuitka is installed in .venv
"%PYTHON_EXE%" -c "import nuitka" 2>nul
if %errorlevel% neq 0 (
    echo Nuitka not found in .venv. Running 'uv sync'...
    uv sync
    if %errorlevel% neq 0 (
        echo Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo Starting Nuitka Build...

REM Clean old build directories
if exist build_nuitka rmdir /s /q build_nuitka
if exist dist_nuitka rmdir /s /q dist_nuitka

REM Run Nuitka Build
REM --onefile: 打包成单文件 exe
"%PYTHON_EXE%" -m nuitka ^
    --onefile ^
    --enable-plugin=pyside6 ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=app.ico ^
    --include-data-file=app.ico=app.ico ^
    --include-package-data=qfluentwidgets ^
    --output-dir=dist_nuitka ^
    --company-name="TS Dashboard" ^
    --product-name="TS Dashboard" ^
    --file-version=1.0.0.0 ^
    --product-version=1.0.0.0 ^
    --output-filename=TS_Dashboard.exe ^
    --include-package=websockets ^
    --remove-output ^
    main.py

if %errorlevel% equ 0 (
    echo.
    echo Build Success!
    echo Output file: dist_nuitka\TS_Dashboard.exe
) else (
    echo.
    echo Build Failed!
)

pause
