# TS Dashboard (TS 仪表盘)

一个为 TeamSpeak 5 设计的综合桌面仪表盘，提供事件监控、聊天日志和服务器管理功能。

## 功能

- **仪表盘 (Dashboard)**：实时监控 TeamSpeak 事件（如用户移动、文字消息等）。
- **聊天监控 (Chat Monitor)**：查看并记录服务器聊天信息。
- **服务器管理 (Server Admin)**：
  - 查看服务器信息、频道列表、用户列表与封禁列表。
  - 执行管理操作：踢出用户 (Kick)、戳一戳 (Poke)、全局广播。
  - 发送自定义 ServerQuery 命令。
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

本项目使用 `uv` 管理依赖，使用 `Nuitka` 打包为原生可执行文件。

### 前置条件

- 已安装 `uv`（参见：<https://github.com/astral-sh/uv>）。
- Windows：安装 Visual Studio 的 C++ 构建工具。
- macOS：安装 Xcode 命令行工具。

### 构建说明

仓库包含一键构建脚本用于环境准备与编译。

**Windows：**
```powershell
.\build_nuitka.bat
```
可执行文件位于 `dist_nuitka\TS_Dashboard.exe`。

**macOS：**
```bash
chmod +x build_nuitka.sh
./build_nuitka.sh
```
应用程序包位于 `dist_nuitka/TS Dashboard.app`。

### 从源码运行

```bash
uv sync
uv run main.py
```

### 发布流程

发布步骤：

1. 在 `_version.py` 中更新版本号。
2. 运行发布脚本：

   **Windows：**
   ```powershell
   .\release.bat
   ```

   **macOS / Linux：**
   ```bash
   ./release.sh
   ```

发布脚本会：
- 将版本号同步到 `pyproject.toml`。
- 提交并推送更改到 `main` 分支。
- 创建并推送 Git 标签（例如 `v1.0.0`），触发 CI/CD 工作流。

