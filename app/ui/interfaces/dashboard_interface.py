from datetime import datetime
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QCheckBox, QMenu, QApplication
)
from PySide6.QtGui import QColor, QAction, QKeySequence, QShortcut
from qfluentwidgets import (
    SubtitleLabel, PrimaryPushButton, PushButton, TextEdit, FluentIcon as FIF,
    SearchLineEdit, BodyLabel, LineEdit
)

from app.common.constants import EVENT_TRANSLATIONS, KEY_TRANSLATIONS
from app.common.i18n import tr

class DashboardInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("dashboardInterface")
        
        self.vBoxLayout = QVBoxLayout(self)
        
        # Title
        self.titleLabel = SubtitleLabel(tr("event_log"), self)
        self.vBoxLayout.addWidget(self.titleLabel)
        
        # Search Bar
        self.searchBar = SearchLineEdit(self)
        self.searchBar.setPlaceholderText(tr("search") + "...")
        self.searchBar.textChanged.connect(self.filter_tree)
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
        
        self.controlLayout.addWidget(self.autoScrollCb)
        self.controlLayout.addWidget(self.autoClearCb)
        self.controlLayout.addWidget(self.autoClearLabel)
        self.controlLayout.addWidget(self.autoClearInput)
        self.controlLayout.addStretch(1)
        self.vBoxLayout.addLayout(self.controlLayout)
        
        # Auto Clear Timer
        self.autoClearTimer = QTimer(self)
        self.autoClearTimer.timeout.connect(self.clear_events)
        
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
        self.inputLabel = SubtitleLabel(tr("send_custom_json"), self)
        self.vBoxLayout.addWidget(self.inputLabel)
        
        # JSON Input
        self.jsonInput = TextEdit(self)
        self.jsonInput.setPlaceholderText("在此输入 JSON 指令...")
        self.jsonInput.setPlainText('{\n    "type": "keyPress",\n    "payload": {\n        "button": "test",\n        "state": true\n    }\n}')
        self.jsonInput.setMaximumHeight(150)
        self.vBoxLayout.addWidget(self.jsonInput)
        
        # Buttons
        self.buttonLayout = QHBoxLayout()
        self.sendBtn = PrimaryPushButton(tr("send"), self)
        self.sendBtn.setIcon(FIF.SEND)
        self.clearBtn = PushButton(tr("clear"), self)
        self.clearBtn.setIcon(FIF.DELETE)
        
        self.buttonLayout.addWidget(self.sendBtn)
        self.buttonLayout.addWidget(self.clearBtn)
        self.buttonLayout.addStretch(1)
        self.vBoxLayout.addLayout(self.buttonLayout)
        
        # Connect buttons
        self.clearBtn.clicked.connect(self.clear_events)
    
    def clear_events(self):
        self.treeWidget.clear()
    
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
