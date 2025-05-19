import socket
import json
from encryption_utils import chunk_and_encrypt, generate_rsa_keypair, load_public_key, encrypt_key_with_rsa
import os

HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 5000       # Change this if needed

def handle_client(conn, chunk_data):
    try:
        request = conn.recv(1024).decode()
        req = json.loads(request)
        action = req.get("action")

        if action == "get_manifest":
            filename = req.get("filename")
            path = f"manifest/{filename}_manifest.json"
            if os.path.exists(path):
                with open(path, "r") as f:
                    data = f.read()
                response = {
                    "status": "OK",
                    "data": data
                }
            else:
                response = {"status": "NOT_FOUND"}

        elif action == "get_key":
            path = "keys/pub.pem"
            if os.path.exists(path):
                with open(path, "r") as f:
                    data = f.read()
                response = {
                    "status": "OK",
                    "data": data
                }
            else:
                response = {"status": "NOT_FOUND"}

        else:
            chunk_hash = req.get("hash")
            if chunk_hash in chunk_data:
                response = {
                    "status": "OK",
                    "chunk": chunk_data[chunk_hash]
                }
            else:
                response = {"status": "NOT_FOUND"}

        conn.sendall(json.dumps(response).encode())

    except Exception as e:
        print(f"[!] Error handling client: {e}")
    finally:
        conn.close()

def start_server(manifest_path):
    if not os.path.exists(manifest_path):
        print("Manifest not found.")
        return

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    chunk_data = manifest["chunk_data"]
    print(f"[*] Loaded {len(chunk_data)} chunks.")
    print(f"[*] Server listening on port {PORT}...")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        while True:
            conn, addr = s.accept()
            print(f"[+] Connection from {addr}")
            handle_client(conn, chunk_data)

if __name__ == "__main__":
    manifest_file = input("Enter path to manifest file (e.g., myfile.pdf_manifest.json): ").strip()
    start_server(manifest_file)
