# 开发文档 (Development Documentation)

本文档旨在帮助开发者深入理解 `TS Dashboard` 的架构设计、代码结构以及开发流程。

## 1. 项目概览

`TS Dashboard` 是一个基于 Python 的桌面应用程序，采用了现代化的 GUI 框架和异步网络通信技术。

- **GUI 框架**: [PySide6](https://doc.qt.io/qtforpython/) (Qt 6.x)
- **UI 组件库**: [QFluentWidgets](https://qfluentwidgets.com/) (WinUI 3 风格)
- **网络通信**: 
  - `websockets` (用于 TS Remote Apps)
  - `asyncio` (用于 ServerQuery Telnet)
- **打包工具**: [Nuitka](https://nuitka.net/) (编译为原生代码)
- **依赖管理**: [uv](https://github.com/astral-sh/uv)

## 2. 项目结构

```text
ts_dashboard/
├── app/
│   ├── common/             # 通用基础设施
│   │   ├── config.py       # 配置管理 (JSON持久化)
│   │   ├── constants.py    # 常量与枚举
│   │   ├── i18n.py         # 国际化 (i18n) 支持
│   │   ├── logger.py       # 日志系统 (Qt集成)
│   │   └── signals.py      # 跨线程信号 (WorkerSignals)
│   ├── core/               # 核心业务逻辑
│   │   ├── ts_client.py    # Remote Apps 客户端 (WebSocket)
│   │   └── ts_query.py     # ServerQuery 客户端 (Async Socket)
│   └── ui/                 # 用户界面层
│       ├── interfaces/     # 功能页面 (Tab页)
│       │   ├── dashboard_interface.py    # 仪表盘
│       │   ├── chat_interface.py         # 聊天监控
│       │   ├── server_admin_interface.py # 服务器管理
│       │   ├── log_interface.py          # 日志查看器
│       │   └── settings_interface.py     # 设置中心
│       └── main_window.py  # 主窗口与事件循环集成
├── docs/                   # 项目文档
├── dist/                   # 构建产物目录
├── .github/                # CI/CD 配置
├── main.py                 # 程序入口
├── pyproject.toml          # 项目配置与依赖
├── run.bat                 # Windows 启动脚本
├── run.sh                  # macOS/Linux 启动脚本
├── build_windows.sh        # Windows 构建脚本
└── build_macos.sh          # macOS 构建脚本
```

## 3. 核心架构说明

### 3.1. 异步与多线程模型
由于 Qt 的 UI 运行在主线程 (Main Thread)，而网络通信 (WebSocket/Socket) 需要长时间运行且不能阻塞 UI，本项目采用了 **Qt + asyncio** 混合模型：

1.  **主线程 (Main Thread)**: 运行 `QApplication` 事件循环，负责 UI 渲染和用户交互。
2.  **工作线程 (Worker Thread)**: 
    - 在 `MainWindow` 初始化时启动一个独立的线程。
    - 该线程运行一个 `asyncio` 事件循环。
    - `TeamSpeakClient` 和 `ServerQueryClient` 均在此循环中运行。
3.  **通信桥梁**: 使用 `app.common.signals.WorkerSignals` (QObject) 进行跨线程通信。
    - 异步线程通过 `emit` 发送信号。
    - 主线程通过 `connect` 接收信号并更新 UI。

### 3.2. 国际化 (i18n) 实现
- **字典存储**: 所有翻译文本存储在 `app/common/i18n.py` 的 `TRANSLATIONS` 字典中。
- **动态切换**: `tr(key)` 函数根据当前配置返回对应语言的文本。
- **注意**: 目前切换语言后需要重启应用，因为 UI 组件是在初始化时加载文本的。

### 3.3. 配置持久化
- 配置文件存储在 `ts_config.json`。
- 使用 `app.common.config` 模块进行读写。
- 为了防止文件损坏，写入时采用“原子写入”策略（先写临时文件，再重命名）。

## 4. 开发流程指南

### 4.1. 环境准备
推荐使用 `uv` 作为包管理器，它比 pip 更快且支持锁文件。

```bash
# 安装依赖
uv sync

# 启动开发环境
# Windows
./run.bat
# macOS/Linux
./run.sh
```

### 4.2. 添加新功能
如果您想添加一个新的功能页面：

1.  **创建 UI**: 在 `app/ui/interfaces/` 下新建 `.py` 文件，继承 `QWidget`。
2.  **注册页面**: 在 `app/ui/main_window.py` 中导入并在 `__init__` 中使用 `addSubInterface` 添加。
3.  **处理逻辑**: 如果需要网络数据，请在 `app/core/` 中扩展相应的 Client，并通过 `WorkerSignals` 转发数据。

### 4.3. 版本发布 (CI/CD)
本项目实现了完全自动化的版本发布流程，基于 GitHub Actions 和 `python-semantic-release`。

- **触发机制**: 当代码推送到 `main` 分支时触发。
- **版本规则**: 根据 Commit Message 自动决定版本号升级 (Major/Minor/Patch)。
- **自动产物**:
  - 更新 `pyproject.toml` 版本号。
  - 生成 `CHANGELOG.md`。
  - 创建 GitHub Release。
  - 自动构建 Windows (.exe) 和 macOS (.app) 并上传附件。

**⚠️ 重要**: 提交代码时必须遵守 [Conventional Commits](https://www.conventionalcommits.org/) 规范！
- `feat: ...` (新功能)
- `fix: ...` (修复)
- `docs: ...` (文档)

## 5. 常见问题排查

### Q: 为什么连接不上 TeamSpeak？
- 检查 TS 客户端是否开启了 Remote Apps。
- 检查防火墙是否拦截了 5899 端口。
- 首次连接必须在 TS 客户端点击 "Allow"。

### Q: 构建失败怎么办？
- 检查 `build_windows.sh` 或 `build_macos.sh` 中的 Nuitka 命令。
- 确保已安装 C 编译器 (Windows 上通常会自动下载 MinGW64)。
- 查看 CI 日志获取详细错误信息。
