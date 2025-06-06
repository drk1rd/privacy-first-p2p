import os
import time
import csv
import shutil
import psutil
import tracemalloc
from hashlib import sha256
from encryption_utils import (
    generate_rsa_keypair,
    load_private_key,
    load_public_key,
    encrypt_key_with_rsa,
    decrypt_key_with_rsa,
    chunk_and_encrypt,
    decrypt_and_reconstruct
)
from p2p_node import DHT, PeerNode

# === Configuration ===
FILE_SIZES_MB = [1, 5, 10, 20]  # Customize sizes
TEST_DIR = "test_files"
CSV_FILE = "p2p_benchmark_results.csv"

os.makedirs(TEST_DIR, exist_ok=True)

def generate_test_file(path, size_mb):
    with open(path, "wb") as f:
        f.write(os.urandom(size_mb * 1024 * 1024))

def basic_p2p_transfer(src, dest):
    start = time.time()
    tracemalloc.start()
    shutil.copyfile(src, dest)
    peak_mem = tracemalloc.get_traced_memory()[1] // 1024
    tracemalloc.stop()
    duration = time.time() - start
    return duration, peak_mem

def secure_p2p_transfer(src, pub_key_path, priv_key_path):
    dht = DHT()
    peer_node = PeerNode(dht)

    result = {}

    # Upload
    start_up = time.time()
    tracemalloc.start()
    aes_key, manifest = chunk_and_encrypt(src)
    encrypted_key = encrypt_key_with_rsa(load_public_key(pub_key_path), aes_key)
    manifest["encrypted_key"] = encrypted_key.hex()
    manifest["filename"] = os.path.basename(src)
    for h, v in manifest["chunk_data"].items():
        dht.store(h, v)
    peak_mem_up = tracemalloc.get_traced_memory()[1] // 1024
    tracemalloc.stop()
    upload_time = time.time() - start_up

    # Save manifest
    manifest_path = src + ".manifest.json"
    with open(manifest_path, "w") as f:
        import json
        json.dump(manifest, f)

    # Download
    start_down = time.time()
    tracemalloc.start()
    enc_key = bytes.fromhex(manifest["encrypted_key"])
    aes_key = decrypt_key_with_rsa(load_private_key(priv_key_path), enc_key)
    output_path = src + ".reconstructed"
    decrypt_and_reconstruct(manifest, aes_key, dht, output_path)
    peak_mem_down = tracemalloc.get_traced_memory()[1] // 1024
    tracemalloc.stop()
    download_time = time.time() - start_down

    # Integrity check
    hash_orig = sha256(open(src, "rb").read()).hexdigest()
    hash_recv = sha256(open(output_path, "rb").read()).hexdigest()
    integrity = hash_orig == hash_recv

    # Manifest size
    manifest_size = os.path.getsize(manifest_path) // 1024

    # Cleanup
    os.remove(manifest_path)
    os.remove(output_path)

    result.update({
        "upload_time": round(upload_time, 3),
        "download_time": round(download_time, 3),
        "total_time": round(upload_time + download_time, 3),
        "real_chunks": len(manifest["chunks"]),
        "decoy_chunks": len(manifest.get("decoy_hashes", [])),
        "memory_upload_kb": peak_mem_up,
        "memory_download_kb": peak_mem_down,
        "manifest_size_kb": manifest_size,
        "integrity_check": integrity
    })

    return result

def write_csv_header(file_path):
    with open(file_path, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "File_Size_MB",
            "Mode",
            "Total_Time_s",
            "Upload_Time_s",
            "Download_Time_s",
            "Memory_Usage_KB",
            "Real_Chunks",
            "Decoy_Chunks",
            "Manifest_Size_KB",
            "Integrity_OK"
        ])

def append_csv_row(file_path, row):
    with open(file_path, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)

def run_benchmark():
    print("🔐 Generating RSA keypair...")
    generate_rsa_keypair()
    priv_key = "my_private.pem"
    pub_key = "my_public.pem"

    write_csv_header(CSV_FILE)

    for size in FILE_SIZES_MB:
        file_path = os.path.join(TEST_DIR, f"sample_{size}MB.bin")
        generate_test_file(file_path, size)

        print(f"\n📦 Testing file size: {size} MB")

        # Basic P2P
        dest_path = file_path + ".copy"
        basic_time, basic_mem = basic_p2p_transfer(file_path, dest_path)
        append_csv_row(CSV_FILE, [
            size, "Basic", round(basic_time, 3), "-", "-", basic_mem,
            "-", "-", "-", "TRUE"
        ])
        os.remove(dest_path)

        # Secure P2P
        secure_stats = secure_p2p_transfer(file_path, pub_key, priv_key)
        append_csv_row(CSV_FILE, [
            size, "Secure",
            secure_stats["total_time"],
            secure_stats["upload_time"],
            secure_stats["download_time"],
            secure_stats["memory_upload_kb"] + secure_stats["memory_download_kb"],
            secure_stats["real_chunks"],
            secure_stats["decoy_chunks"],
            secure_stats["manifest_size_kb"],
            str(secure_stats["integrity_check"]).upper()
        ])

    print(f"\n✅ All tests complete. Results saved to: {CSV_FILE}")

if __name__ == "__main__":
    run_benchmark()
