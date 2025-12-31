#!/bin/bash
# 确保进入脚本所在目录
cd "$(dirname "$0")"

echo "=========================================="
echo "      正在提交开发内容到 dev 分支"
echo "=========================================="

# 1. 检查并切换分支
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "dev" ]; then
    echo "[提示] 当前不在 dev 分支，正在切换..."
    git checkout dev
fi

# 2. 添加更改
git add .

# 3. 输入提交信息
echo -n "请输入本次修改的内容说明: "
read msg
if [ -z "$msg" ]; then
    msg="常规开发更新"
fi

# 4. 提交并推送
git commit -m "$msg"
echo "[执行] 正在推送到云端 dev 分支..."
git push origin dev

echo ""
echo "------------------------------------------"
echo "提交成功！现在你可以去 GitHub 网页端创建 PR 了。"
echo "------------------------------------------"