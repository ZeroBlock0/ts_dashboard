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

### 3.2. 配置与日志
- 配置文件：`ts_config.json`（根目录，Nuitka 运行时同目录）。使用 `app.common.config.save_config` 原子写入，避免损坏。
- 凭据持久化：
  - `persist_api_key` 控制是否把 Remote Apps API Key 写入磁盘；禁用时仍会在内存中使用当前输入。
  - `persist_query_password` 控制 ServerQuery 密码是否落盘，默认为不保存。
- 日志：
  - 日志级别由配置项 `log_level` 控制。
  - 文件日志由 `file_logging` 控制，路径 `ts_dashboard.log`，采用滚动（1MB x 3）。
  - UI 内日志通过 `QtLogHandler` 转发到 Log 页面。

### 3.3. 添加新功能页面
1. 在 `app/ui/interfaces/` 下创建一个新的 `.py` 文件 (例如 `my_interface.py`)。
2. 定义一个继承自 `QWidget` 的类。
3. 在 `app/ui/main_window.py` 中导入该类。
4. 在 `MainWindow.__init__` 中实例化，并使用 `self.addSubInterface` 添加到侧边栏。

### 3.4. 修改 ServerQuery 命令
如果需要添加新的 ServerQuery 功能：
1. 在 `app/core/ts_query.py` 中添加相应的 `async` 方法 (发送命令并解析响应)。
2. 在 `app/ui/interfaces/server_admin_interface.py` 中添加 UI 按钮或输入框。
3. 在 `app/ui/main_window.py` 的 `run_query` 方法中处理新的命令类型，并调用 `ts_query.py` 中的方法。

## 4. 构建 (Build)

使用 Nuitka 将 Python 代码编译为原生可执行文件。

**Windows:**
```cmd
build_nuitka.bat
```

- 图标：exe 使用 `app.ico`；运行时窗口与任务栏使用 `app2.ico`（脚本已打包两者）。

**macOS / Linux:**
```bash
chmod +x build_nuitka.sh
./build_nuitka.sh
```

- 图标：应用包与窗口均使用 `app.icns`（脚本已包含 app.ico/app2.ico 作为附带资源）。
