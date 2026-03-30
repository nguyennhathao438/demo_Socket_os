from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from manager import manager

router = APIRouter()

# routes/chat.py
@router.websocket("/ws/chat/{nickname}")
async def chat_ws(websocket: WebSocket, nickname: str):
    client_ip = websocket.headers.get("x-forwarded-for", websocket.client.host)
    
    if not await manager.connect(websocket, nickname, client_ip):
        return

    # --- THÔNG BÁO KẾT NỐI ---
    join_msg = {"type": "sys", "user": "Hệ thống", "message": f" {nickname} đã tham gia phòng chat"}
    await manager.broadcast(join_msg)
    await manager.notify_admin(f"Người dùng {nickname} đã vào", "connect", client_ip)

    # routes/chat.py
    try:
        while True:
            data = await websocket.receive_text()
            
            # Kiểm tra xem có phải tin nhắn riêng không (Ví dụ: @hoang chào bạn)
            if data.startswith("@"):
                try:
                    parts = data.split(" ", 1)
                    target_name = parts[0][1:] # Bỏ dấu @ để lấy tên
                    content = parts[1] if len(parts) > 1 else ""
                    
                    if content:
                        payload = {
                            "type": "private",
                            "from": nickname,
                            "to": target_name,
                            "message": content
                        }
                        # Gửi cho người nhận
                        success = await manager.send_personal_message(payload, target_name)
                        
                        if success:
                            # Gửi lại cho chính người gửi để họ thấy tin đã đi
                            await websocket.send_json(payload)
                            await manager.notify_admin(f"[PM] {nickname} -> {target_name}: {content}", "private_msg", client_ip)
                        else:
                            await websocket.send_json({
                                "type": "sys",
                                "user": "Hệ thống",
                                "message": f"Người dùng {target_name} không online."
                            })
                    continue # Bỏ qua phần broadcast bên dưới
                except Exception:
                    pass

            # Nếu không phải tin nhắn riêng, gửi công khai như cũ
            await manager.broadcast({
                "type": "chat",
                "user": nickname,
                "message": data
            })
    except WebSocketDisconnect:
        user = manager.disconnect(websocket)
        if user:
            await manager.notify_admin(f"{user['name']} đã thoát", "disconnect", client_ip)