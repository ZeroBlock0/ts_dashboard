from datetime import datetime
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QFileDialog, QPlainTextEdit
)
from qfluentwidgets import (
    SubtitleLabel, PushButton, FluentIcon as FIF, InfoBar, SearchLineEdit,
    BodyLabel, LineEdit, isDarkTheme
)

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
        
        # Auto Clear Controls
        self.autoClearCb = QCheckBox("自动清空 (Auto Clear)", self)
        self.autoClearCb.setChecked(False)
        self.autoClearCb.stateChanged.connect(self.toggle_auto_clear)
        
        self.autoClearLabel = BodyLabel("间隔(秒):", self)
        self.autoClearInput = LineEdit(self)
        self.autoClearInput.setText("60")
        self.autoClearInput.setFixedWidth(60)
        self.autoClearInput.textChanged.connect(self.update_auto_clear_interval)
        
        self.exportBtn = PushButton("导出日志 (Export)", self)
        self.exportBtn.setIcon(FIF.SAVE)
        self.clearBtn = PushButton("清空 (Clear)", self)
        self.clearBtn.setIcon(FIF.DELETE)
        
        self.controlLayout.addWidget(self.autoScrollCb)
        self.controlLayout.addWidget(self.autoClearCb)
        self.controlLayout.addWidget(self.autoClearLabel)
        self.controlLayout.addWidget(self.autoClearInput)
        self.controlLayout.addStretch(1)
        self.controlLayout.addWidget(self.exportBtn)
        self.controlLayout.addWidget(self.clearBtn)
        self.vBoxLayout.addLayout(self.controlLayout)
        
        # Auto Clear Timer
        self.autoClearTimer = QTimer(self)
        self.autoClearTimer.timeout.connect(self.clear_logs)
        
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
