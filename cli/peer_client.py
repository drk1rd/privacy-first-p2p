import socket
import json
import os
from encryption_utils import load_private_key, decrypt_key_with_rsa, decrypt_and_reconstruct

SERVER_IP = input("Enter server IP address: ").strip()
PORT = 5000

def request_chunk(chunk_hash):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, PORT))
        request = json.dumps({ "hash": chunk_hash })
        s.sendall(request.encode())

        response = s.recv(65536).decode()
        reply = json.loads(response)

        if reply.get("status") == "OK":
            return reply["chunk"]
        return None

class SocketDHT:
    def __init__(self, real_hashes):
        self.cache = {}
        self.real_hashes = set(real_hashes)

    def retrieve(self, chunk_hash):
        if chunk_hash not in self.real_hashes:
            return None  # ignore decoys
        if chunk_hash in self.cache:
            return self.cache[chunk_hash]

        chunk = request_chunk(chunk_hash)
        if chunk:
            self.cache[chunk_hash] = chunk
        return chunk

def start_client():
    manifest_path = input("Enter path to manifest file: ").strip()
    priv_key_path = input("Enter path to your private key: ").strip()
    output_path = input("Enter output file path: ").strip()

    if not os.path.exists(manifest_path) or not os.path.exists(priv_key_path):
        print("Missing manifest or private key.")
        return

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    priv_key = load_private_key(priv_key_path)
    enc_key = bytes.fromhex(manifest["encrypted_key"])
    aes_key = decrypt_key_with_rsa(priv_key, enc_key)

    # Wrap server as a DHT-like interface
    real_hashes = manifest["chunks"]
    dht = SocketDHT(real_hashes)

    # If user gave a folder path, auto-generate a file path using manifest filename
    if os.path.isdir(output_path):
        output_path = os.path.join(output_path, "RECEIVED_" + manifest["filename"])

    decrypt_and_reconstruct(manifest, aes_key, dht, output_path)


if __name__ == "__main__":
    start_client()
