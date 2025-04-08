class DHT:
    def __init__(self):
        self.storage = {}

    def store(self, key, value):
        self.storage[key] = value
        print(f"Stored: {key}")

    def retrieve(self, key):
        return self.storage.get(key)

class PeerNode:
    def __init__(self, dht):
        self.dht = dht
        self.peers = []

    def connect_to_peer(self, ip, port):
        print(f"Connected to {ip}:{port}")
        self.peers.append((ip, port))
