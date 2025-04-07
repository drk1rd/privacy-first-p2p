import os
import sys
from encryption_utils import generate_rsa_keypair, load_public_key, load_private_key
from encryption_utils import encrypt_file_chunks, decrypt_file_chunks, encrypt_key_with_rsa, decrypt_key_with_rsa
from p2p_node import PeerNode, DHT
import json

dht = DHT()
peer_node = PeerNode(dht)

def upload_file():
    file_path = input("Enter path to file: ").strip()
    pub_key_path = input("Enter path to receiver's public key (e.g., receiver_public.pem): ").strip()

    if not os.path.exists(file_path) or not os.path.exists(pub_key_path):
        print("File or public key not found.")
        return

    receiver_pubkey = load_public_key(pub_key_path)
    aes_key, manifest = encrypt_file_chunks(file_path)
    encrypted_key = encrypt_key_with_rsa(receiver_pubkey, aes_key)
    manifest["encrypted_key"] = encrypted_key.hex()

    # Store chunks
    for chunk_hash, chunk_data in manifest["chunks"].items():
        dht.store(chunk_hash, chunk_data)

    # Write manifest
    manifest_path = file_path + "_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)
    print(f"File uploaded. Manifest saved to {manifest_path}")

def download_file():
    manifest_path = input("Enter path to manifest file: ").strip()
    private_key_path = input("Enter path to your private key (e.g., my_private.pem): ").strip()

    if not os.path.exists(manifest_path) or not os.path.exists(private_key_path):
        print("Manifest or private key not found.")
        return

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    priv_key = load_private_key(private_key_path)
    encrypted_key = bytes.fromhex(manifest["encrypted_key"])
    aes_key = decrypt_key_with_rsa(priv_key, encrypted_key)

    decrypt_file_chunks(manifest, aes_key, output_dir="receiver")


def cli():
    while True:
        print("\n--- P2P Secure File Sharing ---")
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
            ip = input("Enter peer IP: ").strip()
            port = input("Enter peer Port: ").strip()
            peer_node.connect_to_peer(ip, port)
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid option. Try again.")

if __name__ == "__main__":
    cli()