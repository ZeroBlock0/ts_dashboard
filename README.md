# TS Dashboard (TS 仪表盘)

一个为 TeamSpeak 5 设计的综合桌面仪表盘，提供事件监控、聊天日志和服务器管理功能。

## 功能

- **仪表盘 (Dashboard)**：
  - 实时监控 TeamSpeak 事件（如用户移动、文字消息等）。
  - 支持**自动清空**日志，防止内存占用过高。
- **聊天监控 (Chat Monitor)**：
  - 查看并记录服务器聊天信息。
  - 支持**自动清空**历史消息。
- **服务器管理 (Server Admin)**：
  - 查看服务器信息、频道列表、用户列表与封禁列表。
  - 执行管理操作：踢出用户 (Kick)、戳一戳 (Poke)、全局广播。
  - 发送自定义 ServerQuery 命令。
- **系统日志 (System Logs)**：
  - 记录程序运行状态与错误信息。
  - 支持导出日志与**自动清空**。
- **设置 (Settings)**：
  - 配置 Remote Apps（WebSocket）与 ServerQuery（Telnet）连接信息。
  - **自动连接**：启动时是否自动连接。
  - **手动控制**：带状态指示的连接 / 断开按钮。
  - **API Key**：管理 TeamSpeak Remote Apps 的 API Key。

> **注意**：配置保存在 `ts_config.json`，如果遇到程序无法启动的情况，删除该文件可重置设置。

## 安装与使用

1. **启用 TeamSpeak Remote Apps**：
   - 打开 TeamSpeak 设置 → Remote Apps。
   - 确保 WebSocket 服务已启用（默认端口 5899）。

2. **运行程序**：
   - Windows：运行 `TS_Dashboard.exe`。
   - macOS：打开 `TS Dashboard.app`。
   - 首次运行时，TeamSpeak 会提示授权，请点击 “Allow”。

3. **ServerQuery（可选）**：
   - 前往 “设置” 页，输入 ServerQuery 的 IP、端口、用户名与密码。
   - 点击 “保存并重连” 或使用单独的连接按钮进行连接。

## 开发与构建

本项目已采用模块化架构，使用 `uv` 管理依赖，使用 `Nuitka` 打包为原生可执行文件。

详细的开发指南请参阅 [开发文档 (docs/DEVELOPMENT.md)](docs/DEVELOPMENT.md)。

### 快速开始

```bash
# 安装依赖
uv sync

# 运行程序
uv run main.py
```

### 构建

```bash
# Windows
build_nuitka.bat

# macOS / Linux
./build_nuitka.sh
```

