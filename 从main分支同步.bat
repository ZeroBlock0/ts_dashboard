@echo off
setlocal
cd /d %~dp0

echo === Syncing with Remote Main ===

REM 1. 切换到 main 分支
echo [1/3] Switching to main branch...
git checkout main

REM 2. 拉取云端最新的代码（包括 Action 自动修改的 _version.py）
echo [2/3] Pulling latest changes from origin...
git pull origin main

REM 3. 同步云端生成的自动标签
echo [3/3] Fetching new tags from origin...
git fetch --tags --all

echo.
echo === Sync Complete! ===
REM 显示当前同步后的最新版本号
for /f "tokens=2 delims='" %%I in ('findstr "__version__" _version.py') do set VERSION=%%I
echo Local version is now: v%VERSION%
echo.
pause