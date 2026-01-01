# Semantic Release 指南

本项目使用 [python-semantic-release](https://python-semantic-release.readthedocs.io/) 自动化版本管理和发布流程。

## 核心原则

我们遵循 **[Conventional Commits](https://www.conventionalcommits.org/)** 规范。这意味着你的提交信息（Commit Message）决定了版本号如何变更。

### 提交格式

```text
<type>(<scope>): <subject>
```

### 常用类型 (Type)

| 类型 | 描述 | 版本变更 |
| :--- | :--- | :--- |
| **fix** | 修复 Bug | **Patch** (1.0.0 -> 1.0.1) |
| **feat** | 新功能 | **Minor** (1.0.0 -> 1.1.0) |
| **perf** | 性能优化 | **Patch** |
| **docs** | 文档变更 | 无 (默认) |
| **style** | 代码格式调整 | 无 (默认) |
| **refactor** | 代码重构 | 无 (默认) |
| **test** | 测试相关 | 无 (默认) |
| **chore** | 构建/工具变动 | 无 (默认) |

### 重大变更 (Breaking Changes)

如果在提交信息的正文或页脚中包含 `BREAKING CHANGE:`，或者在类型后加 `!` (例如 `feat!: ...`)，将触发 **Major** 版本更新 (1.0.0 -> 2.0.0)。

## 自动发布流程

1.  **开发**: 在功能分支上进行开发。
2.  **提交**: 使用符合规范的提交信息提交代码。
3.  **合并**: 将代码合并到 `main` 分支。
4.  **发布**: GitHub Actions 会自动检测 `main` 分支的新提交：
    *   分析提交历史。
    *   计算下一个版本号。
    *   更新 `pyproject.toml` 和 `app/__init__.py` 中的版本号。
    *   生成 `CHANGELOG.md`。
    *   创建 Git Tag。
    *   创建 GitHub Release。
    *   触发构建流程（Windows/macOS）并将产物上传到 Release。

## 配置说明

配置文件位于 `pyproject.toml`：

```toml
[tool.semantic_release]
version_variables = ["app/__init__.py:__version__", "pyproject.toml:version"]
upload_to_pypi = false
upload_to_release = true
```

## 常见问题

### 为什么没有触发发布？

*   检查提交信息是否包含 `fix` 或 `feat`。如果只有 `docs` 或 `chore`，默认不会触发版本升级。
*   确保是在 `main` 分支上进行的推送。

### 如何手动触发？

目前配置仅支持 `push` 到 `main` 分支触发发布。如果需要强制发布，可以提交一个空的 `fix` 提交：

```bash
git commit --allow-empty -m "fix: force release"
git push
```
