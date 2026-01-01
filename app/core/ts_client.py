import asyncio
import json
import os
import websockets
import logging
from app import __version__

# Configure logging to file
# logging.basicConfig(
#     filename='ts_debug.log',
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     filemode='w'
# )

class TeamSpeakClient:
    def __init__(self, ip="127.0.0.1", port=5899, config_file="ts_config.json", persist_api_key=True):
        self.ip = ip
        self.port = port
        self.uri = f"ws://{ip}:{port}"
        self.config_file = config_file
        self.persist_api_key = persist_api_key
        self.api_key = self.load_api_key() if persist_api_key else ""
        self.websocket = None
        self.connected = False
        self.state = {}
        self.on_connect_callback = None
        self.on_disconnect_callback = None
        self.on_state_update_callback = None
        self.running = False

    def update_connection_info(self, ip, port):
        self.ip = ip
        self.port = port
        self.uri = f"ws://{ip}:{port}"

    def load_api_key(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("apiKey", "")
            except Exception:
                return ""
        return ""

    def save_api_key(self, key):
        self.api_key = key
        # 允许清除旧值，但在禁用持久化时不写入新值
        if not self.persist_api_key and key:
            return
        data = {}
        # Read existing config to preserve other settings
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                pass
        
        data["apiKey"] = key
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving API key: {e}")

    async def connect(self):
        if self.running:
            return
        self.running = True
        while self.running:
            try:
                async with websockets.connect(self.uri) as websocket:
                    self.websocket = websocket
                    self.connected = True
                    logging.info("Connected to TeamSpeak")
                    if self.on_connect_callback:
                        self.on_connect_callback()

                    await self.authenticate()
                    
                    # Keep listening for messages
                    async for message in websocket:
                        await self.handle_message(message)
            
            except Exception as e:
                logging.error(f"Connection error: {e}")
                self.connected = False
                if self.on_disconnect_callback:
                    self.on_disconnect_callback()

                if not self.running:
                    break
                await asyncio.sleep(5) # Retry delay

    async def stop(self):
        self.running = False
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass
        self.connected = False
        if self.on_disconnect_callback:
            self.on_disconnect_callback()

    async def authenticate(self):
        payload = {
            "type": "auth",
            "payload": {
                "identifier": "com.ts_dashboard.app",
                "version": __version__,
                "name": "TS Dashboard",
                "description": "Dashboard for TeamSpeak",
                "content": {
                    "apiKey": self.api_key
                }
            }
        }
        logging.info(f"Sending auth payload: {json.dumps(payload)}")
        await self.websocket.send(json.dumps(payload))

    async def handle_message(self, message):
        logging.info(f"Received message: {message}")
        data = json.loads(message)
        
        msg_type = data.get("type")
        
        if msg_type == "auth":
            status = data.get("status", {})
            if status.get("code") == 0:
                payload = data.get("payload", {})
                new_key = payload.get("apiKey")
                if new_key and new_key != self.api_key:
                    self.save_api_key(new_key)
                    logging.info("API Key saved")
                
                # Update state with initial data
                self.state = payload
                if self.on_state_update_callback:
                    self.on_state_update_callback(data)
            else:
                logging.error(f"Auth failed: {status.get('message')}")
        else:
            # For other events, pass them to the callback
            if self.on_state_update_callback:
                self.on_state_update_callback(data)

    def set_callbacks(self, on_connect, on_disconnect, on_state_update=None):
        self.on_connect_callback = on_connect
        self.on_disconnect_callback = on_disconnect
        self.on_state_update_callback = on_state_update

    async def send_hotkey(self, button_id, state=True):
        if self.websocket and self.connected:
            payload = {
                "type": "keyPress",
                "payload": {
                    "button": button_id,
                    "state": state
                }
            }
            await self.websocket.send(json.dumps(payload))
