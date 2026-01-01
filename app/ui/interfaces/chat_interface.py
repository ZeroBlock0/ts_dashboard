from datetime import datetime
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QTextEdit
)
from qfluentwidgets import (
    SubtitleLabel, PushButton, FluentIcon as FIF, SearchLineEdit, BodyLabel, LineEdit
)
from app.common.i18n import tr

class ChatInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("chatInterface")
        
        self.vBoxLayout = QVBoxLayout(self)
        
        self.titleLabel = SubtitleLabel(tr("chat_log"), self)
        self.vBoxLayout.addWidget(self.titleLabel)
        
        self.messages = [] # Store messages
        
        # Search Bar
        self.searchBar = SearchLineEdit(self)
        self.searchBar.setPlaceholderText(tr("search") + "...")
        self.searchBar.textChanged.connect(self.filter_chat)
        self.vBoxLayout.addWidget(self.searchBar)
        
        # Controls
        self.controlLayout = QHBoxLayout()
        self.autoScrollCb = QCheckBox(tr("auto_scroll"), self)
        self.autoScrollCb.setChecked(True)
        
        # Auto Clear Controls
        self.autoClearCb = QCheckBox(tr("auto_clear"), self)
        self.autoClearCb.setChecked(False)
        self.autoClearCb.stateChanged.connect(self.toggle_auto_clear)
        
        self.autoClearLabel = BodyLabel(tr("interval_sec") + ":", self)
        self.autoClearInput = LineEdit(self)
        self.autoClearInput.setText("60")
        self.autoClearInput.setFixedWidth(60)
        self.autoClearInput.textChanged.connect(self.update_auto_clear_interval)
        
        self.clearBtn = PushButton(tr("clear"), self)
        self.clearBtn.setIcon(FIF.DELETE)
        
        self.controlLayout.addWidget(self.autoScrollCb)
        self.controlLayout.addWidget(self.autoClearCb)
        self.controlLayout.addWidget(self.autoClearLabel)
        self.controlLayout.addWidget(self.autoClearInput)
        self.controlLayout.addStretch(1)
        self.controlLayout.addWidget(self.clearBtn)
        self.vBoxLayout.addLayout(self.controlLayout)
        
        # Auto Clear Timer
        self.autoClearTimer = QTimer(self)
        self.autoClearTimer.timeout.connect(self.clear_chat)
        
        self.chatLog = QTextEdit(self)
        self.chatLog.setReadOnly(True)
        self.chatLog.setStyleSheet("font-family: 'Microsoft YaHei'; font-size: 14px;")
        self.vBoxLayout.addWidget(self.chatLog)
        
        self.clearBtn.clicked.connect(self.clear_chat)

    def clear_chat(self):
        self.chatLog.clear()
        self.messages = []
    
    def toggle_auto_clear(self, state):
        if state == Qt.CheckState.Checked.value:
            self.update_auto_clear_interval()
        else:
            self.autoClearTimer.stop()
    
    def update_auto_clear_interval(self):
        if not self.autoClearCb.isChecked():
            return
        try:
            seconds = int(self.autoClearInput.text())
            if seconds > 0:
                self.autoClearTimer.start(seconds * 1000)
        except ValueError:
            pass

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
