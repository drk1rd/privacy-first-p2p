import threading
import socket


class DHT:
    def __init__(self):
        self.storage = {}

    def store(self, key, value):
        self.storage[key] = value
        print(f"Stored: {key}")

    def retrieve(self, key):
        return self.storage.get(key)
class PeerNode:
  def __init__(self, dht, host='0.0.0.0', port=5000):
    self.dht = dht
    self.peers = []
    self.host = host
    self.port = int(port)
    threading.Thread(target=self.run_server, daemon=True).start()

  def run_server(self):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((self.host, self.port))
    server_socket.listen()
    print(f"📡 PeerNode server listening on {self.host}:{self.port}")

    while True:
      client_socket, addr = server_socket.accept()
      threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

  def handle_client(self, client_socket):
    try:
      chunk_hash = client_socket.recv(1024).decode()
      chunk_data = self.dht.retrieve(chunk_hash)
      if chunk_data:
        client_socket.send(chunk_data)
      else:
        client_socket.send(b'')  # Not found
    except Exception as e:
      print(f"❌ Error handling client: {e}")
    finally:
      client_socket.close()

  def connect_to_peer(self, ip, port):
    print(f"🔌 Connected to {ip}:{port}")
    self.peers.append((ip, int(port)))

