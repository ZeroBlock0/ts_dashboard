import sys
import os
import json
import asyncio
import threading
import logging

from PySide6.QtCore import Slot, QTimer
from PySide6.QtGui import QIcon
from qfluentwidgets import (
    FluentWindow, FluentIcon as FIF, InfoBar, Theme, setTheme, InfoBarPosition
)

from app.common.config import load_config, get_config_path
from app.common.signals import WorkerSignals
from app.common.logger import QtLogHandler
from app.core.ts_client import TeamSpeakClient
from app.core.ts_query import ServerQueryClient

from app.ui.interfaces.dashboard_interface import DashboardInterface
from app.ui.interfaces.chat_interface import ChatInterface
from app.ui.interfaces.settings_interface import SettingsInterface
from app.ui.interfaces.server_admin_interface import ServerAdminInterface
from app.ui.interfaces.log_interface import LogInterface

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
        t = self.config.get("theme", "Light")
        
        def apply_theme_delayed():
            if t == "Dark":
                setTheme(Theme.DARK)
            elif t == "System":
                setTheme(Theme.AUTO)
            else:
                setTheme(Theme.LIGHT)

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

    def show_status(self, text, type_):
        # Using InfoBar for status updates is cleaner than a permanent label
        if type_ == "success":
            InfoBar.success(title='状态更新', content=text, parent=self, position=InfoBarPosition.BOTTOM_RIGHT)
        elif type_ == "error":
            InfoBar.error(title='状态更新', content=text, parent=self, position=InfoBarPosition.BOTTOM_RIGHT)
        elif type_ == "warning":
            InfoBar.warning(title='状态更新', content=text, parent=self, position=InfoBarPosition.BOTTOM_RIGHT)

