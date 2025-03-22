import socket
import threading
import json

HOST = "127.0.0.1"
PORT = 65432
peers = []

def handle_client(conn, addr):
    print(f"New connection from {addr}")
    try:
        data = conn.recv(1024).decode()
        if data:
            message = json.loads(data)
            if message["type"] == "peer":
                if message["addr"] not in peers:
                    peers.append(message["addr"])
                    print(f"New peer added: {message['addr']}")
            elif message["type"] == "message":
                print(f"Message from {addr}: {message['content']}")
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Node listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

def connect_to_peer(peer_host, peer_port):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((peer_host, peer_port))
        client.send(json.dumps({"type": "peer", "addr": f"{HOST}:{PORT}"}).encode())
        client.close()
        if f"{peer_host}:{peer_port}" not in peers:
            peers.append(f"{peer_host}:{peer_port}")
    except Exception as e:
        print(f"Failed to connect to peer {peer_host}:{peer_port} — {e}")

def send_message(content):
    for peer in peers:
        try:
            peer_host, peer_port = peer.split(":")
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((peer_host, int(peer_port)))
            client.send(json.dumps({"type": "message", "content": content}).encode())
            client.close()
        except Exception as e:
            print(f"Failed to send message to {peer}: {e}")

threading.Thread(target=start_server).start()

while True:
    command = input("Enter 'connect [IP] [PORT]' or 'send [message]': ").strip()
    if command.startswith("connect"):
        _, ip, port = command.split()
        connect_to_peer(ip, int(port))
    elif command.startswith("send"):
        _, msg = command.split(" ", 1)
        send_message(msg)
