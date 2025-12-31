@echo off
setlocal
cd /d %~dp0

echo ==========================================
echo       正在提交开发内容到 dev 分支
echo ==========================================

REM 1. 检查是否在 dev 分支
for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%i
if not "%BRANCH%"=="dev" (
    echo [提示] 当前不在 dev 分支，正在切换...
    git checkout dev
)

REM 2. 添加更改
git add .

REM 3. 让用户输入提交信息
set /p msg="请输入本次修改的内容说明: "
if "%msg%"=="" set msg="常规开发更新"

REM 4. 提交并推送
git commit -m "%msg%"
echo [执行] 正在推送到云端 dev 分支...
git push origin dev

echo.
echo ------------------------------------------
echo 提交成功！现在你可以去 GitHub 网页端创建 PR 了。
echo ------------------------------------------
pause