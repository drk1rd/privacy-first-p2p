class DHT:
    def __init__(self):
        self.storage = {}

    def store(self, key, value):
        self.storage[key] = value

    def retrieve(self, key):
        return self.storage.get(key, None)

class PeerNode:
    def __init__(self, dht):
        self.dht = dht
        self.peers = []

    def connect_to_peer(self, ip, port):
        peer = f"{ip}:{port}"
        if peer not in self.peers:
            self.peers.append(peer)
            print(f"Connected to peer {peer}")
        else:
            print("Peer already connected.")