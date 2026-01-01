from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QCheckBox
)
from qfluentwidgets import (
    SubtitleLabel, PrimaryPushButton, PushButton, BodyLabel, LineEdit,
    PasswordLineEdit, ComboBox
)

from app import __version__

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

        # Logging Settings
        self.groupLogging = QGroupBox("日志设置 (Logging)", self)
        self.layoutLogging = QFormLayout(self.groupLogging)
        self.comboLogLevel = ComboBox(self)
        self.comboLogLevel.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        level = str(self.config.get("log_level", "INFO")).upper()
        level_map = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
        self.comboLogLevel.setCurrentIndex(level_map.get(level, 1))
        self.saveLogToFileCb = QCheckBox("启用文件日志 (含轮转)", self)
        self.saveLogToFileCb.setChecked(self.config.get("file_logging", True))
        self.layoutLogging.addRow("日志级别:", self.comboLogLevel)
        self.layoutLogging.addRow("写入文件:", self.saveLogToFileCb)
        self.vBoxLayout.addWidget(self.groupLogging)
        
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
        self.portRemote.setText(str(self.config.get("remote_port", "")))
        self.apiKeyRemote = LineEdit(self)
        self.apiKeyRemote.setPlaceholderText("API Key")
        self.apiKeyRemote.setText(self.config.get("apiKey", ""))

        self.saveApiKeyCb = QCheckBox("保存 API Key 到本地", self)
        self.saveApiKeyCb.setChecked(self.config.get("persist_api_key", True))
        self.clearApiKeyBtn = PushButton("清除已保存的 API Key", self)
        self.clearApiKeyBtn.setFixedWidth(180)

        self.layoutRemote.addRow("IP 地址:", self.ipRemote)
        self.layoutRemote.addRow("端口 (Port):", self.portRemote)
        self.layoutRemote.addRow("API Key:", self.apiKeyRemote)
        self.layoutRemote.addRow("持久化:", self.saveApiKeyCb)
        self.layoutRemote.addRow(" ", self.clearApiKeyBtn)
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
        self.portQuery.setText(str(self.config.get("query_port", "")))
        self.userQuery = LineEdit(self)
        self.userQuery.setText(self.config.get("query_user", ""))
        self.userQuery.setPlaceholderText("serveradmin")
        self.passQuery = PasswordLineEdit(self)
        self.passQuery.setText(self.config.get("query_pass", ""))
        self.saveQueryPassCb = QCheckBox("保存密码到本地", self)
        self.saveQueryPassCb.setChecked(self.config.get("persist_query_password", False))
        self.clearQueryPassBtn = PushButton("清除已保存的密码", self)
        self.clearQueryPassBtn.setFixedWidth(180)
        self.layoutQuery.addRow("IP 地址:", self.ipQuery)
        self.layoutQuery.addRow("端口 (Port):", self.portQuery)
        self.layoutQuery.addRow("用户名:", self.userQuery)
        self.layoutQuery.addRow("密码:", self.passQuery)
        self.layoutQuery.addRow("持久化:", self.saveQueryPassCb)
        self.layoutQuery.addRow(" ", self.clearQueryPassBtn)
        self.vBoxLayout.addWidget(self.groupQuery)
        
        # Save Button
        self.saveBtn = PrimaryPushButton("保存并重连 (Save & Reconnect)", self)
        self.saveBtn.setFixedWidth(260)
        self.vBoxLayout.addWidget(self.saveBtn)
        self.vBoxLayout.addStretch(1)
        
        # Version Label
        self.versionLabel = BodyLabel(f"Version: {__version__}", self)
        self.versionLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vBoxLayout.addWidget(self.versionLabel)
