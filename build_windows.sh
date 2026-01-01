#!/bin/bash
cd "$(dirname "$0")"

echo "Checking environment..."

# --- 优先使用环境变量 VERSION，否则从 app/__init__.py 提取 ---
if [ -n "$VERSION" ]; then
    echo "Using VERSION from environment: $VERSION"
else
    VERSION=$(python - <<'PY'
import re
from pathlib import Path
# 尝试读取 app/__init__.py
p = Path('app/__init__.py')
if p.exists():
    text = p.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", text)
    print(m.group(1) if m else '')
else:
    print('')
PY
    )
fi

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

# Windows 下 .venv 结构不同 (Scripts vs bin)
PYTHON_EXE=".venv/Scripts/python.exe"

echo "Starting Nuitka Build for Windows..."
rm -rf build_nuitka dist_nuitka

"$PYTHON_EXE" -m nuitka \
    --assume-yes-for-downloads \
    --onefile \
    --enable-plugin=pyside6 \
    --windows-console-mode=disable \
    --windows-icon-from-ico=app.ico \
    --include-data-file=app.ico=app.ico \
    --include-data-file=app2.ico=app2.ico \
    --include-package-data=qfluentwidgets \
    --include-package=websockets \
    --output-dir=dist_nuitka \
    --company-name="114514" \
    --product-name="TS Dashboard" \
    --file-version=$VERSION \
    --product-version=$VERSION \
    --output-filename=TS_Dashboard.exe \
    --remove-output \
    main.py

if [ $? -eq 0 ]; then
    echo "Build Success!"
    echo "Output: dist_nuitka/TS_Dashboard.exe"
else
    echo "Build Failed!"
    exit 1
fi
