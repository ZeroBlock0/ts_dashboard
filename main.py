import sys
import os
import json
import asyncio
import threading
import time
import logging
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QObject, Slot, QThread, QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QTreeWidget, QTreeWidgetItem, QHeaderView, QTextEdit,
    QLabel, QLineEdit, QFormLayout, QGroupBox, QMenu, QFileDialog,
    QPlainTextEdit, QCheckBox
)
from PySide6.QtGui import QColor, QIcon, QAction, QKeySequence, QShortcut

from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, SubtitleLabel, 
    PrimaryPushButton, PushButton, TextEdit, 
    FluentIcon as FIF, InfoBar, InfoBarPosition, Theme, setTheme, isDarkTheme,
    LineEdit, PasswordLineEdit, CardWidget, BodyLabel, SearchLineEdit,
    ComboBox
)

from ts_client import TeamSpeakClient
from ts_query import ServerQueryClient
try:
    from _version import __version__
except ImportError:
    __version__ = "0.0.0"

# --- Translations ---
EVENT_TRANSLATIONS = {
    "auth": "认证 (Auth)",
    "clientMoved": "用户移动 (Client Moved)",
    "textMessage": "文字消息 (Text Message)",
    "talkStatusChanged": "语音状态 (Talk Status)",
    "serverPropertiesUpdated": "服务器属性更新",
    "channelCreated": "频道创建",
    "channelDeleted": "频道删除",
    "clientPropertiesUpdated": "用户属性更新",
    "connectStatusChanged": "连接状态变更",
}

KEY_TRANSLATIONS = {
    "type": "类型 (type)",
    "payload": "数据载荷 (payload)",
    "invoker": "触发者 (invoker)",
    "name": "名称 (name)",
    "message": "内容 (message)",
    "from": "来源 (from)",
    "targetMode": "目标模式 (targetMode)",
    "clientId": "客户端ID",
    "channelId": "频道ID",
    "reasonId": "原因ID",
    "status": "状态",
    "flag": "标志",
    "isTalking": "正在说话",
    "isWhispering": "正在私聊",
    "nickname": "昵称",
    "uid": "用户UID",
}

def get_config_path():
    # Nuitka specific check
    if "__compiled__" in globals():
        # Nuitka standalone/onefile
        # sys.argv[0] is the path to the executable file
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # Development
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "ts_config.json")

def load_config():
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

# --- Signal Bridge for Thread Safety ---
class WorkerSignals(QObject):
    connected = Signal()
    disconnected = Signal()
    new_event = Signal(dict)
    query_response = Signal(dict)
    new_log = Signal(str, str)

class QtLogHandler(logging.Handler):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals

    def emit(self, record):
        msg = self.format(record)
        self.signals.new_log.emit(record.levelname, msg)

