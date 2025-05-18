from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import json, os

def encrypt_manifest(data: dict, key: bytes, output_path: str):
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(json.dumps(data).encode())
    with open(output_path, "wb") as f:
        for item in [cipher.nonce, tag, ciphertext]:
            f.write(item)

def decrypt_manifest(key: bytes, input_path: str) -> dict:
    with open(input_path, "rb") as f:
        nonce = f.read(16)
        tag = f.read(16)
        ciphertext = f.read()
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    data = cipher.decrypt_and_verify(ciphertext, tag)
    return json.loads(data.decode())

def generate_aes_key() -> bytes:
    return get_random_bytes(16)  # 128-bit key
