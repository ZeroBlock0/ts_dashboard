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

### 配置与安全
- 设置页可选择是否**保存 API Key** 与 **保存 ServerQuery 密码**，默认不强制保存密码，方便避免明文落盘。
- 支持一键清除已保存的凭据。
- 端口输入会自动校验，非法值会回退为默认端口并提示。

### 日志
- 日志级别可在设置中切换（DEBUG/INFO/WARNING/ERROR）。
- 可选文件日志，默认写入 `ts_dashboard.log`（滚动保存，最大约 1MB，最多 3 个文件）。

### 版本
- 版本号由 `semantic-release` 自动管理，无需手动修改。
- 遵循 **Conventional Commits** 规范提交代码，CI 会自动计算版本号、生成 Changelog 并发布 Release。

### 图标与打包
- Windows：Exe 使用 `app.ico`；窗口与任务栏图标使用 `app2.ico`（脚本已将两者内置）。
- macOS：应用包与窗口均使用 `app.icns`。

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

在 `dev` 分支开发，PR通过后的版本发布由 GitHub Actions 自动完成。

### 快速开始
```bash
# 方式一：直接使用 uv
uv sync
uv run main.py

# 方式二：使用脚本 (自动同步依赖并运行)
./run.sh
```

### 提交规范 (Conventional Commits)
本项目使用 `semantic-release` 自动发布版本，请务必遵守以下提交格式：
- `fix: ...` -> 修复 Bug (Patch 版本 +1)
- `feat: ...` -> 新功能 (Minor 版本 +1)
- `feat!: ...` -> 破坏性变更 (Major 版本 +1)
- `docs:`, `style:`, `refactor:`, `chore:` -> 不触发版本发布

### 手动构建
```bash
# Windows
./build_windows.sh

# macOS
./build_macos.sh
```

