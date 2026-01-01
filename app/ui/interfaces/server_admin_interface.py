from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTreeWidget, QTreeWidgetItem, QHeaderView
)
from qfluentwidgets import (
    SubtitleLabel, PushButton, SearchLineEdit, BodyLabel, LineEdit, ComboBox,
    PasswordLineEdit, PrimaryPushButton
)
from app.common.i18n import tr

class ServerAdminInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("serverAdminInterface")
        self.vBoxLayout = QVBoxLayout(self)
        
        self.titleLabel = SubtitleLabel(tr("server_admin"), self)
        self.vBoxLayout.addWidget(self.titleLabel)
        
        # Search Bar
        self.searchBar = SearchLineEdit(self)
        self.searchBar.setPlaceholderText(tr("search") + "...")
        self.searchBar.textChanged.connect(self.filter_tree)
        self.vBoxLayout.addWidget(self.searchBar)
        
        # Group 1: Information & Lists
        self.groupInfo = QGroupBox(tr("info"), self)
        self.layoutInfo = QHBoxLayout(self.groupInfo)
        self.btnInfo = PushButton(tr("server_info"), self)
        self.btnChannels = PushButton(tr("channel_list"), self)
        self.btnClients = PushButton(tr("client_list"), self)
        self.btnBans = PushButton(tr("ban_list"), self)
        self.btnTokens = PushButton(tr("token_list"), self)
        
        self.layoutInfo.addWidget(self.btnInfo)
        self.layoutInfo.addWidget(self.btnChannels)
        self.layoutInfo.addWidget(self.btnClients)
        self.layoutInfo.addWidget(self.btnBans)
        self.layoutInfo.addWidget(self.btnTokens)
        self.layoutInfo.addStretch(1)
        self.vBoxLayout.addWidget(self.groupInfo)

        # Group 2: Management Actions
        self.groupAction = QGroupBox(tr("actions"), self)
        self.layoutAction = QVBoxLayout(self.groupAction)
        
        # Row 1: Message Center
        self.rowMsg = QHBoxLayout()
        self.comboMsgType = ComboBox(self)
        self.comboMsgType.addItems([tr("broadcast"), tr("server_chat"), tr("channel_chat"), tr("private_chat")])
        self.comboMsgType.setFixedWidth(160)
        self.comboMsgType.currentIndexChanged.connect(self.on_msg_type_changed)
        
        self.inputMsgTarget = LineEdit(self)
        self.inputMsgTarget.setPlaceholderText(tr("target_id"))
        self.inputMsgTarget.setFixedWidth(100)
        self.inputMsgTarget.setEnabled(False) # Default disabled
        
        self.inputMsg = LineEdit(self)
        self.inputMsg.setPlaceholderText(tr("message_content"))
        
        self.btnSendMsg = PrimaryPushButton(tr("send"), self)
        
        self.rowMsg.addWidget(self.comboMsgType)
        self.rowMsg.addWidget(self.inputMsgTarget)
        self.rowMsg.addWidget(self.inputMsg)
        self.rowMsg.addWidget(self.btnSendMsg)
        self.layoutAction.addLayout(self.rowMsg)
        
        # Row 2: Query Bot Move & Rename
        self.rowBotMove = QHBoxLayout()
        self.inputBotCid = LineEdit(self)
        self.inputBotCid.setPlaceholderText(tr("target_cid"))
        self.inputBotCid.setFixedWidth(120)
        self.inputBotPwd = PasswordLineEdit(self)
        self.inputBotPwd.setPlaceholderText(tr("channel_password"))
        self.inputBotPwd.setFixedWidth(120)
        self.btnBotMove = PushButton(tr("switch_channel"), self)
        
        self.inputBotName = LineEdit(self)
        self.inputBotName.setPlaceholderText(tr("bot_nickname"))
        self.inputBotName.setFixedWidth(120)
        self.btnBotRename = PushButton(tr("rename"), self)
        
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
        self.inputClid.setPlaceholderText(tr("target_clid"))
        self.inputClid.setFixedWidth(150)
        self.btnKick = PushButton(tr("kick"), self)
        
        self.inputPokeMsg = LineEdit(self)
        self.inputPokeMsg.setPlaceholderText(tr("poke_message"))
        self.inputPokeMsg.setFixedWidth(150)
        self.btnPoke = PushButton(tr("poke"), self)
        
        self.rowClient.addWidget(self.inputClid)
        self.rowClient.addWidget(self.btnKick)
        self.rowClient.addWidget(self.inputPokeMsg)
        self.rowClient.addWidget(self.btnPoke)
        self.rowClient.addStretch(1)
        self.layoutAction.addLayout(self.rowClient)
        
        # Row 4: Custom Command
        self.rowCustom = QHBoxLayout()
        self.inputCustom = LineEdit(self)
        self.inputCustom.setPlaceholderText("输入自定义 ServerQuery 命令 (例如: whoami)")
        self.btnSendCustom = PrimaryPushButton(tr("send"), self)
        self.rowCustom.addWidget(self.inputCustom)
        self.rowCustom.addWidget(self.btnSendCustom)
        self.layoutAction.addLayout(self.rowCustom)
        
        self.vBoxLayout.addWidget(self.groupAction)
        
        # Output Area
        self.outputTree = QTreeWidget(self)
        self.outputTree.setHeaderLabels(["键 / 事件 (Key / Event)", "值 (Value)"])
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
