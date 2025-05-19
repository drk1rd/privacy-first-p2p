import os
import json
from encryption_utils import (
    generate_rsa_keypair, load_private_key, load_public_key,
    encrypt_key_with_rsa, decrypt_key_with_rsa,
    chunk_and_encrypt, decrypt_and_reconstruct
)
from p2p_node import DHT, PeerNode

dht = DHT()
peer_node = PeerNode(dht)

def upload_file():
    file_path = input("Enter file name: ").strip()
    os.makedirs("input", exist_ok=True)
    file_path = "input/"+file_path
    # pub_key_path = input("Enter receiver's public key path: ").strip()
    pub_key_path = "keys/pub.pem"

    if not os.path.exists(file_path):
        print("File does not exist")
        return
    if not os.path.exists(pub_key_path):
        generate_rsa_keypair()

    pub_key_path = "keys/pub.pem"
    pub_key = load_public_key(pub_key_path)
    aes_key, manifest = chunk_and_encrypt(file_path)

    manifest["encrypted_key"] = encrypt_key_with_rsa(pub_key, aes_key).hex()

    for h in manifest["chunk_data"]:
        dht.store(h, manifest["chunk_data"][h])

    filename = os.path.basename(file_path)
    os.makedirs("manifest",exist_ok=True)
    manifest_path = "manifest/"+filename+ "_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    print(f"✅ Uploaded and manifest saved at: {manifest_path}")

def download_file():
    manifest_path = input("Enter manifest filename: ").strip()
    manifest_path = "manifest/" + manifest_path
    priv_key_path = "keys/pvt.pem"
    # priv_key_path = input("Enter your private key path: ").strip()
    # output_path = input("Enter path where output file should be saved: ").strip()
    os.makedirs("output",exist_ok=True)
    output_path = "output/"

    if not os.path.exists(manifest_path) :
        print("Manifest File does not exist")
        return

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    priv_key = load_private_key(priv_key_path)
    enc_key = bytes.fromhex(manifest["encrypted_key"])
    aes_key = decrypt_key_with_rsa(priv_key, enc_key)

    if os.path.isdir(output_path):
        filename = "RECEIVED_" + manifest["filename"]
        output_path = os.path.join(output_path, filename)

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
