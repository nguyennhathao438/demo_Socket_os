import json
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # {websocket: {"ip": "...", "username": "..."}}
        self.active_connections = {} 
        self.admin_connections = []
        self.blacklist_ips = set()

    async def connect(self, websocket: WebSocket, username: str, ip: str):
        if ip in self.blacklist_ips:
            await websocket.accept() # Chấp nhận rồi mới đóng được với code tùy chỉnh
            await websocket.close(code=4003)
            return False
        
        await websocket.accept()
        self.active_connections[websocket] = {"username": username, "ip": ip}
        await self.update_admin_ui()
        return True

    def disconnect(self, websocket: WebSocket):
        """Xóa kết nối khỏi danh sách mà không gây lỗi nếu đã xóa rồi"""
        if websocket in self.active_connections:
            del self.active_connections[websocket]
        
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Gửi tin nhắn (dạng dict) tới tất cả các client đang online"""
        # Chuyển dict sang JSON string để gửi qua websocket.send_text
        message_text = json.dumps(message)
        for connection in list(self.active_connections.keys()):
            try:
                await connection.send_text(message_text)
            except Exception:
                # Nếu gửi lỗi, coi như client đã mất kết nối
                self.disconnect(connection)

    async def update_admin_ui(self):
        if not self.admin_connections:
            return
        
        online_users = [
            {"ip": info["ip"], "username": info.get("username", "Ẩn danh")}
            for info in self.active_connections.values()
        ]
        
        payload = {
            "online_users": online_users,
            "banned_ips": list(self.blacklist_ips)
        }

        for admin in self.admin_connections:
            try:
                await admin.send_json(payload)
            except:
                if admin in self.admin_connections:
                    self.admin_connections.remove(admin)

    async def notify_admin(self, content: str, log_type: str = "admin_log", ip: str = None):
        for admin in self.admin_connections:
            try:
                await admin.send_json({
                    "type": "admin_log",
                    "content": content,
                    "log_type": log_type,
                    "ip": ip,
                    "online_count": len(self.active_connections)
                })
            except:
                pass
    # manager.py
    async def send_personal_message(self, message: dict, target_username: str):
        """Gửi tin nhắn cho một người cụ thể dựa trên username"""
        target_ws = None
        # Tìm WebSocket của người nhận
        for ws, info in self.active_connections.items():
            if info["username"] == target_username:
                target_ws = ws
                break

        if target_ws:
            try:
                await target_ws.send_json(message)
                return True
            except:
                self.disconnect(target_ws)
        return False

manager = ConnectionManager()