import socket
import ssl
import json
import os

HOST = '0.0.0.0'
PORT = 5000

def handle_client(conn, chunk_data):
    try:
        request = conn.recv(1024).decode()
        req = json.loads(request)
        # ... same as before ...
        # Your existing handling code remains unchanged

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

    # Create SSL context for server
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(
        certfile="certificate/server_cert.pem",
        keyfile="certificate/server_key.pem"
    )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        print(f"[*] Server listening on port {PORT}...")

        while True:
            conn, addr = s.accept()
            print(f"[+] Connection from {addr}")

            try:
                # Wrap plain socket with SSL
                ssl_conn = context.wrap_socket(conn, server_side=True)
                handle_client(ssl_conn, chunk_data)
            except ssl.SSLError as e:
                print(f"[!] SSL error with client {addr}: {e}")
                conn.close()


if __name__ == "__main__":
    manifest_file = input("Enter path to manifest file (e.g., myfile.pdf_manifest.json): ").strip()
    start_server(manifest_file)
