from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from manager import manager
import json

router = APIRouter()

@router.websocket("/ws/admin")
async def admin_ws(websocket: WebSocket):
    await websocket.accept()
    manager.admin_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            cmd = json.loads(data)

            if cmd.get("action") == "ban":
                ip = cmd.get("ip")
                manager.blacklist_ips.add(ip)

                kicks = [
                    ws for ws, info in manager.active_connections.items()
                    if info["ip"] == ip
                ]

                for ws in kicks:
                    await ws.close(code=4003)
                    manager.disconnect(ws)

                await manager.notify_admin(f"Đã chặn IP: {ip}", "ban_success")

    except WebSocketDisconnect:
        manager.disconnect(websocket)