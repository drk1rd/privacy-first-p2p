import os
import json
import socket
import ssl
from encryption_utils import (
    generate_rsa_keypair, load_private_key, load_public_key,
    encrypt_key_with_rsa, decrypt_key_with_rsa,
    chunk_and_encrypt, decrypt_and_reconstruct, request_manifest_and_key
)
from p2p_node import DHT, PeerNode

dht = DHT()
peer_node = PeerNode(dht)

def upload_file():
    file_path = input("Enter file name: ").strip()
    os.makedirs("input", exist_ok=True)
    file_path = "input/"+file_path
    # pub_key_path = input("Enter receiver's public key path: ").strip()
    pvt_key_path = "keys/pvt.pem"

    if not os.path.exists(file_path):
        print("File does not exist")
        return
    if not os.path.exists(pvt_key_path):
        generate_rsa_keypair()

    pvt_key_path = "keys/pvt.pem"
    pvt_key = load_public_key(pvt_key_path)
    aes_key, manifest = chunk_and_encrypt(file_path)

    manifest["encrypted_key"] = encrypt_key_with_rsa(pvt_key, aes_key).hex()

    for h in manifest["chunk_data"]:
        dht.store(h, manifest["chunk_data"][h])

    filename = os.path.basename(file_path)
    os.makedirs("manifest",exist_ok=True)
    manifest_path = "manifest/"+filename+ "_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    print(f"✅ Uploaded and manifest saved at: {manifest_path}")

def download_file():
    manifest_filename = input("Enter manifest filename (without _manifest.json): ").strip()
    manifest_path = f"manifest/{manifest_filename}_manifest.json"
    pub_key_path = "keys/pub.pem"
    os.makedirs("output", exist_ok=True)

    if not os.path.exists(manifest_path):
        print("📡 Manifest not found locally. Trying to fetch from peer.")
        peer_ip = input("Enter peer IP address: ").strip()
        peer_port = input("Enter peer port (e.g., 5000): ").strip()
        success = request_manifest_and_key(peer_ip, peer_port, manifest_filename)
        if not success:
            print("❌ Could not retrieve manifest and key.")
            return

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    priv_key = load_private_key(pub_key_path)
    enc_key = bytes.fromhex(manifest["encrypted_key"])
    aes_key = decrypt_key_with_rsa(priv_key, enc_key)

    output_path = os.path.join("output", "RECEIVED_" + manifest["filename"])
    decrypt_and_reconstruct(manifest, aes_key, dht, output_path)



def cli():
    while True:
        print("\n--- P2P CLI Secure File Sharing (Phase 3) ---")
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
