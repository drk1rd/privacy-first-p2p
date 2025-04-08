import zlib
import base64
from hashlib import sha256
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

def compress(data):
    return zlib.compress(data)

def decompress(data):
    return zlib.decompress(data)

def generate_rsa_keypair():
    key = RSA.generate(2048)
    with open("my_private.pem", "wb") as f:
        f.write(key.export_key())
    with open("my_public.pem", "wb") as f:
        f.write(key.publickey().export_key())
    print("RSA keypair generated.")

def load_public_key(path):
    with open(path, "rb") as f:
        return RSA.import_key(f.read())

def load_private_key(path):
    with open(path, "rb") as f:
        return RSA.import_key(f.read())

def encrypt_key_with_rsa(pub_key, aes_key):
    cipher = PKCS1_OAEP.new(pub_key)
    return cipher.encrypt(aes_key)

def decrypt_key_with_rsa(priv_key, enc_key):
    cipher = PKCS1_OAEP.new(priv_key)
    return cipher.decrypt(enc_key)

def chunk_and_encrypt(filepath):
    with open(filepath, "rb") as f:
        data = f.read()

    chunk_size = 16 * 1024
    sub_chunk_size = 8 * 1024
    key = get_random_bytes(16)

    manifest = {
        "filename": filepath.split("/")[-1],
        "chunks": {},
        "nonces": {},
        "encrypted_key": ""
    }

    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        for j in range(0, len(chunk), sub_chunk_size):
            sub_chunk = chunk[j:j + sub_chunk_size]
            compressed = compress(sub_chunk)
            cipher = AES.new(key, AES.MODE_EAX)
            ciphertext, _ = cipher.encrypt_and_digest(compressed)
            chunk_hash = sha256(ciphertext).hexdigest()
            manifest["chunks"][chunk_hash] = base64.b64encode(ciphertext).decode()
            manifest["nonces"][chunk_hash] = base64.b64encode(cipher.nonce).decode()

    return key, manifest

def decrypt_and_reconstruct(manifest, key, dht, output_dir="."):
    import os, threading
    sub_chunks = {}
    out_path = os.path.join(output_dir, "RECEIVED_" + manifest["filename"])
    os.makedirs(output_dir, exist_ok=True)

    def retrieve_and_decrypt(chunk_hash):
        ciphertext_b64 = dht.retrieve(chunk_hash)
        if not ciphertext_b64:
            print(f"Missing chunk: {chunk_hash}")
            return
        ciphertext = base64.b64decode(ciphertext_b64)
        nonce = base64.b64decode(manifest["nonces"][chunk_hash])
        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
        decrypted = cipher.decrypt(ciphertext)
        sub_chunks[chunk_hash] = decompress(decrypted)

    threads = []
    for chunk_hash in manifest["chunks"]:
        t = threading.Thread(target=retrieve_and_decrypt, args=(chunk_hash,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    with open(out_path, "wb") as f:
        for chunk_hash in sorted(sub_chunks):
            f.write(sub_chunks[chunk_hash])
    print(f"File reconstructed at: {out_path}")
