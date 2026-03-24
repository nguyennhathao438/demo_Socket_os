import socket
import threading


CLIENT_NAME = "client1"


def receive_messages(sock):
    reader = sock.makefile("r", encoding="utf8", newline="\n")
    try:
        for line in reader:
            msg = line.rstrip("\n")
            if msg:
                print("\n" + msg)
        print("\nMất kết nối tới server.")
    except OSError:
        pass
    finally:
        try:
            reader.close()
        except OSError:
            pass

def main():
    HOST = '127.0.0.1'  
    PORT = 8084

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = (HOST, PORT)
    
    print('Connecting to server at:', server_address)
    try:
        s.connect(server_address)
        print('Connected successfully!')
        s.sendall(f"NAME:{CLIENT_NAME}\n".encode("utf8"))
    except ConnectionRefusedError:
        print('Error: Could not connect to server. Make sure server is running.')
        return

    try:
        recv_thread = threading.Thread(target=receive_messages, args=(s,), daemon=True)
        recv_thread.start()

        while True:
            msg = input(f'{CLIENT_NAME}: ')
            s.sendall((msg + "\n").encode("utf8"))

            if msg.lower() == "quit":
                break
    finally:
        print('Closing connection')
        s.close()

if __name__ == '__main__': 
    main()