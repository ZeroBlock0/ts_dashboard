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
│   │   ├── i18n.py         # 国际化支持 (Translation)
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
├── run.sh                  # 运行脚本 (自动同步依赖)
├── build_windows.sh        # Windows 构建脚本 (Bash)
└── build_macos.sh          # macOS 构建脚本 (Bash)
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

### 3.3. 国际化 (i18n)
本项目支持多语言切换（目前支持简体中文 `zh_CN` 和英文 `en_US`）。
- **实现方式**：使用 `app.common.i18n` 模块。
- **添加新语言**：
  1. 在 `app/common/i18n.py` 的 `TRANSLATIONS` 字典中添加新的语言代码（如 `ja_JP`）。
  2. 在 `app/ui/interfaces/settings_interface.py` 的语言下拉框中添加新选项。
- **使用翻译**：
  在 UI 代码中，使用 `tr("key")` 替代硬编码的字符串。
  ```python
  from app.common.i18n import tr
  label = BodyLabel(tr("dashboard"), self)
  ```
- **注意事项**：目前语言切换需要重启应用才能生效。

### 3.4. 版本与发布 (Semantic Release)

本项目采用全自动化的版本管理和发布流程，基于 [python-semantic-release](https://python-semantic-release.readthedocs.io/)。

#### 3.3.1. 工作原理
开发者无需手动修改版本号。CI 系统会根据 **Commit Messages** 自动判断版本升级类型（Major/Minor/Patch），并执行以下操作：
1.  计算下一个版本号。
2.  更新 `app/__init__.py` 和 `pyproject.toml` 中的版本号。
3.  生成 `CHANGELOG.md`。
4.  创建 Git Tag。
5.  创建 GitHub Release。
6.  触发构建流程，将生成的 `.exe` / `.app` 上传到 Release 附件。

#### 3.3.2. 提交规范 (Conventional Commits)
为了让系统正确识别，**必须**使用符合 [Conventional Commits](https://www.conventionalcommits.org/) 规范的提交信息：

格式：`<type>(<scope>): <description>`

| 类型 (Type) | 含义 | 版本影响 | 示例 |
| :--- | :--- | :--- | :--- |
| **fix** | 修复 Bug | **Patch** (1.0.0 -> 1.0.1) | `fix: 修复了聊天窗口无法滚动的bug` |
| **feat** | 新功能 | **Minor** (1.0.0 -> 1.1.0) | `feat: 新增服务器状态监控面板` |
| **feat!** | 破坏性变更 | **Major** (1.0.0 -> 2.0.0) | `feat!: 重构API接口，不再兼容旧版` |
| **docs** | 文档修改 | 无 | `docs: 更新README安装说明` |
| **style** | 格式调整 | 无 | `style: 调整代码缩进` |
| **refactor**| 代码重构 | 无 | `refactor: 优化数据库连接逻辑` |
| **chore** | 杂务 | 无 | `chore: 更新依赖库` |
| **ci** | CI配置 | 无 | `ci: 修复GitHub Actions脚本` |

> **注意**：如果提交信息不符合规范（如简单的 "update code"），该提交将被忽略，不会触发版本发布。

#### 3.3.3. 发布流程
1.  在本地完成开发。
2.  使用规范的 Commit Message 提交代码。
3.  推送到 `main` 分支：`git push origin main`。
4.  前往 GitHub Actions 页面查看 `Build and Release` 工作流进度。

### 3.4. 构建 (Build)
构建产物将输出到 `dist/` 目录。

```bash
# Windows 构建 (生成 dist/TS_Dashboard.exe)
./build_windows.sh

# macOS 构建 (生成 dist/TS_Dashboard.app 和 .dmg)
./build_macos.sh
```

### 3.5. 添加新功能页面
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
