from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from manager import manager
import json

router = APIRouter()

@router.websocket("/ws/admin")
async def admin_ws(websocket: WebSocket):
    await websocket.accept()
    manager.admin_connections.append(websocket)
    
    # Gửi cập nhật trạng thái ngay khi admin vừa kết nối
    await manager.update_admin_ui() 

    try:
        while True:
            data = await websocket.receive_text()
            cmd = json.loads(data)
            action = cmd.get("action")
            ip = cmd.get("ip")

            if cmd.get("action") == "ban":
                ip = cmd.get("ip")
                manager.blacklist_ips.add(ip)

                # Tìm các kết nối đang online có IP này
                kicks = [
                    ws for ws, info in manager.active_connections.items()
                    if info["ip"] == ip
                ]

                for ws in kicks:
                    try:
                        # Chỉ cần gửi lệnh close, việc xóa khỏi danh sách 
                        # hãy để hàm disconnect ở route của client đó lo.
                        await ws.close(code=4003)
                    except:
                        pass
                    # KHÔNG gọi manager.disconnect(ws) ở đây nữa để tránh xung đột

                await manager.notify_admin(f"Đã chặn IP: {ip}", "ban_success")
                await manager.update_admin_ui()

            elif action == "unban":
                if ip in manager.blacklist_ips:
                    manager.blacklist_ips.remove(ip)
                await manager.notify_admin(f"Đã mở chặn IP: {ip}", "unban_success")
            
            # Sau mỗi hành động, cập nhật lại danh sách cho Admin
            await manager.update_admin_ui()

    except WebSocketDisconnect:
        manager.admin_connections.remove(websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)