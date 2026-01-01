import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QCheckBox
)
from qfluentwidgets import (
    SubtitleLabel, PrimaryPushButton, PushButton, BodyLabel, LineEdit,
    PasswordLineEdit, ComboBox, InfoBar, InfoBarPosition
)

from app import __version__
from app.common.i18n import tr, get_current_language

class SettingsInterface(QWidget):
    def __init__(self, config=None, parent=None):
        super().__init__(parent=parent)
        self.config = config or {}
        self.setObjectName("settingsInterface")
        self.vBoxLayout = QVBoxLayout(self)
        
        self.titleLabel = SubtitleLabel(tr("settings"), self)
        self.vBoxLayout.addWidget(self.titleLabel)
        
        # Auto Connect Switch
        self.autoConnectCb = QCheckBox(tr("auto_connect"), self)
        self.autoConnectCb.setChecked(self.config.get("auto_connect", True))
        self.vBoxLayout.addWidget(self.autoConnectCb)
        
        # --- Row 1: Appearance & Logging ---
        self.row1Layout = QHBoxLayout()
        
        # Appearance Settings
        self.groupAppearance = QGroupBox(tr("appearance"), self)
        self.layoutAppearance = QFormLayout(self.groupAppearance)
        
        # Language Selection
        self.comboLang = ComboBox(self)
        self.comboLang.addItems(["简体中文 (zh_CN)", "English (en_US)"])
        curr_lang = get_current_language()
        if curr_lang == "en_US":
            self.comboLang.setCurrentIndex(1)
        else:
            self.comboLang.setCurrentIndex(0)
        self.layoutAppearance.addRow(f"{tr('language')}:", self.comboLang)

        self.comboTheme = ComboBox(self)
        self.comboTheme.addItems([f"{tr('light')} (Light)", f"{tr('dark')} (Dark)", f"{tr('auto')} (System)"])
        
        # Set initial selection based on config
        current_theme = self.config.get("theme", "Light")
        if current_theme == "Dark":
            self.comboTheme.setCurrentIndex(1)
        elif current_theme == "System":
            self.comboTheme.setCurrentIndex(2)
        else:
            self.comboTheme.setCurrentIndex(0)
            
        self.layoutAppearance.addRow(f"{tr('theme')}:", self.comboTheme)
        
        # Logging Settings
        self.groupLogging = QGroupBox(tr("logs"), self)
        self.layoutLogging = QFormLayout(self.groupLogging)
        self.comboLogLevel = ComboBox(self)
        self.comboLogLevel.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        level = str(self.config.get("log_level", "INFO")).upper()
        level_map = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
        self.comboLogLevel.setCurrentIndex(level_map.get(level, 1))
        self.saveLogToFileCb = QCheckBox(tr("file_logging"), self)
        self.saveLogToFileCb.setChecked(self.config.get("file_logging", True))
        self.layoutLogging.addRow(f"{tr('log_level')}:", self.comboLogLevel)
        self.layoutLogging.addRow(f"{tr('save')}:", self.saveLogToFileCb)
        
        # Add to Row 1
        self.row1Layout.addWidget(self.groupAppearance)
        self.row1Layout.addWidget(self.groupLogging)
        self.vBoxLayout.addLayout(self.row1Layout)
        
        # --- Row 2: Remote Apps & ServerQuery ---
        self.row2Layout = QHBoxLayout()
        
        # Remote Apps Settings
        self.groupRemote = QGroupBox(tr("remote_apps"), self)
        self.layoutRemote = QFormLayout(self.groupRemote)
        
        # Header with Connect Button and Status
        self.headerRemote = QWidget()
        self.headerLayoutRemote = QHBoxLayout(self.headerRemote)
        self.headerLayoutRemote.setContentsMargins(0, 0, 0, 0)
        self.btnConnectRemote = PushButton(tr("connect"), self)
        self.statusRemote = BodyLabel(tr("disconnect"), self)
        self.headerLayoutRemote.addWidget(self.btnConnectRemote)
        self.headerLayoutRemote.addWidget(self.statusRemote)
        self.headerLayoutRemote.addStretch(1)
        self.layoutRemote.addRow(tr("connection_status"), self.headerRemote)

        self.ipRemote = LineEdit(self)
        self.ipRemote.setPlaceholderText("127.0.0.1")
        self.ipRemote.setText(self.config.get("remote_ip", ""))
        self.portRemote = LineEdit(self)
        self.portRemote.setPlaceholderText("5899")
        self.portRemote.setText(str(self.config.get("remote_port", "")))
        self.apiKeyRemote = LineEdit(self)
        self.apiKeyRemote.setPlaceholderText("API Key")
        self.apiKeyRemote.setText(self.config.get("apiKey", ""))

        self.saveApiKeyCb = QCheckBox(tr("persist_api_key"), self)
        self.saveApiKeyCb.setChecked(self.config.get("persist_api_key", True))
        self.clearApiKeyBtn = PushButton(tr("clear"), self)
        self.clearApiKeyBtn.setFixedWidth(180)

        self.layoutRemote.addRow(f"{tr('host')}:", self.ipRemote)
        self.layoutRemote.addRow(f"{tr('port')}:", self.portRemote)
        self.layoutRemote.addRow(f"{tr('api_key')}:", self.apiKeyRemote)
        self.layoutRemote.addRow(f"{tr('save')}:", self.saveApiKeyCb)
        self.layoutRemote.addRow(" ", self.clearApiKeyBtn)
        
        # ServerQuery Settings
        self.groupQuery = QGroupBox(tr("server_query"), self)
        self.layoutQuery = QFormLayout(self.groupQuery)
        
        # Header with Connect Button and Status
        self.headerQuery = QWidget()
        self.headerLayoutQuery = QHBoxLayout(self.headerQuery)
        self.headerLayoutQuery.setContentsMargins(0, 0, 0, 0)
        self.btnConnectQuery = PushButton(tr("connect"), self)
        self.statusQuery = BodyLabel(tr("disconnect"), self)
        self.headerLayoutQuery.addWidget(self.btnConnectQuery)
        self.headerLayoutQuery.addWidget(self.statusQuery)
        self.headerLayoutQuery.addStretch(1)
        self.layoutQuery.addRow(tr("connection_status"), self.headerQuery)

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
        self.saveQueryPassCb = QCheckBox(tr("persist_password"), self)
        self.saveQueryPassCb.setChecked(self.config.get("persist_query_password", False))
        self.clearQueryPassBtn = PushButton(tr("clear"), self)
        self.clearQueryPassBtn.setFixedWidth(180)
        self.layoutQuery.addRow(f"{tr('host')}:", self.ipQuery)
        self.layoutQuery.addRow(f"{tr('port')}:", self.portQuery)
        self.layoutQuery.addRow(f"{tr('username')}:", self.userQuery)
        self.layoutQuery.addRow(f"{tr('password')}:", self.passQuery)
        self.layoutQuery.addRow(f"{tr('save')}:", self.saveQueryPassCb)
        self.layoutQuery.addRow(" ", self.clearQueryPassBtn)
        
        # Add to Row 2
        self.row2Layout.addWidget(self.groupRemote)
        self.row2Layout.addWidget(self.groupQuery)
        self.vBoxLayout.addLayout(self.row2Layout)
        
        # About
        self.groupAbout = QGroupBox(tr("about"), self)
        self.layoutAbout = QFormLayout(self.groupAbout)
        self.versionLabel = BodyLabel(f"{tr('version')}: {__version__}", self)
        self.repoBtn = PushButton(tr("repo"), self)
        self.repoBtn.setFixedWidth(200)
        self.repoBtn.clicked.connect(lambda: os.startfile("https://github.com/ZeroBlock0/ts_dashboard"))
        self.layoutAbout.addRow(self.versionLabel)
        self.layoutAbout.addRow(self.repoBtn)
        self.vBoxLayout.addWidget(self.groupAbout)

        self.vBoxLayout.addStretch(1)

        # Connect signals
        self.comboLang.currentIndexChanged.connect(self._on_language_changed)

        # Save Button
        self.saveBtn = PrimaryPushButton(tr("save"), self)
        self.saveBtn.setFixedWidth(260)
        self.vBoxLayout.addWidget(self.saveBtn, 0, Qt.AlignmentFlag.AlignCenter)
        self.vBoxLayout.addStretch(1)

    def _on_language_changed(self, index):
        lang_code = "en_US" if index == 1 else "zh_CN"
        if lang_code != self.config.get("language", "zh_CN"):
            self.config["language"] = lang_code
            # Notify user about restart
            InfoBar.warning(
                title=tr("restart_required"),
                content=tr("restart_required_msg"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self
            )
