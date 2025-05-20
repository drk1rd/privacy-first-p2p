import zlib
import base64
import ssl
import socket
import json
import os
import random
import string
from hashlib import sha256
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Util.number import bytes_to_long, long_to_bytes


def compress(data):
    return zlib.compress(data)

def decompress(data):
    return zlib.decompress(data)

def generate_rsa_keypair():
    key = RSA.generate(2048)
    os.makedirs("keys",exist_ok=True)
    with open("keys/pvt.pem", "wb") as f:
        f.write(key.export_key())
    with open("keys/pub.pem", "wb") as f:
        f.write(key.publickey().export_key())
    print("RSA keypair generated.")

def load_public_key(path):
    with open(path, "rb") as f:
        return RSA.import_key(f.read())

def load_private_key(path):
    with open(path, "rb") as f:
        return RSA.import_key(f.read())

def encrypt_key_with_rsa(pub_key, aes_key):
  num = bytes_to_long(aes_key)
  encrypted = pow(num, priv_key.d, priv_key.n)
  return long_to_bytes(encrypted)

def decrypt_key_with_rsa(priv_key, enc_key):
  num = bytes_to_long(enc_key)
  decrypted = pow(num, pub_key.e, pub_key.n)
  return long_to_bytes(decrypted)

def request_chunk_from_peer(ip, port, chunk_hash):
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.connect((ip, int(port)))
      s.send(chunk_hash.encode())
      return s.recv(65536)
  except Exception as e:
    print(f"❌ Failed to fetch {chunk_hash} from {ip}:{port} – {e}")
    return None

def generate_dummy_data(size=128):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size)).encode()

def chunk_and_encrypt(filepath, add_decoys=True):
    with open(filepath, "rb") as f:
        data = f.read()

    chunk_size = 16 * 1024
    sub_chunk_size = 8 * 1024
    key = get_random_bytes(16)

    manifest = {
        "filename": os.path.basename(filepath),
        "chunks": [],
        "chunk_data": {},
        "nonces": {},
        "encrypted_key": "",
        "decoy_hashes": []
    }

    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        for j in range(0, len(chunk), sub_chunk_size):
            sub_chunk = chunk[j:j + sub_chunk_size]
            compressed = compress(sub_chunk)
            cipher = AES.new(key, AES.MODE_EAX)
            ciphertext, _ = cipher.encrypt_and_digest(compressed)
            chunk_hash = sha256(ciphertext).hexdigest()

            manifest["chunks"].append(chunk_hash)
            manifest["chunk_data"][chunk_hash] = base64.b64encode(ciphertext).decode()
            manifest["nonces"][chunk_hash] = base64.b64encode(cipher.nonce).decode()

    # Add fake/dummy chunks to the manifest
    if add_decoys:
        for _ in range(len(manifest["chunks"]) // 2):  # 50% dummy ratio
            fake_data = compress(generate_dummy_data())
            cipher = AES.new(key, AES.MODE_EAX)
            encrypted, _ = cipher.encrypt_and_digest(fake_data)
            fake_hash = sha256(encrypted).hexdigest()
            manifest["decoy_hashes"].append(fake_hash)
            manifest["chunk_data"][fake_hash] = base64.b64encode(encrypted).decode()
            manifest["nonces"][fake_hash] = base64.b64encode(cipher.nonce).decode()

    return key, manifest

def decrypt_and_reconstruct(manifest, key, dht, output_path):
    import threading
    from p2p_node import peer_node  # import here to avoid circular imports
    sub_chunks = {}

    def retrieve_and_decrypt(chunk_hash):
        # Step 1: Try local DHT first
        chunk_data = dht.retrieve(chunk_hash)
        if not chunk_data:
            # Step 2: Ask peers
            for ip, port in peer_node.peers:
                chunk_data = request_chunk_from_peer(ip, port, chunk_hash)
                if chunk_data:
                    dht.store(chunk_hash, chunk_data)  # cache it locally
                    break

        if not chunk_data:
            print(f"[!] Missing chunk: {chunk_hash}")
            return

        # Step 3: Decrypt and decompress
        ciphertext = chunk_data if isinstance(chunk_data, bytes) else base64.b64decode(chunk_data)
        nonce = base64.b64decode(manifest["nonces"][chunk_hash])
        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
        decrypted = cipher.decrypt(ciphertext)
        sub_chunks[chunk_hash] = decompress(decrypted)

    threads = []
    for chunk_hash in manifest["chunks"]:
        t = threading.Thread(target=retrieve_and_decrypt, args=(chunk_hash,))
        threads.append(t)
        t.start()

    # Simulate traffic noise (optional)
    for fake_hash in manifest.get("decoy_hashes", []):
        _ = dht.retrieve(fake_hash)

    for t in threads:
        t.join()

    with open(output_path, "wb") as f:
        for chunk_hash in manifest["chunks"]:
            f.write(sub_chunks[chunk_hash])
    print(f"✅ File reconstructed at: {output_path}")

def request_manifest_and_key(peer_ip, peer_port, filename):
    os.makedirs("manifest", exist_ok=True)
    os.makedirs("keys", exist_ok=True)

    def recv_all(sock, buffer_size=4096):
      data = b""
      while True:
        part = sock.recv(buffer_size)
        if not part:
          break
        data += part
      return data
    context = ssl.create_default_context(cafile="certificate/server_cert.pem")
    
    context.load_verify_locations("certificate/server_cert.pem")
    context.check_hostname = False
    context.verify_mode = ssl.CERT_REQUIRED

    with socket.create_connection((peer_ip, int(peer_port))) as sock:
        with context.wrap_socket(sock, server_hostname=peer_ip) as ssock:
            # Request manifest
            ssock.sendall(json.dumps({
                "action": "get_manifest",
                "filename": filename
            }).encode())

            # response = json.loads(ssock.recv(65536).decode())
            raw = recv_all(ssock).decode()
            response = json.loads(raw)

            if response["status"] != "OK":
                print("❌ Failed to get manifest.")
                return False
            manifest_path = f"manifest/{filename}_manifest.json"
            with open(manifest_path, "w") as f:
                f.write(response["data"])
            print(f"✅ Manifest saved to {manifest_path}")

    # Reconnect to fetch public key
    with socket.create_connection((peer_ip, int(peer_port))) as sock:
        with context.wrap_socket(sock, server_hostname=peer_ip) as ssock:
            ssock.sendall(json.dumps({
                "action": "get_key"
            }).encode())

            # response = json.loads(ssock.recv(8192).decode())
            raw = recv_all(ssock).decode()
            response = json.loads(raw)

            if response["status"] != "OK":
                print("❌ Failed to get public key.")
                return False
            key_path = "keys/pub.pem"
            with open(key_path, "w") as f:
                f.write(response["data"])
            print(f"✅ Public key saved to {key_path}")

    return True