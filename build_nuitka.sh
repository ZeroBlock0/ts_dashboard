#!/bin/bash
# 确保进入脚本所在目录
cd "$(dirname "$0")"

echo "Checking environment..."

# --- 新增：从 _version.py 提取版本号 ---
# 使用 sed 提取引号内的内容
VERSION=$(sed -n "s/__version__ = ['\"]\(.*\)['\"]/\1/p" _version.py)

# 如果没找到版本号，设置默认值
if [ -z "$VERSION" ]; then
    VERSION="1.0.0.0"
fi
echo "Version detected: $VERSION"

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

# 显示系统资源信息
echo "System Info:"
sysctl hw.memsize hw.ncpu || true
df -h . || true

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
    --company-name="114514" \
    --product-name="TS Dashboard" \
    --file-version=$VERSION \
    --product-version=$VERSION \
    --remove-output \
    --show-progress \
    --show-memory \
    --jobs=2 \
    main.py

# --- DMG 打包部分 ---
if [ $? -eq 0 ]; then
    echo "Nuitka Build Success! Starting DMG creation..."
    
    APP_NAME="TS Dashboard"
    # 将版本号加入 DMG 文件名，方便区分
    DMG_NAME="TS_Dashboard_macOS_v$VERSION.dmg"
    
    cd dist_nuitka

    if [ -d "main.app" ]; then
        mv "main.app" "$APP_NAME.app"
    fi
    
    echo "Fixing permissions..."
    chmod +x "$APP_NAME.app/Contents/MacOS/main"
    
    echo "Creating DMG..."
    hdiutil create -volname "$APP_NAME" -srcfolder "$APP_NAME.app" -ov -format UDZO "$DMG_NAME"
    
    if [ $? -eq 0 ]; then
        echo "DMG Created Successfully: $DMG_NAME"
        ls -lh "$DMG_NAME"
    else
        echo "DMG Creation Failed!"
        exit 1
    fi
    cd ..
else
    echo "Build Failed!"
    exit 1
fi

echo "Build process completed!"
