@echo off
setlocal
cd /d %~dp0

echo Checking environment...

REM 从 app/__init__.py 提取版本号（去掉引号，避免版本信息落为空导致使用默认值）
if "%VERSION%"=="" (
    for /f "tokens=2 delims== " %%I in ('findstr /R /C:"__version__" app\__init__.py') do set "VERSION_RAW=%%I"
)
if defined VERSION_RAW set "VERSION=%VERSION_RAW:"=%"
if "%VERSION%"=="" set "VERSION=1.0.0.0"
echo Version detected: %VERSION%

REM 检查 uv
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: 'uv' is not installed.
    exit /b 1
)

REM 确保依赖
if not exist ".venv" (
    echo Virtual environment not found. Running 'uv sync'...
    uv sync
)

set "PYTHON_EXE=.venv\Scripts\python.exe"

echo Starting Nuitka Build...

if exist build_nuitka rmdir /s /q build_nuitka
if exist dist_nuitka rmdir /s /q dist_nuitka

REM 运行 Nuitka 打包，使用变量设置版本信息 [cite: 2]
"%PYTHON_EXE%" -m nuitka ^
    --assume-yes-for-downloads ^
    --onefile ^
    --enable-plugin=pyside6 ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=app.ico ^
    --include-data-file=app.ico=app.ico ^
    --include-data-file=app2.ico=app2.ico ^
    --include-package-data=qfluentwidgets ^
    --include-package=websockets ^
    --output-dir=dist_nuitka ^
    --company-name="114514" ^
    --product-name="TS Dashboard" ^
    --file-version=%VERSION% ^
    --product-version=%VERSION% ^
    --output-filename=TS_Dashboard.exe ^
    --remove-output ^
    main.py

if %errorlevel% equ 0 (
    echo Build Success! [cite: 3]
    echo Output: dist_nuitka\TS_Dashboard.exe
) else (
    echo Build Failed!
    exit /b 1
)