# --- Log Interface ---
class LogInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("logInterface")
        self.vBoxLayout = QVBoxLayout(self)
        
        self.titleLabel = SubtitleLabel("系统日志 (System Logs)", self)
        self.vBoxLayout.addWidget(self.titleLabel)
        
        self.logs = [] # Store logs for filtering
        
        # Search Bar
        self.searchBar = SearchLineEdit(self)
        self.searchBar.setPlaceholderText("搜索日志内容...")
        self.searchBar.textChanged.connect(self.filter_logs)
        self.vBoxLayout.addWidget(self.searchBar)
        
        # Controls
        self.controlLayout = QHBoxLayout()
        self.autoScrollCb = QCheckBox("自动滚动 (Auto Scroll)", self)
        self.autoScrollCb.setChecked(True)
        self.exportBtn = PushButton("导出日志 (Export)", self)
        self.exportBtn.setIcon(FIF.SAVE)
        self.clearBtn = PushButton("清空 (Clear)", self)
        self.clearBtn.setIcon(FIF.DELETE)
        
        self.controlLayout.addWidget(self.autoScrollCb)
        self.controlLayout.addStretch(1)
        self.controlLayout.addWidget(self.exportBtn)
        self.controlLayout.addWidget(self.clearBtn)
        self.vBoxLayout.addLayout(self.controlLayout)
        
        # Log View
        self.logView = QPlainTextEdit(self)
        self.logView.setReadOnly(True)
        self.logView.setMaximumBlockCount(2000) # Limit to 2000 lines to prevent freezing
        self.logView.setStyleSheet("font-family: 'Consolas', 'Monospace'; font-size: 12px;")
        self.vBoxLayout.addWidget(self.logView)
        
        # Connect signals
        self.clearBtn.clicked.connect(self.clear_logs)
        self.exportBtn.clicked.connect(self.export_logs)

    def clear_logs(self):
        self.logView.clear()
        self.logs = []

    def append_log(self, level, message):
        # Colorize based on level
        color = "#000000"
        if isDarkTheme():
             color = "#ffffff"
        
        if level == "ERROR":
            color = "#ff4d4f"
        elif level == "WARNING":
            color = "#faad14"
        elif level == "DEBUG":
            color = "#8c8c8c"
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f'<span style="color:{color}">[{timestamp}] [{level}] {message}</span>'
        raw_msg = f"[{timestamp}] [{level}] {message}"
        
        self.logs.append((raw_msg, formatted_msg))
        if len(self.logs) > 2000:
            self.logs.pop(0)
            
        # Only append if matches filter
        filter_txt = self.searchBar.text().lower()
        if not filter_txt or filter_txt in raw_msg.lower():
            self.logView.appendHtml(formatted_msg)
            if self.autoScrollCb.isChecked():
                self.logView.moveCursor(self.logView.textCursor().MoveOperation.End)

    def filter_logs(self, text):
        self.logView.clear()
        text = text.lower()
        for raw, formatted in self.logs:
            if not text or text in raw.lower():
                self.logView.appendHtml(formatted)
        
        if self.autoScrollCb.isChecked():
            self.logView.moveCursor(self.logView.textCursor().MoveOperation.End)

    def export_logs(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存日志", "ts_dashboard_logs.txt", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.logView.toPlainText())
                InfoBar.success(title='导出成功', content=f"日志已保存到 {file_path}", parent=self)
            except Exception as e:
                InfoBar.error(title='导出失败', content=str(e), parent=self)

# --- Dashboard Interface ---
class DashboardInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("dashboardInterface")
        
        self.vBoxLayout = QVBoxLayout(self)
        
        # Title
        self.titleLabel = SubtitleLabel("实时事件流 (TeamSpeak Events)", self)
        self.vBoxLayout.addWidget(self.titleLabel)
        
        # Search Bar
        self.searchBar = SearchLineEdit(self)
        self.searchBar.setPlaceholderText("搜索事件内容...")
        self.searchBar.textChanged.connect(self.filter_tree)
        self.vBoxLayout.addWidget(self.searchBar)
        
        # Controls
        self.controlLayout = QHBoxLayout()
        self.autoScrollCb = QCheckBox("自动滚动 (Auto Scroll)", self)
        self.autoScrollCb.setChecked(True)
        self.controlLayout.addWidget(self.autoScrollCb)
        self.controlLayout.addStretch(1)
        self.vBoxLayout.addLayout(self.controlLayout)
        
        # Tree Widget for Events
        self.treeWidget = QTreeWidget(self)
        self.treeWidget.setHeaderLabels(["键 / 事件 (Key / Event)", "值 (Value)"])
        self.treeWidget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.treeWidget.setAlternatingRowColors(True)
        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.show_context_menu)
        self.treeWidget.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.vBoxLayout.addWidget(self.treeWidget)
        
        # Shortcuts
        self.copyShortcut = QShortcut(QKeySequence("Ctrl+C"), self.treeWidget)
        self.copyShortcut.activated.connect(self.copy_selection)
        
        # Input Area Title
        self.inputLabel = SubtitleLabel("发送自定义 JSON 指令", self)
        self.vBoxLayout.addWidget(self.inputLabel)
        
        # JSON Input
        self.jsonInput = TextEdit(self)
        self.jsonInput.setPlaceholderText("在此输入 JSON 指令...")
        self.jsonInput.setPlainText('{\n    "type": "keyPress",\n    "payload": {\n        "button": "test",\n        "state": true\n    }\n}')
        self.jsonInput.setMaximumHeight(150)
        self.vBoxLayout.addWidget(self.jsonInput)
        
        # Buttons
        self.buttonLayout = QHBoxLayout()
        self.sendBtn = PrimaryPushButton("发送指令 (Send)", self)
        self.sendBtn.setIcon(FIF.SEND)
        self.clearBtn = PushButton("清空日志 (Clear)", self)
        self.clearBtn.setIcon(FIF.DELETE)
        
        self.buttonLayout.addWidget(self.sendBtn)
        self.buttonLayout.addWidget(self.clearBtn)
        self.buttonLayout.addStretch(1)
        self.vBoxLayout.addLayout(self.buttonLayout)
        
        # Connect buttons
        self.clearBtn.clicked.connect(self.treeWidget.clear)

    def add_event(self, data):
        raw_type = data.get("type", "Unknown")
        cn_type = EVENT_TRANSLATIONS.get(raw_type, raw_type)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Create summary for root node
        summary = ""
        payload = data.get("payload", {})
        if raw_type == "textMessage":
            invoker = payload.get("invoker")
            sender = "?"
            if isinstance(invoker, dict):
                sender = invoker.get("name") or invoker.get("nickname") or "?"
            
            if sender == "?":
                sender = str(payload.get("from", "?"))
                
            msg = payload.get("message", "")
            summary = f" - {sender}: {msg}"
        elif raw_type == "clientMoved":
            # Try to get who moved
            try:
                cid = payload.get("clientId", "?")
                new_channel = payload.get("newChannelId", "?")
                summary = f" - ID:{cid} -> Ch:{new_channel}"
            except: pass

        root_item = QTreeWidgetItem(self.treeWidget)
        root_item.setText(0, f"[{timestamp}] {cn_type}{summary}")
        
        # Color coding
        if raw_type == "textMessage":
            root_item.setForeground(0, QColor("#4cc2ff")) # Light Blue
        elif raw_type == "auth":
            root_item.setForeground(0, QColor("#6cc24a")) # Green
        elif raw_type == "talkStatusChanged":
            root_item.setForeground(0, QColor("#dcdcdc")) # Grayish
            
        self._populate_tree(root_item, data)
        self.treeWidget.insertTopLevelItem(0, root_item)
        
        # Auto expand only important events
        if raw_type in ["textMessage", "auth", "clientMoved"]:
            root_item.setExpanded(True)
            
        # Auto Scroll (Scroll to top item)
        if self.autoScrollCb.isChecked():
            self.treeWidget.scrollToItem(root_item)

    def _populate_tree(self, parent_item, data):
        if isinstance(data, dict):
            for key, value in data.items():
                cn_key = KEY_TRANSLATIONS.get(key, key)
                item = QTreeWidgetItem(parent_item)
                item.setText(0, str(cn_key))
                self._populate_tree(item, value)
        elif isinstance(data, list):
            for i, value in enumerate(data):
                item = QTreeWidgetItem(parent_item)
                item.setText(0, f"[{i}]")
                self._populate_tree(item, value)
        else:
            parent_item.setText(1, str(data))

    def filter_tree(self, text):
        text = text.lower()
        root = self.treeWidget.invisibleRootItem()
        child_count = root.childCount()
        
        for i in range(child_count):
            item = root.child(i)
            self._filter_item(item, text)

    def _filter_item(self, item, text):
        # Check if item matches
        match = text in item.text(0).lower() or text in item.text(1).lower()
        
        # Check children
        child_match = False
        for i in range(item.childCount()):
            if self._filter_item(item.child(i), text):
                child_match = True
        
        should_show = match or child_match
        item.setHidden(not should_show)
        
        # If a child matches, expand this item so the child is visible
        if child_match:
            item.setExpanded(True)
            
        return should_show

    def show_context_menu(self, position):
        items = self.treeWidget.selectedItems()
        if not items:
            return
            
        menu = QMenu(self)
        
        if len(items) == 1:
            item = items[0]
            copy_key_act = QAction("复制键 (Copy Key)", self)
            copy_key_act.triggered.connect(lambda: QApplication.clipboard().setText(item.text(0)))
            
            copy_val_act = QAction("复制值 (Copy Value)", self)
            copy_val_act.triggered.connect(lambda: QApplication.clipboard().setText(item.text(1)))
            
            menu.addAction(copy_key_act)
            menu.addAction(copy_val_act)
            
        copy_row_act = QAction(f"复制选中行 ({len(items)} Rows)", self)
        copy_row_act.triggered.connect(self.copy_selection)
        menu.addAction(copy_row_act)
        
        menu.exec(self.treeWidget.viewport().mapToGlobal(position))

    def copy_selection(self):
        items = self.treeWidget.selectedItems()
        if not items:
            return
            
        text_list = []
        for item in items:
            k = item.text(0)
            v = item.text(1)
            if v:
                text_list.append(f"{k}: {v}")
            else:
                text_list.append(k)
        
        QApplication.clipboard().setText("\n".join(text_list))

