import asyncio
import logging

class ServerQueryClient:
    def __init__(self):
        self.reader = None
        self.writer = None
        self.connected = False

    async def connect(self, ip, port, username, password, server_port=9987):
        try:
            self.reader, self.writer = await asyncio.open_connection(ip, port)
            
            # Read welcome message
            await self.read_until(b"\n\r") # TS3
            await self.read_until(b"\n\r") # Welcome...

            # Login
            if username and password:
                await self.send_command(f"login {username} {password}")
            
            # Select server
            await self.send_command(f"use port={server_port}")
            
            self.connected = True
            return True, "Connected"
        except Exception as e:
            self.connected = False
            return False, str(e)

    async def disconnect(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.connected = False

    async def send_command(self, command):
        if not self.writer:
            raise Exception("Not connected")
        
        logging.debug(f"Query Send: {command}")
        self.writer.write(f"{command}\n".encode())
        await self.writer.drain()
        
        response = await self.read_response()
        logging.debug(f"Query Recv: {response}")
        return response

    async def read_until(self, separator):
        data = await self.reader.readuntil(separator)
        return data.decode()

    async def read_response(self):
        # ServerQuery responses end with "error id=0 msg=ok" (or similar error line)
        full_response = ""
        while True:
            line = await self.reader.readline()
            line_str = line.decode().strip()
            if not line_str:
                continue
            
            full_response += line_str + "\n"
            
            if line_str.startswith("error id="):
                break
        
        return self._parse_response(full_response)

    def _parse_response(self, raw_response):
        # Simple parser: returns list of dicts for data, and error dict
        lines = raw_response.strip().split('\n')
        data = []
        error = {}
        
        for line in lines:
            if line.startswith("error id="):
                error = self._parse_line(line)
            else:
                # Data line, might contain multiple items separated by |
                items = line.split('|')
                for item in items:
                    data.append(self._parse_line(item))
                    
        return {"data": data, "error": error}

    def _parse_line(self, line):
        # key=value key=value ...
        # Value escaping needs handling but for simple display we might skip complex unescaping for now
        # TS3 escaping: \s=space, \p=|, \/=/, \\=\
        result = {}
        parts = line.split(' ')
        for part in parts:
            if '=' in part:
                key, val = part.split('=', 1)
                result[key] = self._unescape(val)
            else:
                result[part] = None
        return result

    def _unescape(self, text):
        return text.replace(r'\s', ' ').replace(r'\p', '|').replace(r'\/', '/').replace(r'\\', '\\')

    def _escape(self, text):
        return text.replace('\\', r'\\').replace('/', r'\/').replace('|', r'\p').replace(' ', r'\s')

    # --- High Level Methods ---
    async def get_client_list(self):
        return await self.send_command("clientlist -uid -ip -groups")

    async def get_ban_list(self):
        return await self.send_command("banlist")

    async def get_token_list(self):
        return await self.send_command("tokenlist")

    async def get_server_info(self):
        return await self.send_command("serverinfo")

    async def get_channel_list(self):
        return await self.send_command("channellist")

    async def send_global_message(self, msg):
        return await self.send_command(f"gm msg={self._escape(msg)}")

    async def kick_client(self, clid, reason="Kicked"):
        return await self.send_command(f"clientkick reasonid=5 reasonmsg={self._escape(reason)} clid={clid}")

    async def poke_client(self, clid, msg="Poke!"):
        return await self.send_command(f"clientpoke msg={self._escape(msg)} clid={clid}")

    async def send_text_message(self, target_mode, msg, target_id=None):
        # target_mode: 1=Private, 2=Channel, 3=Server
        cmd = f"sendtextmessage targetmode={target_mode} msg={self._escape(msg)}"
        if target_id:
            cmd += f" target={target_id}"
        return await self.send_command(cmd)

    async def whoami(self):
        return await self.send_command("whoami")

    async def client_move(self, clid, cid, password=""):
        cmd = f"clientmove clid={clid} cid={cid}"
        if password:
            cmd += f" cpw={self._escape(password)}"
        return await self.send_command(cmd)

    async def update_nickname(self, new_name):
        return await self.send_command(f"clientupdate client_nickname={self._escape(new_name)}")
