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

# --- 新增 DMG 打包部分 ---
if [ $? -eq 0 ]; then
    echo ""
    echo "Nuitka Build Success! Starting DMG creation..."
    
    APP_NAME="TS Dashboard"
    DMG_NAME="TS_Dashboard_macOS.dmg"
    
    # 确保在 dist_nuitka 目录下操作
    cd dist_nuitka
    
    # 使用 hdiutil 创建 DMG
    # -srcfolder 指定要打包的 .app 文件夹
    # -format UDZO 表示创建压缩格式的只读镜像
    hdiutil create -volname "$APP_NAME" -srcfolder "$APP_NAME.app" -ov -format UDZO "$DMG_NAME"
    
    if [ $? -eq 0 ]; then
        echo "DMG Created Successfully: dist_nuitka/$DMG_NAME"
    else
        echo "DMG Creation Failed!"
        exit 1
    fi
    cd ..
else
    echo ""
    echo "Build Failed!"
    exit 1
fi