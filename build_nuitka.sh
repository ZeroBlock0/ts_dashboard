#!/bin/bash
# 确保进入脚本所在目录
cd "$(dirname "$0")"

echo "Checking environment..."

# 检查 uv
if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' is not installed."
    exit 1
fi

# 同步环境
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Running 'uv sync'..."
    uv sync
fi

PYTHON_EXE=".venv/bin/python"

echo "Starting Nuitka Build for macOS..."
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

# --- DMG 打包部分 ---
if [ $? -eq 0 ]; then
    echo "Nuitka Build Success! Starting DMG creation..."
    
    APP_NAME="TS Dashboard"
    DMG_NAME="TS_Dashboard_macOS.dmg"
    
    cd dist_nuitka

    # Rename the generated app to the desired product name
    if [ -d "main.app" ]; then
        mv "main.app" "$APP_NAME.app"
    fi
    
    # 修复权限
    chmod +x "$APP_NAME.app/Contents/MacOS/main"
    
    # 创建 DMG
    hdiutil create -volname "$APP_NAME" -srcfolder "$APP_NAME.app" -ov -format UDZO "$DMG_NAME"
    
    if [ $? -eq 0 ]; then
        echo "DMG Created Successfully: $DMG_NAME"
    else
        echo "DMG Creation Failed!"
        exit 1
    fi
    cd ..
else
    echo "Build Failed!"
    exit 1
fi