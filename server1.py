import socket
import sys
import threading


clients = {}
clients_lock = threading.Lock()


def broadcast(message, sender=None):
    dead_sockets = []

    with clients_lock:
        for client_sock in clients:
            if sender is not None and client_sock is sender:
                continue
            try:
                client_sock.sendall((message + "\n").encode("utf8"))
            except OSError:
                dead_sockets.append(client_sock)

        for dead_sock in dead_sockets:
            clients.pop(dead_sock, None)


def send_to_client(client_sock, message):
    try:
        client_sock.sendall((message + "\n").encode("utf8"))
        return True
    except OSError:
        with clients_lock:
            clients.pop(client_sock, None)
        return False


def send_private(sender_sock, sender_name, target_name, body):
    with clients_lock:
        target_sock = None
        for sock, name in clients.items():
            if name == target_name:
                target_sock = sock
                break

    if target_sock is None:
        send_to_client(sender_sock, f"Khong tim thay nguoi dung: {target_name}")
        return

    sent = send_to_client(target_sock, f"[Rieng] {sender_name}: {body}")
    if sent:
        send_to_client(sender_sock, f"[Ban -> {target_name}] {body}")
    else:
        send_to_client(sender_sock, f"Khong gui duoc toi {target_name}")


def list_users(sender_sock):
    with clients_lock:
        names = list(clients.values())

    if not names:
        send_to_client(sender_sock, "Khong co nguoi dung nao dang online.")
        return

    send_to_client(sender_sock, "Online: " + ", ".join(names))


def handle_client(client, addr):
    nickname = f"{addr[0]}:{addr[1]}"
    reader = None

    try:
        reader = client.makefile("r", encoding="utf8", newline="\n")
        first_line = reader.readline()
        if not first_line:
            return

        first_message = first_line.strip()
        if first_message.startswith("NAME:"):
            proposed_name = first_message[5:].strip()
            if proposed_name:
                nickname = proposed_name

        with clients_lock:
            clients[client] = nickname

        print(f"{nickname} đã kết nối từ {addr}")
        send_to_client(client, "Da ket noi. Dung /list de xem user, @ten noi_dung de nhan rieng, quit de thoat.")
        broadcast(f"{nickname} đã tham gia cuộc trò chuyện.", sender=client)

        while True:
            line = reader.readline()
            if not line:
                break

            message = line.strip()
            if not message:
                continue

            if message.lower() == "quit":
                break

            if message.lower() == "/list":
                list_users(client)
                continue

            if message.startswith("@"):
                target_part, sep, body = message[1:].partition(" ")
                target_name = target_part.strip()
                body = body.strip()

                if not sep or not target_name or not body:
                    send_to_client(client, "Dung dung: @ten_client noi_dung")
                    continue

                send_private(client, nickname, target_name, body)
                continue

            print(f"{nickname}: {message}")
            broadcast(f"{nickname}: {message}", sender=client)
    except Exception as e:
        print(f"Lỗi với client {addr}: {e}")
    finally:
        with clients_lock:
            clients.pop(client, None)

        broadcast(f"{nickname} đã rời cuộc trò chuyện.", sender=client)
        if reader is not None:
            try:
                reader.close()
            except OSError:
                pass
        try:
            client.close()
        except OSError:
            pass
        print(f"Đã đóng kết nối với {nickname}")

def main():
    HOST = '0.0.0.0'  
    PORT = 8084        

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Cho phép tái sử dụng địa chỉ
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"Server đang lắng nghe trên {HOST}:{PORT}")
    except OSError as e:
        print(f"Lỗi: Không thể khởi động server: {e}")
        sys.exit(1)

    try:
        while True:
            client, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(client, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\nServer đang tắt...")
    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        with clients_lock:
            for client_sock in list(clients.keys()):
                try:
                    client_sock.close()
                except OSError:
                    pass
            clients.clear()

    s.close()

if __name__ == '__main__': 
    main()