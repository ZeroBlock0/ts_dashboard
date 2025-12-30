#!/bin/bash

# 确保进入脚本所在目录
cd "$(dirname "$0")"

echo "Checking environment..."

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' is not installed. Please install uv first."
    echo "Visit https://github.com/astral-sh/uv"
    exit 1
fi

# Ensure dependencies
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Running 'uv sync'..."
    uv sync
fi

PYTHON_EXE=".venv/bin/python"

# Check Nuitka
$PYTHON_EXE -c "import nuitka" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Nuitka not found in .venv. Running 'uv sync'..."
    uv sync
    if [ $? -ne 0 ]; then
        echo "Failed to install dependencies."
        exit 1
    fi
fi

echo "Starting Nuitka Build for macOS..."

# 清理旧构建
rm -rf build_nuitka dist_nuitka

# 运行 Nuitka 打包
# 注意: macOS 上通常生成 .app 应用包，而不是单文件 exe

$PYTHON_EXE -m nuitka \
    --standalone \
    --macos-create-app-bundle \
    --macos-app-icon=app.icns \
    --enable-plugin=pyside6 \
    --include-data-file=app.ico=app.ico \
    --include-data-file=app.icns=app.icns \
    --include-package-data=qfluentwidgets \
    --include-package=websockets \
    --output-dir=dist_nuitka \
    --company-name="TS Dashboard" \
    --product-name="TS Dashboard" \
    --file-version=1.0.0.0 \
    --product-version=1.0.0.0 \
    --remove-output \
    main.py

if [ $? -eq 0 ]; then
    echo ""
    echo "Build Success!"
    echo "Output: dist_nuitka/TS Dashboard.app"
else
    echo ""
    echo "Build Failed!"
fi
