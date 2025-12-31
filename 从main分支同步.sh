#!/bin/bash
# 确保进入脚本所在目录
cd "$(dirname "$0")"

echo "=== Syncing with Remote Main ==="

# 1. 切换到 main 分支
echo "[1/3] Switching to main branch..."
git checkout main

# 2. 拉取最新更改
echo "[2/3] Pulling latest changes from origin..."
git pull origin main

# 3. 同步标签
echo "[3/3] Fetching new tags..."
git fetch --tags --all

# 提取并显示同步后的版本
VERSION=$(sed -n "s/__version__ = ['\"]\(.*\)['\"]/\1/p" _version.py)

echo ""
echo "=== Sync Complete! ==="
echo "Local version is now: v$VERSION"