import os
import time
import json
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

# Create test files of various sizes
FILE_SIZES_MB = [1, 5, 10, 20]  # You can expand this list
TEST_DIR = "test_files"
RESULTS_FILE = "performance_results.json"

os.makedirs(TEST_DIR, exist_ok=True)

def generate_test_file(filepath, size_mb):
    with open(filepath, "wb") as f:
        f.write(os.urandom(size_mb * 1024 * 1024))

# Normal P2P transfer simulation
def basic_p2p_transfer(file_path, output_path):
    start = time.time()
    shutil.copyfile(file_path, output_path)
    end = time.time()
    return end - start

def measure_secure_p2p(file_path, pub_key_path, priv_key_path):
    dht = DHT()
    peer_node = PeerNode(dht)
    result = {}

    # Upload
    start_upload = time.time()
    tracemalloc.start()
    process = psutil.Process(os.getpid())

    aes_key, manifest = chunk_and_encrypt(file_path)
    encrypted_key = encrypt_key_with_rsa(load_public_key(pub_key_path), aes_key)
    manifest["encrypted_key"] = encrypted_key.hex()
    manifest["filename"] = os.path.basename(file_path)

    for h, v in manifest["chunk_data"].items():
        dht.store(h, v)

    peak_memory_upload = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    upload_time = time.time() - start_upload

    manifest_path = file_path + ".manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    # Download
    output_path = file_path + ".reconstructed"
    start_download = time.time()
    tracemalloc.start()
    enc_key = bytes.fromhex(manifest["encrypted_key"])
    aes_key = decrypt_key_with_rsa(load_private_key(priv_key_path), enc_key)
    decrypt_and_reconstruct(manifest, aes_key, dht, output_path)
    peak_memory_download = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    download_time = time.time() - start_download

    # Integrity check
    original_hash = sha256(open(file_path, 'rb').read()).hexdigest()
    reconstructed_hash = sha256(open(output_path, 'rb').read()).hexdigest()
    integrity = (original_hash == reconstructed_hash)

    result.update({
        "upload_time": round(upload_time, 3),
        "download_time": round(download_time, 3),
        "total_time": round(upload_time + download_time, 3),
        "real_chunks": len(manifest["chunks"]),
        "decoy_chunks": len(manifest.get("decoy_hashes", [])),
        "memory_upload_kb": peak_memory_upload // 1024,
        "memory_download_kb": peak_memory_download // 1024,
        "integrity_check": integrity,
        "final_manifest_size_kb": os.path.getsize(manifest_path) // 1024
    })

    # Cleanup
    os.remove(output_path)
    os.remove(manifest_path)

    return result

def run_benchmark():
    generate_rsa_keypair()
    priv_key_path = "my_private.pem"
    pub_key_path = "my_public.pem"

    results = {}

    for size_mb in FILE_SIZES_MB:
        test_file = os.path.join(TEST_DIR, f"test_{size_mb}MB.dat")
        generate_test_file(test_file, size_mb)

        print(f"\n▶ Testing {size_mb}MB file...")

        # Basic P2P
        basic_out = test_file + ".basic_copy"
        basic_time = basic_p2p_transfer(test_file, basic_out)
        os.remove(basic_out)

        # Secure P2P
        secure_result = measure_secure_p2p(test_file, pub_key_path, priv_key_path)

        results[size_mb] = {
            "basic_transfer_time": round(basic_time, 3),
            "secure_transfer": secure_result
        }

    # Save all results
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=4)

    print(f"\n✅ Benchmark complete. Results saved to '{RESULTS_FILE}'.")

if __name__ == "__main__":
    run_benchmark()
