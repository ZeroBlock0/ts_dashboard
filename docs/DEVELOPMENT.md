# 开发文档 (Development Documentation)

本文档旨在帮助开发者理解 `TS Dashboard` 的代码结构，并指导如何进行功能扩展和维护。

## 1. 项目结构 (Project Structure)

本项目采用模块化架构，将核心逻辑、UI 界面和通用工具分离。

```text
ts_dashboard/
├── app/
│   ├── common/             # 通用工具模块
│   │   ├── config.py       # 配置文件的加载与保存 (ts_config.json)
│   │   ├── constants.py    # 常量定义 (如事件类型翻译字典)
│   │   ├── logger.py       # 日志处理 (QtLogHandler)
│   │   └── signals.py      # 全局 Qt 信号定义 (WorkerSignals)
│   ├── core/               # 核心业务逻辑
│   │   ├── ts_client.py    # TeamSpeak WebSocket 客户端 (Remote Apps)
│   │   └── ts_query.py     # ServerQuery Telnet 客户端 (Admin Query)
│   └── ui/                 # 用户界面 (基于 PySide6 + QFluentWidgets)
│       ├── interfaces/     # 各个功能页面 (Tab)
│       │   ├── dashboard_interface.py    # 仪表盘 (事件流)
│       │   ├── chat_interface.py         # 聊天监控
│       │   ├── server_admin_interface.py # 服务器管理
│       │   ├── log_interface.py          # 系统日志
│       │   └── settings_interface.py     # 设置页面
│       └── main_window.py  # 主窗口逻辑 (负责组装各 Interface 和处理信号)
├── docs/                   # 文档
├── main.py                 # 程序入口点
├── pyproject.toml          # 项目依赖配置 (uv)
├── build_nuitka.bat        # Windows 构建脚本
└── build_nuitka.sh         # macOS/Linux 构建脚本
```

## 2. 核心组件说明

### 2.1. 信号系统 (Signals)
所有的跨线程通信都通过 `app.common.signals.WorkerSignals` 类进行。
- `connected / disconnected`: WebSocket 连接状态变化。
- `new_event(dict)`: 收到新的 TeamSpeak 事件数据。
- `new_log(str, str)`: 产生新的日志 (Level, Message)。
- `query_response(dict)`: ServerQuery 命令的返回结果。

### 2.2. 客户端 (Clients)
- **TeamSpeakClient (`app.core.ts_client`)**:
  - 使用 `websockets` 库连接 TS5 Remote Apps 服务。
  - 运行在 `asyncio` 事件循环中。
  - 负责接收实时事件流。
- **ServerQueryClient (`app.core.ts_query`)**:
  - 使用 `telnetlib3` (或原生 socket 封装) 连接 ServerQuery 端口 (10011)。
  - 负责执行管理命令 (Kick, Ban, Channel List 等)。

### 2.3. 界面 (UI)
- **MainWindow (`app.ui.main_window`)**:
  - 继承自 `FluentWindow`。
  - 初始化 `asyncio` 事件循环线程。
  - 连接 `WorkerSignals` 到各个 Interface 的槽函数。
  - 负责处理全局的业务逻辑协调。

## 3. 开发指南

### 3.1. 环境搭建
本项目使用 `uv` 进行依赖管理。

```bash
# 安装依赖
uv sync

# 运行项目
uv run main.py
```

### 3.2. 添加新功能页面
1. 在 `app/ui/interfaces/` 下创建一个新的 `.py` 文件 (例如 `my_interface.py`)。
2. 定义一个继承自 `QWidget` 的类。
3. 在 `app/ui/main_window.py` 中导入该类。
4. 在 `MainWindow.__init__` 中实例化，并使用 `self.addSubInterface` 添加到侧边栏。

### 3.3. 修改 ServerQuery 命令
如果需要添加新的 ServerQuery 功能：
1. 在 `app/core/ts_query.py` 中添加相应的 `async` 方法 (发送命令并解析响应)。
2. 在 `app/ui/interfaces/server_admin_interface.py` 中添加 UI 按钮或输入框。
3. 在 `app/ui/main_window.py` 的 `run_query` 方法中处理新的命令类型，并调用 `ts_query.py` 中的方法。

## 4. 构建发布 (Build)

使用 Nuitka 将 Python 代码编译为原生可执行文件。

**Windows:**
```cmd
build_nuitka.bat
```

**macOS / Linux:**
```bash
chmod +x build_nuitka.sh
./build_nuitka.sh
```

## 注意

本项目已采用全自动化流水线。开发者只需关注 `dev` 分支的开发，版本发布由 GitHub Actions 自动完成。

### 自动化发布流程
1. **本地开发**：在 `dev` 分支编写代码，使用 `提交到dev分支` 推送。
2. **提交审核**：在 GitHub 提交 Pull Request 到 `main` 分支。
3. **自动构建**：云端会自动运行 Nuitka 构建并由 Copilot 进行审查。
4. **合并发布**：PR 合并后，云端会自动累加版本号、打标签并发布 Release。
5. **本地同步**：合并完成后，运行 `从main分支同步` 保持本地版本最新。
