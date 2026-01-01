# TS Dashboard (TS 仪表盘)

一个为 TeamSpeak 5 设计的现代化综合桌面仪表盘，提供实时事件监控、聊天日志记录和强大的服务器管理功能。

![License](https://img.shields.io/github/license/ZeroBlock0/ts_dashboard)
![Version](https://img.shields.io/github/v/release/ZeroBlock0/ts_dashboard)
![Build Status](https://img.shields.io/github/actions/workflow/status/ZeroBlock0/ts_dashboard/release.yml)

## ✨ 核心功能

### 📊 仪表盘 (Dashboard)
- **实时监控**：捕获并展示 TeamSpeak 客户端的所有事件（如用户进出、文字消息、权限变动等）。
- **智能管理**：支持自动清空日志，防止长时间运行导致内存占用过高。
- **自定义指令**：支持发送自定义 JSON 指令到 Remote Apps。

### 💬 聊天监控 (Chat Monitor)
- **全频道记录**：实时查看并记录服务器内的公共聊天、频道聊天和私聊信息。
- **历史回溯**：支持自动滚动和自动清理历史消息。

### 🛠️ 服务器管理 (Server Admin)
- **信息概览**：查看服务器基本信息、在线人数、频道列表。
- **用户管理**：查看在线用户列表，执行 **踢出 (Kick)**、**封禁 (Ban)** 操作。
- **趣味互动**：支持 **戳一戳 (Poke)** 功能，并可发送自定义戳一戳消息。
- **高级控制**：内置 ServerQuery 终端，支持发送任意 Telnet 管理命令（如 `whoami`, `serverinfo`）。

### ⚙️ 系统与设置
- **多语言支持**：内置 **简体中文** 和 **English**，一键切换。
- **主题适配**：支持浅色/深色主题切换，或跟随系统自动调整。
- **连接管理**：支持 Remote Apps (WebSocket) 和 ServerQuery (Telnet) 双重连接。
- **安全隐私**：敏感信息（如 API Key、密码）可选择是否保存，支持一键清除。

## 🚀 安装与使用

### 1. 准备工作
在使用本软件前，请确保您的 TeamSpeak 客户端已启用 Remote Apps 功能：
1. 打开 TeamSpeak 客户端设置。
2. 进入 **Remote Apps** 选项卡。
3. 勾选 **Enable Remote Apps**（默认端口 5899）。

### 2. 运行程序
- **Windows**: 下载并运行 `TS_Dashboard.exe`。
- **macOS**: 下载并打开 `TS Dashboard.app`。

> 首次连接时，TeamSpeak 客户端会弹出授权提示框，请点击 **Allow** (允许)。

### 3. 连接 ServerQuery (可选)
如果您需要使用服务器管理功能（如踢人、封禁）：
1. 在 TS Dashboard 中进入 **设置** 页面。
2. 填写 ServerQuery 的 IP、端口（默认 10011）、用户名（通常是 `serveradmin`）和密码。
3. 点击 **连接** 或 **保存并重连**。

## 🛠️ 开发与构建

本项目基于 Python 3.12 + PySide6 (Qt) + Nuitka 开发。

### 环境要求
- Python 3.12+
- `uv` (推荐) 或 `pip`

### 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/ZeroBlock0/ts_dashboard.git
cd ts_dashboard

# 2. 安装依赖
uv sync

# 3. 运行
# Windows
./run.bat

# macOS / Linux
./run.sh
```

### 手动构建
构建产物将输出到 `dist/` 目录。

```bash
# Windows
./build_windows.sh

# macOS
./build_macos.sh
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

本项目使用 **Semantic Release** 自动管理版本，请务必遵守 [Conventional Commits](https://www.conventionalcommits.org/) 规范提交代码：

- `feat: ...` -> 新功能 (Minor 版本 +1)
- `fix: ...` -> 修复 Bug (Patch 版本 +1)
- `docs: ...` -> 文档变更
- `style: ...` -> 代码格式调整

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

