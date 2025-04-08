import os
import json
from cli.encryption_utils import (
    generate_rsa_keypair, load_private_key, load_public_key,
    encrypt_key_with_rsa, decrypt_key_with_rsa,
    chunk_and_encrypt, decrypt_and_reconstruct
)
from cli.p2p_node import DHT, PeerNode

dht = DHT()
peer_node = PeerNode(dht)

def upload_file():
    file_path = input("Enter file path: ").strip()
    pub_key_path = input("Enter receiver's public key path: ").strip()

    if not os.path.exists(file_path) or not os.path.exists(pub_key_path):
        print("Invalid paths.")
        return

    pub_key = load_public_key(pub_key_path)
    aes_key, manifest = chunk_and_encrypt(file_path)
    manifest["encrypted_key"] = encrypt_key_with_rsa(pub_key, aes_key).hex()

    for h, chunk in manifest["chunks"].items():
        dht.store(h, chunk)

    manifest_path = file_path + "_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)
    print(f"Uploaded and manifest saved at: {manifest_path}")

def download_file():
    manifest_path = input("Enter manifest path: ").strip()
    priv_key_path = input("Enter your private key path: ").strip()

    if not os.path.exists(manifest_path) or not os.path.exists(priv_key_path):
        print("Invalid paths.")
        return

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    priv_key = load_private_key(priv_key_path)
    enc_key = bytes.fromhex(manifest["encrypted_key"])
    aes_key = decrypt_key_with_rsa(priv_key, enc_key)

    decrypt_and_reconstruct(manifest, aes_key, dht, output_dir="receiver")

def cli():
    while True:
        print("\n--- P2P CLI Secure File Sharing ---")
        print("1. Upload file")
        print("2. Download file")
        print("3. Generate RSA Keypair")
        print("4. Connect to Peer")
        print("5. Exit")

        choice = input("Choose an option: ").strip()
        if choice == "1":
            upload_file()
        elif choice == "2":
            download_file()
        elif choice == "3":
            generate_rsa_keypair()
        elif choice == "4":
            ip = input("Peer IP: ")
            port = input("Peer Port: ")
            peer_node.connect_to_peer(ip, port)
        elif choice == "5":
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    cli()