# --- Chat Interface ---
class ChatInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("chatInterface")
        
        self.vBoxLayout = QVBoxLayout(self)
        
        self.titleLabel = SubtitleLabel("聊天监控 (Chat Monitor)", self)
        self.vBoxLayout.addWidget(self.titleLabel)
        
        self.messages = [] # Store messages
        
        # Search Bar
        self.searchBar = SearchLineEdit(self)
        self.searchBar.setPlaceholderText("搜索聊天记录...")
        self.searchBar.textChanged.connect(self.filter_chat)
        self.vBoxLayout.addWidget(self.searchBar)
        
        # Controls
        self.controlLayout = QHBoxLayout()
        self.autoScrollCb = QCheckBox("自动滚动 (Auto Scroll)", self)
        self.autoScrollCb.setChecked(True)
        self.clearBtn = PushButton("清空 (Clear)", self)
        self.clearBtn.setIcon(FIF.DELETE)
        
        self.controlLayout.addWidget(self.autoScrollCb)
        self.controlLayout.addStretch(1)
        self.controlLayout.addWidget(self.clearBtn)
        self.vBoxLayout.addLayout(self.controlLayout)
        
        self.chatLog = QTextEdit(self)
        self.chatLog.setReadOnly(True)
        self.chatLog.setStyleSheet("font-family: 'Microsoft YaHei'; font-size: 14px;")
        self.vBoxLayout.addWidget(self.chatLog)
        
        self.clearBtn.clicked.connect(self.clear_chat)

    def clear_chat(self):
        self.chatLog.clear()
        self.messages = []

    def add_message(self, sender, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"<b>[{timestamp}] [{sender}]:</b> {message}"
        raw_msg = f"[{timestamp}] [{sender}]: {message}"
        
        self.messages.append((raw_msg, formatted_msg))
        
        # Only append if matches filter
        filter_txt = self.searchBar.text().lower()
        if not filter_txt or filter_txt in raw_msg.lower():
            self.chatLog.append(formatted_msg)
            if self.autoScrollCb.isChecked():
                self.chatLog.moveCursor(self.chatLog.textCursor().MoveOperation.End)

    def filter_chat(self, text):
        self.chatLog.clear()
        text = text.lower()
        for raw, formatted in self.messages:
            if not text or text in raw.lower():
                self.chatLog.append(formatted)
        
        if self.autoScrollCb.isChecked():
            self.chatLog.moveCursor(self.chatLog.textCursor().MoveOperation.End)

# --- Settings Interface ---
class SettingsInterface(QWidget):
    def __init__(self, config=None, parent=None):
        super().__init__(parent=parent)
        self.config = config or {}
        self.setObjectName("settingsInterface")
        self.vBoxLayout = QVBoxLayout(self)
        
        self.titleLabel = SubtitleLabel("连接设置 (Connection Settings)", self)
        self.vBoxLayout.addWidget(self.titleLabel)
        
        # Auto Connect Switch
        self.autoConnectCb = QCheckBox("启动时自动连接 (Auto Connect on Startup)", self)
        self.autoConnectCb.setChecked(self.config.get("auto_connect", True))
        self.vBoxLayout.addWidget(self.autoConnectCb)
        
        # Appearance Settings
        self.groupAppearance = QGroupBox("外观设置 (Appearance)", self)
        self.layoutAppearance = QFormLayout(self.groupAppearance)
        self.comboTheme = ComboBox(self)
        self.comboTheme.addItems(["浅色 (Light)", "深色 (Dark)", "跟随系统 (System)"])
        
        # Set initial selection based on config
        current_theme = self.config.get("theme", "Light")
        if current_theme == "Dark":
            self.comboTheme.setCurrentIndex(1)
        elif current_theme == "System":
            self.comboTheme.setCurrentIndex(2)
        else:
            self.comboTheme.setCurrentIndex(0)
            
        self.layoutAppearance.addRow("主题 (Theme):", self.comboTheme)
        self.vBoxLayout.addWidget(self.groupAppearance)
        
        # Remote Apps Settings
        self.groupRemote = QGroupBox("Remote Apps (WebSocket)", self)
        self.layoutRemote = QFormLayout(self.groupRemote)
        
        # Header with Connect Button and Status
        self.headerRemote = QWidget()
        self.headerLayoutRemote = QHBoxLayout(self.headerRemote)
        self.headerLayoutRemote.setContentsMargins(0, 0, 0, 0)
        self.btnConnectRemote = PushButton("连接 (Connect)", self)
        self.statusRemote = BodyLabel("未连接", self)
        self.headerLayoutRemote.addWidget(self.btnConnectRemote)
        self.headerLayoutRemote.addWidget(self.statusRemote)
        self.headerLayoutRemote.addStretch(1)
        self.layoutRemote.addRow("操作:", self.headerRemote)

        self.ipRemote = LineEdit(self)
        self.ipRemote.setPlaceholderText("127.0.0.1")
        self.ipRemote.setText(self.config.get("remote_ip", ""))
        self.portRemote = LineEdit(self)
        self.portRemote.setPlaceholderText("5899")
        self.portRemote.setText(self.config.get("remote_port", ""))
        self.apiKeyRemote = LineEdit(self)
        self.apiKeyRemote.setPlaceholderText("API Key")
        self.apiKeyRemote.setText(self.config.get("apiKey", ""))

        self.layoutRemote.addRow("IP 地址:", self.ipRemote)
        self.layoutRemote.addRow("端口 (Port):", self.portRemote)
        self.layoutRemote.addRow("API Key:", self.apiKeyRemote)
        self.vBoxLayout.addWidget(self.groupRemote)
        
        # ServerQuery Settings
        self.groupQuery = QGroupBox("ServerQuery (Telnet)", self)
        self.layoutQuery = QFormLayout(self.groupQuery)
        
        # Header with Connect Button and Status
        self.headerQuery = QWidget()
        self.headerLayoutQuery = QHBoxLayout(self.headerQuery)
        self.headerLayoutQuery.setContentsMargins(0, 0, 0, 0)
        self.btnConnectQuery = PushButton("连接 (Connect)", self)
        self.statusQuery = BodyLabel("未连接", self)
        self.headerLayoutQuery.addWidget(self.btnConnectQuery)
        self.headerLayoutQuery.addWidget(self.statusQuery)
        self.headerLayoutQuery.addStretch(1)
        self.layoutQuery.addRow("操作:", self.headerQuery)

        self.ipQuery = LineEdit(self)
        self.ipQuery.setPlaceholderText("127.0.0.1")
        self.ipQuery.setText(self.config.get("query_ip", ""))
        self.portQuery = LineEdit(self)
        self.portQuery.setPlaceholderText("10011")
        self.portQuery.setText(self.config.get("query_port", ""))
        self.userQuery = LineEdit(self)
        self.userQuery.setText(self.config.get("query_user", ""))
        self.userQuery.setPlaceholderText("serveradmin")
        self.passQuery = PasswordLineEdit(self)
        self.passQuery.setText(self.config.get("query_pass", ""))
        self.layoutQuery.addRow("IP 地址:", self.ipQuery)
        self.layoutQuery.addRow("端口 (Port):", self.portQuery)
        self.layoutQuery.addRow("用户名:", self.userQuery)
        self.layoutQuery.addRow("密码:", self.passQuery)
        self.vBoxLayout.addWidget(self.groupQuery)
        
        # Save Button
        self.saveBtn = PrimaryPushButton("保存并重连 (Save & Reconnect)", self)
        self.vBoxLayout.addWidget(self.saveBtn)
        self.vBoxLayout.addStretch(1)
        
        # Version Label
        self.versionLabel = BodyLabel(f"Version: {__version__}", self)
        self.versionLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vBoxLayout.addWidget(self.versionLabel)

# --- Server Admin Interface ---
class ServerAdminInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("serverAdminInterface")
        self.vBoxLayout = QVBoxLayout(self)
        
        self.titleLabel = SubtitleLabel("服务器管理 (Server Admin)", self)
        self.vBoxLayout.addWidget(self.titleLabel)
        
        # Search Bar
        self.searchBar = SearchLineEdit(self)
        self.searchBar.setPlaceholderText("搜索结果...")
        self.searchBar.textChanged.connect(self.filter_tree)
        self.vBoxLayout.addWidget(self.searchBar)
        
        # Group 1: Information & Lists
        self.groupInfo = QGroupBox("信息查询 (Information)", self)
        self.layoutInfo = QHBoxLayout(self.groupInfo)
        self.btnInfo = PushButton("服务器信息", self)
        self.btnChannels = PushButton("频道列表", self)
        self.btnClients = PushButton("用户列表", self)
        self.btnBans = PushButton("封禁列表", self)
        self.btnTokens = PushButton("特权密钥", self)
        
        self.layoutInfo.addWidget(self.btnInfo)
        self.layoutInfo.addWidget(self.btnChannels)
        self.layoutInfo.addWidget(self.btnClients)
        self.layoutInfo.addWidget(self.btnBans)
        self.layoutInfo.addWidget(self.btnTokens)
        self.layoutInfo.addStretch(1)
        self.vBoxLayout.addWidget(self.groupInfo)

        # Group 2: Management Actions
        self.groupAction = QGroupBox("管理操作 (Actions)", self)
        self.layoutAction = QVBoxLayout(self.groupAction)
        
        # Row 1: Message Center
        self.rowMsg = QHBoxLayout()
        self.comboMsgType = ComboBox(self)
        self.comboMsgType.addItems(["全局广播 (GM)", "服务器聊天 (Server)", "频道聊天 (Channel)", "私聊 (Private)"])
        self.comboMsgType.setFixedWidth(160)
        self.comboMsgType.currentIndexChanged.connect(self.on_msg_type_changed)
        
        self.inputMsgTarget = LineEdit(self)
        self.inputMsgTarget.setPlaceholderText("目标ID (clid)")
        self.inputMsgTarget.setFixedWidth(100)
        self.inputMsgTarget.setEnabled(False) # Default disabled
        
        self.inputMsg = LineEdit(self)
        self.inputMsg.setPlaceholderText("输入消息内容...")
        
        self.btnSendMsg = PrimaryPushButton("发送消息 (Send)", self)
        
        self.rowMsg.addWidget(self.comboMsgType)
        self.rowMsg.addWidget(self.inputMsgTarget)
        self.rowMsg.addWidget(self.inputMsg)
        self.rowMsg.addWidget(self.btnSendMsg)
        self.layoutAction.addLayout(self.rowMsg)
        
        # Row 2: Query Bot Move & Rename
        self.rowBotMove = QHBoxLayout()
        self.inputBotCid = LineEdit(self)
        self.inputBotCid.setPlaceholderText("目标频道ID (cid)")
        self.inputBotCid.setFixedWidth(120)
        self.inputBotPwd = PasswordLineEdit(self)
        self.inputBotPwd.setPlaceholderText("频道密码 (可选)")
        self.inputBotPwd.setFixedWidth(120)
        self.btnBotMove = PushButton("切换频道", self)
        
        self.inputBotName = LineEdit(self)
        self.inputBotName.setPlaceholderText("修改 Bot 昵称")
        self.inputBotName.setFixedWidth(120)
        self.btnBotRename = PushButton("改名", self)
        
        self.rowBotMove.addWidget(self.inputBotCid)
        self.rowBotMove.addWidget(self.inputBotPwd)
        self.rowBotMove.addWidget(self.btnBotMove)
        self.rowBotMove.addWidget(self.inputBotName)
        self.rowBotMove.addWidget(self.btnBotRename)
        self.rowBotMove.addStretch(1)
        self.layoutAction.addLayout(self.rowBotMove)
        
        # Row 3: Client Operations
        self.rowClient = QHBoxLayout()
        self.inputClid = LineEdit(self)
        self.inputClid.setPlaceholderText("目标用户ID (clid)")
        self.inputClid.setFixedWidth(150)
        self.btnKick = PushButton("踢出用户 (Kick)", self)
        self.btnPoke = PushButton("戳用户 (Poke)", self)
        self.rowClient.addWidget(self.inputClid)
        self.rowClient.addWidget(self.btnKick)
        self.rowClient.addWidget(self.btnPoke)
        self.rowClient.addStretch(1)
        self.layoutAction.addLayout(self.rowClient)
        
        # Row 4: Custom Command
        self.rowCustom = QHBoxLayout()
        self.inputCustom = LineEdit(self)
        self.inputCustom.setPlaceholderText("输入自定义 ServerQuery 命令 (例如: whoami)")
        self.btnSendCustom = PrimaryPushButton("发送命令 (Send)", self)
        self.rowCustom.addWidget(self.inputCustom)
        self.rowCustom.addWidget(self.btnSendCustom)
        self.layoutAction.addLayout(self.rowCustom)
        
        self.vBoxLayout.addWidget(self.groupAction)
        
        # Output Area
        self.outputTree = QTreeWidget(self)
        self.outputTree.setHeaderLabels(["Key", "Value"])
        self.outputTree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.vBoxLayout.addWidget(self.outputTree)

    def on_msg_type_changed(self, index):
        # Index 3 is Private Chat, which needs target ID
        self.inputMsgTarget.setEnabled(index == 3)
        if index == 3:
            self.inputMsgTarget.setPlaceholderText("目标ID (clid)")
        else:
            self.inputMsgTarget.setPlaceholderText("无需目标")

    def filter_tree(self, text):
        text = text.lower()
        root = self.outputTree.invisibleRootItem()
        child_count = root.childCount()
        
        for i in range(child_count):
            item = root.child(i)
            self._filter_item(item, text)

    def _filter_item(self, item, text):
        # Check if item matches
        match = text in item.text(0).lower() or text in item.text(1).lower()
        
        # Check children
        child_match = False
        for i in range(item.childCount()):
            if self._filter_item(item.child(i), text):
                child_match = True
        
        should_show = match or child_match
        item.setHidden(not should_show)
        
        # If a child matches, expand this item so the child is visible
        if child_match:
            item.setExpanded(True)
            
        return should_show

    def display_data(self, data_list):
        self.outputTree.clear()
        if not data_list:
            return
            
        for item in data_list:
            root = QTreeWidgetItem(self.outputTree)
            # Use first key as title if possible
            title = "Item"
            if 'virtualserver_name' in item: title = item['virtualserver_name']
            elif 'channel_name' in item: title = item['channel_name']
            elif 'nickname' in item: title = item['nickname']
            elif 'token' in item: title = item['token']
            elif 'ip' in item: title = item['ip']
            
            root.setText(0, title)
            
            for k, v in item.items():
                child = QTreeWidgetItem(root)
                child.setText(0, str(k))
                child.setText(1, str(v))
            
            self.outputTree.addTopLevelItem(root)

# --- Main Window ---
class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TS 仪表盘 (Dashboard)")
        
        # Set Window Icon
        icon_name = "app.icns" if sys.platform == "darwin" else "app.ico"
        icon_path = self.get_resource_path(icon_name)
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.resize(1000, 750)
        
        # Load Config
        self.config = load_config()
        
        # Force apply theme from config
        # This ensures that even if FluentWindow defaults to something else, we override it.
        t = self.config.get("theme", "Light")
        
        def apply_theme_delayed():
            if t == "Dark":
                setTheme(Theme.DARK)
            elif t == "System":
                setTheme(Theme.AUTO)
            else:
                setTheme(Theme.LIGHT)
                
            # Debug info
            # InfoBar.info(
            #    title='Theme Loaded',
            #    content=f"Applied Theme: {t}",
            #    parent=self,
            #    duration=3000
            # )

        # Apply immediately
        apply_theme_delayed()
        # And apply again shortly after show to override any auto-detection
        QTimer.singleShot(100, apply_theme_delayed)
        
        # Initialize Signals
        self.signals = WorkerSignals()
        self.signals.connected.connect(self.on_connected)
        self.signals.disconnected.connect(self.on_disconnected)
        self.signals.new_event.connect(self.on_new_event)
        self.signals.query_response.connect(self.on_query_response)
        
        # Initialize Interfaces
        self.dashboardInterface = DashboardInterface(self)
        self.chatInterface = ChatInterface(self)
        self.settingsInterface = SettingsInterface(config=self.config, parent=self)
        self.serverAdminInterface = ServerAdminInterface(self)
        self.logInterface = LogInterface(self)
        
        # Setup Logging
        self.logHandler = QtLogHandler(self.signals)
        self.logHandler.setFormatter(logging.Formatter('%(message)s'))
        logging.getLogger().addHandler(self.logHandler)
        logging.getLogger().setLevel(logging.DEBUG) # Capture all logs
        
        # Connect Log Signal
        self.signals.new_log.connect(self.logInterface.append_log)
        
        # Log Config Path for Debugging
        logging.info(f"Config Path: {get_config_path()}")
        logging.info(f"Frozen: {getattr(sys, 'frozen', False)}")
        logging.info(f"Executable: {sys.executable}")
        
        # Add Navigation Items
        self.addSubInterface(self.dashboardInterface, FIF.HOME, "仪表盘")
        self.addSubInterface(self.chatInterface, FIF.CHAT, "聊天监控")
        self.addSubInterface(self.serverAdminInterface, FIF.PEOPLE, "服务器管理")
        self.addSubInterface(self.logInterface, FIF.DOCUMENT, "系统日志")
        self.addSubInterface(self.settingsInterface, FIF.SETTING, "设置")
        
        # Connect Dashboard Send Button
        self.dashboardInterface.sendBtn.clicked.connect(self.send_command)
        
        # Connect Settings Button
        self.settingsInterface.saveBtn.clicked.connect(self.update_settings)
        self.settingsInterface.btnConnectRemote.clicked.connect(self.toggle_remote_connection)
        self.settingsInterface.btnConnectQuery.clicked.connect(self.toggle_query_connection)
        
        # Connect Admin Buttons
        self.serverAdminInterface.btnInfo.clicked.connect(lambda: self.run_query("serverinfo"))
        self.serverAdminInterface.btnChannels.clicked.connect(lambda: self.run_query("channellist"))
        self.serverAdminInterface.btnClients.clicked.connect(lambda: self.run_query("clientlist"))
        self.serverAdminInterface.btnBans.clicked.connect(lambda: self.run_query("banlist"))
        self.serverAdminInterface.btnTokens.clicked.connect(lambda: self.run_query("tokenlist"))
        
        self.serverAdminInterface.btnSendMsg.clicked.connect(lambda: self.run_query("sendmsg"))
        self.serverAdminInterface.btnBotMove.clicked.connect(lambda: self.run_query("move_self"))
        self.serverAdminInterface.btnBotRename.clicked.connect(lambda: self.run_query("rename_self"))
        self.serverAdminInterface.btnKick.clicked.connect(lambda: self.run_query("kick"))
        self.serverAdminInterface.btnPoke.clicked.connect(lambda: self.run_query("poke"))
        self.serverAdminInterface.btnSendCustom.clicked.connect(lambda: self.run_query("custom"))
        
        # Initialize Clients
        # Use config for initial connection info if available
        ra_ip = self.config.get("remote_ip") or "127.0.0.1"
        
        ra_port_val = self.config.get("remote_port")
        try:
            ra_port = int(ra_port_val) if ra_port_val else 5899
        except ValueError:
            ra_port = 5899
            
        self.ts_client = TeamSpeakClient(ip=ra_ip, port=ra_port, config_file=get_config_path())
        
        self.query_client = ServerQueryClient()
        self.loop = asyncio.new_event_loop()
        
        # Start Background Thread
        self.thread = threading.Thread(target=self.start_async_loop, daemon=True)
        self.thread.start()
        
        # Initial Status
        if self.config.get("auto_connect", True):
            self.show_status(f"正在连接 Remote Apps ({ra_ip}:{ra_port})...", "warning")

    def get_resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def save_config(self):
        path = get_config_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            InfoBar.error(title='保存配置失败', content=str(e), parent=self)

    def start_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.ts_client.set_callbacks(
            lambda: self.signals.connected.emit(),
            lambda: self.signals.disconnected.emit(),
            lambda data: self.signals.new_event.emit(data)
        )
        
        if self.config.get("auto_connect", True):
            self.loop.create_task(self.ts_client.connect())
            
            # Auto connect Query
            q_ip = self.config.get("query_ip", "")
            q_port = self.config.get("query_port", "10011")
            q_user = self.config.get("query_user", "")
            q_pass = self.config.get("query_pass", "")
            
            if q_ip and q_port:
                try:
                    port = int(q_port)
                    self.loop.create_task(self._async_connect_query(q_ip, port, q_user, q_pass))
                except:
                    pass

        self.loop.run_forever()

    async def _async_connect_query(self, ip, port, user, password):
        success, msg = await self.query_client.connect(ip, port, user, password)
        if success:
            self.signals.query_response.emit({"status": "connected", "msg": "ServerQuery Connected"})
        else:
            self.signals.query_response.emit({"status": "error", "msg": f"ServerQuery Error: {msg}"})

    def toggle_remote_connection(self):
        if self.ts_client.connected:
            # Disconnect
            asyncio.run_coroutine_threadsafe(self.ts_client.stop(), self.loop)
            self.settingsInterface.btnConnectRemote.setText("连接 (Connect)")
            self.settingsInterface.statusRemote.setText("断开连接")
        else:
            # Connect
            if not self.ts_client.running:
                 asyncio.run_coroutine_threadsafe(self.ts_client.connect(), self.loop)
            self.settingsInterface.btnConnectRemote.setText("断开 (Disconnect)")
            self.settingsInterface.statusRemote.setText("正在连接...")

    def toggle_query_connection(self):
        if self.query_client.connected:
            # Disconnect
            asyncio.run_coroutine_threadsafe(self.query_client.disconnect(), self.loop)
            self.settingsInterface.btnConnectQuery.setText("连接 (Connect)")
            self.settingsInterface.statusQuery.setText("断开连接")
        else:
            # Connect
            q_ip = self.settingsInterface.ipQuery.text()
            try:
                q_port = int(self.settingsInterface.portQuery.text())
            except:
                InfoBar.error(title='错误', content="端口必须是数字", parent=self)
                return
            q_user = self.settingsInterface.userQuery.text()
            q_pass = self.settingsInterface.passQuery.text()
            
            self.settingsInterface.statusQuery.setText("正在连接...")
            asyncio.run_coroutine_threadsafe(
                self._async_connect_query(q_ip, q_port, q_user, q_pass), 
                self.loop
            )

    @Slot()
    def on_connected(self):
        self.show_status("已连接到 TeamSpeak 5 (Remote Apps)", "success")
        self.settingsInterface.btnConnectRemote.setText("断开 (Disconnect)")
        self.settingsInterface.statusRemote.setText("已连接")

    @Slot()
    def on_disconnected(self):
        self.show_status("Remote Apps 连接断开", "error")
        self.settingsInterface.btnConnectRemote.setText("连接 (Connect)")
        self.settingsInterface.statusRemote.setText("未连接")

    @Slot(dict)
    def on_new_event(self, data):
        # Update Dashboard
        self.dashboardInterface.add_event(data)
        
        # Update Chat if applicable
        event_type = data.get("type", "")
        payload = data.get("payload", {})
        
        # Check for chat messages (Strictly check for textMessage type)
        if "textMessage" in event_type:
            sender = "Unknown"
            invoker = payload.get("invoker")
            
            if isinstance(invoker, dict):
                sender = invoker.get("name") or invoker.get("nickname") or "Unknown"
            
            if sender == "Unknown":
                 # Try 'from' field
                 sender = str(payload.get("from", "Unknown"))
                 # Debug log to help identify why name is missing
                 if sender == "Unknown":
                     logging.debug(f"TextMessage missing name. Keys: {list(payload.keys())}")

            msg = payload.get("message", "")
            if msg:
                self.chatInterface.add_message(sender, msg)

    @Slot(dict)
    def on_query_response(self, data):
        # Handle connection status messages
        if "status" in data:
            if data["status"] == "connected":
                self.settingsInterface.btnConnectQuery.setText("断开 (Disconnect)")
                self.settingsInterface.statusQuery.setText("已连接")
                InfoBar.success(title='ServerQuery', content=data["msg"], parent=self)
                return
            elif data["status"] == "error":
                self.settingsInterface.btnConnectQuery.setText("连接 (Connect)")
                self.settingsInterface.statusQuery.setText("连接失败")
                InfoBar.error(title='ServerQuery Error', content=data["msg"], parent=self)
                return

        # Handle errors
        if "error" in data and data["error"]:
            InfoBar.error(title='ServerQuery Error', content=str(data["error"]), parent=self)
            return
            
        # Handle data display
        if "data" in data and isinstance(data["data"], list):
             self.serverAdminInterface.display_data(data["data"])
        elif isinstance(data, list):
             self.serverAdminInterface.display_data(data)
        elif isinstance(data, dict):
             # Fallback for single item or other dicts
             self.serverAdminInterface.display_data([data])

    def send_command(self):
        json_str = self.dashboardInterface.jsonInput.toPlainText().strip()
        if not json_str:
            return
            
        try:
            # Validate JSON
            json.loads(json_str)
            # Send via async loop
            if self.ts_client.websocket:
                asyncio.run_coroutine_threadsafe(self.ts_client.websocket.send(json_str), self.loop)
                InfoBar.success(title='发送成功', content="指令已发送", parent=self)
            else:
                InfoBar.error(title='发送失败', content="未连接到 Remote Apps", parent=self)
        except Exception as e:
            InfoBar.error(title='发送失败', content=str(e), parent=self)

    def update_settings(self):
        # Get values
        ra_ip = self.settingsInterface.ipRemote.text()
        ra_port = self.settingsInterface.portRemote.text()
        
        # Update Config
        self.config["auto_connect"] = self.settingsInterface.autoConnectCb.isChecked()
        self.config["remote_ip"] = ra_ip
        self.config["remote_port"] = ra_port
        self.config["apiKey"] = self.settingsInterface.apiKeyRemote.text()
        self.config["query_ip"] = self.settingsInterface.ipQuery.text()
        self.config["query_port"] = self.settingsInterface.portQuery.text()
        self.config["query_user"] = self.settingsInterface.userQuery.text()
        self.config["query_pass"] = self.settingsInterface.passQuery.text()
        
        # Update Theme Config
        theme_idx = self.settingsInterface.comboTheme.currentIndex()
        theme_val = "Light"
        if theme_idx == 1: theme_val = "Dark"
        elif theme_idx == 2: theme_val = "System"
        self.config["theme"] = theme_val
        
        self.save_config()
        
        # Apply Theme
        if theme_val == "Dark":
            setTheme(Theme.DARK)
        elif theme_val == "System":
            setTheme(Theme.AUTO)
        else:
            setTheme(Theme.LIGHT)
        
        # Use defaults if empty for connection
        connect_ip = ra_ip if ra_ip else "127.0.0.1"
        connect_port = ra_port if ra_port else "5899"
        
        # Update Remote Apps Client
        self.ts_client.update_connection_info(connect_ip, connect_port)
        self.ts_client.api_key = self.config.get("apiKey", "")
        
        # Trigger reconnect logic (simplified: just restart app usually, but here we can try to reconnect)
        # For now, just notify user
        InfoBar.info(title='设置已保存', content="配置已保存，主题已更新", parent=self)

    def run_query(self, command_type):
        # Get Query Settings
        q_ip = self.settingsInterface.ipQuery.text()
        q_port = int(self.settingsInterface.portQuery.text())
        q_user = self.settingsInterface.userQuery.text()
        q_pass = self.settingsInterface.passQuery.text()
        
        asyncio.run_coroutine_threadsafe(
            self._async_run_query(q_ip, q_port, q_user, q_pass, command_type), 
            self.loop
        )

    async def _async_run_query(self, ip, port, user, password, cmd_type):
        try:
            if not self.query_client.connected:
                success, msg = await self.query_client.connect(ip, port, user, password)
                if not success:
                    self.signals.query_response.emit({"error": msg})
                    return

            data = {}
            if cmd_type == "clientlist":
                data = await self.query_client.get_client_list()
            elif cmd_type == "banlist":
                data = await self.query_client.get_ban_list()
            elif cmd_type == "tokenlist":
                data = await self.query_client.get_token_list()
            elif cmd_type == "serverinfo":
                data = await self.query_client.get_server_info()
            elif cmd_type == "channellist":
                data = await self.query_client.get_channel_list()
            elif cmd_type == "sendmsg":
                # Get message type index: 0=GM, 1=Server, 2=Channel, 3=Private
                idx = self.serverAdminInterface.comboMsgType.currentIndex()
                msg = self.serverAdminInterface.inputMsg.text()
                
                if not msg:
                    self.signals.query_response.emit({"error": "消息内容不能为空"})
                    return

                if idx == 0: # GM
                    data = await self.query_client.send_global_message(msg)
                else:
                    # Map index to targetmode: 
                    # Index 1 (Server) -> targetmode 3
                    # Index 2 (Channel) -> targetmode 2
                    # Index 3 (Private) -> targetmode 1
                    target_mode = 3
                    target_id = None
                    
                    if idx == 1: target_mode = 3
                    elif idx == 2: target_mode = 2
                    elif idx == 3: 
                        target_mode = 1
                        target_id = self.serverAdminInterface.inputMsgTarget.text()
                        if not target_id:
                            self.signals.query_response.emit({"error": "私聊需要提供目标 Client ID"})
                            return
                            
                    data = await self.query_client.send_text_message(target_mode, msg, target_id)

            elif cmd_type == "move_self":
                cid = self.serverAdminInterface.inputBotCid.text()
                pwd = self.serverAdminInterface.inputBotPwd.text()
                if not cid:
                    self.signals.query_response.emit({"error": "目标频道 ID 不能为空"})
                    return
                
                # 1. Get own client ID
                whoami_data = await self.query_client.whoami()
                if "error" in whoami_data and whoami_data["error"]:
                     self.signals.query_response.emit(whoami_data)
                     return
                
                # Parse client_id from whoami response
                # Response format: {'data': [{'client_id': '123', ...}], 'error': {}}
                my_clid = None
                if whoami_data.get("data"):
                    my_clid = whoami_data["data"][0].get("client_id")
                
                if not my_clid:
                    self.signals.query_response.emit({"error": "无法获取自身 Client ID"})
                    return

                # 2. Move self
                data = await self.query_client.client_move(my_clid, cid, pwd)

            elif cmd_type == "rename_self":
                new_name = self.serverAdminInterface.inputBotName.text()
                if not new_name:
                    self.signals.query_response.emit({"error": "新昵称不能为空"})
                    return
                
                data = await self.query_client.update_nickname(new_name)

            elif cmd_type == "kick":
                clid = self.serverAdminInterface.inputClid.text()
                if clid:
                    data = await self.query_client.kick_client(clid)
                else:
                    self.signals.query_response.emit({"error": "Client ID 不能为空"})
                    return
            elif cmd_type == "poke":
                clid = self.serverAdminInterface.inputClid.text()
                if clid:
                    data = await self.query_client.poke_client(clid)
                else:
                    self.signals.query_response.emit({"error": "Client ID 不能为空"})
                    return
            elif cmd_type == "custom":
                cmd = self.serverAdminInterface.inputCustom.text()
                if cmd:
                    data = await self.query_client.send_command(cmd)
                else:
                    self.signals.query_response.emit({"error": "命令不能为空"})
                    return
            
            self.signals.query_response.emit(data)
            
        except Exception as e:
            self.signals.query_response.emit({"error": str(e)})
            InfoBar.success(title='查询成功', content="数据已更新", parent=self)

    def show_status(self, text, type_):
        # Using InfoBar for status updates is cleaner than a permanent label
        if type_ == "success":
            InfoBar.success(title='状态更新', content=text, parent=self, position=InfoBarPosition.BOTTOM_RIGHT)
        elif type_ == "error":
            InfoBar.error(title='状态更新', content=text, parent=self, position=InfoBarPosition.BOTTOM_RIGHT)
        elif type_ == "warning":
            InfoBar.warning(title='状态更新', content=text, parent=self, position=InfoBarPosition.BOTTOM_RIGHT)

if __name__ == "__main__":
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    
    # Load initial theme from config
    init_theme = Theme.LIGHT
    cfg = load_config()
    t = cfg.get("theme", "Light")
    
    if t == "Dark": 
        init_theme = Theme.DARK
    elif t == "System": 
        init_theme = Theme.AUTO
        
    setTheme(init_theme)
    
    w = MainWindow()
    w.show()
    
    sys.exit(app.exec())
