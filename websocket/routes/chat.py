from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from manager import manager

router = APIRouter()

@router.websocket("/ws/chat/{nickname}")
async def chat_ws(websocket: WebSocket, nickname: str):
    # client_ip = websocket.client.host
    client_ip = websocket.headers.get("x-forwarded-for", websocket.client.host)
    if not await manager.connect(websocket, nickname, client_ip):
        return

    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast({
                "type": "chat",
                "user": nickname,
                "message": data
            })
            await manager.notify_admin(f"{nickname}: {data}", "message", client_ip)
    except WebSocketDisconnect:
        user = manager.disconnect(websocket)
        if user:
            await manager.notify_admin(f"{user['name']} đã thoát", "disconnect", client_ip)