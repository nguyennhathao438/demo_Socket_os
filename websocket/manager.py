import json
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}
        self.admin_connections = []
        self.blacklist_ips = set()

    async def connect(self, websocket: WebSocket, nickname: str, ip: str):
        if ip in self.blacklist_ips:
            await websocket.close(code=4003)
            return False
        await websocket.accept()
        self.active_connections[websocket] = {"name": nickname, "ip": ip}
        await self.notify_admin(f"User {nickname} đã vào", "connect", ip)
        return True

    def disconnect(self, websocket: WebSocket):
        user = self.active_connections.pop(websocket, None)
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)
        return user

    async def broadcast(self, message_data: dict):
        payload = json.dumps(message_data)

        # for connection in self.active_connections:
        #     await connection.send_text(payload)
            
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except:
                dead.append(connection)

        for d in dead:
            self.active_connections.pop(d, None)

    async def notify_admin(self, content, event_type, ip=""):
        payload = json.dumps({
            "type": "admin_log",
            "event": event_type,
            "content": content,
            "ip": ip,
            "online_count": len(self.active_connections)
        })
        for admin in self.admin_connections:
            await admin.send_text(payload)

manager = ConnectionManager()