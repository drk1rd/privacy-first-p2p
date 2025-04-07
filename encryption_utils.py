from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
import os, json, base64
from hashlib import sha256

def generate_rsa_keypair():
    key = RSA.generate(2048)
    with open("my_private.pem", "wb") as f:
        f.write(key.export_key())
    with open("my_public.pem", "wb") as f:
        f.write(key.publickey().export_key())
    print("RSA keypair generated as 'my_private.pem' and 'my_public.pem'.")

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

def encrypt_file_chunks(filepath):
    with open(filepath, "rb") as f:
        data = f.read()

    chunk_size = 1024
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

    key = get_random_bytes(16)
    manifest = {
        "chunks": {},
        "filename": os.path.basename(filepath),
        "nonces": {}
    }

    for i, chunk in enumerate(chunks):
        cipher = AES.new(key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(chunk)
        chunk_hash = sha256(ciphertext).hexdigest()
        manifest["chunks"][chunk_hash] = base64.b64encode(ciphertext).decode()
        manifest["nonces"][chunk_hash] = base64.b64encode(cipher.nonce).decode()

    return key, manifest


def decrypt_file_chunks(manifest, key, output_dir="."):
    out_path = os.path.join(output_dir, "RECEIVED_" + manifest["filename"])
    with open(out_path, "wb") as f:
        for chunk_hash, chunk_data in manifest["chunks"].items():
            ciphertext = base64.b64decode(chunk_data)
            nonce = base64.b64decode(manifest["nonces"][chunk_hash])
            cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
            plaintext = cipher.decrypt(ciphertext)
            f.write(plaintext)
    print(f"File reconstructed: {out_path}")