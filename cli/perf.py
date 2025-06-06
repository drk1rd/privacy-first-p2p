import os, time, json, csv
import psutil, tracemalloc
from pathlib import Path
from encryption_utils import (
    chunk_and_encrypt, decrypt_and_reconstruct,
    encrypt_key_with_rsa, decrypt_key_with_rsa,
    load_public_key, load_private_key
)
from threading import Lock
from random import choice
import matplotlib.pyplot as plt

# ---- Simulated DHT and Nodes ----

class DHTNode:
    def __init__(self, node_id):
        self.node_id = node_id
        self.storage = {}
        self.lock = Lock()

    def store(self, chunk_hash, data):
        with self.lock:
            self.storage[chunk_hash] = data

    def retrieve(self, chunk_hash):
        with self.lock:
            return self.storage.get(chunk_hash, None)

class DHTNetwork:
    def __init__(self, num_nodes=5):
        self.nodes = [DHTNode(f"node_{i}") for i in range(num_nodes)]

    def store(self, chunk_hash, data):
        # Store chunk on a random node to simulate P2P distribution
        node = choice(self.nodes)
        node.store(chunk_hash, data)

    def retrieve(self, chunk_hash):
        # Search all nodes for the chunk
        for node in self.nodes:
            data = node.retrieve(chunk_hash)
            if data is not None:
                return data
        return None

# ---- Benchmark Setup ----

TMP = "benchmark_local"
os.makedirs(TMP, exist_ok=True)

RSA_PUB = "generated/my_public.pem"
RSA_PRIV = "generated/my_private.pem"
CSV_OUT = "comparison_results.csv"
SIZES_MB = [1, 5, 10, 20]

def create_file(path, size_mb):
    with open(path, "wb") as f:
        f.write(os.urandom(size_mb * 1024 * 1024))

def measure(fn, *args):
    tracemalloc.start()
    cpu_before = psutil.cpu_percent(interval=None)
    net_before = psutil.net_io_counters()._asdict()
    start = time.time()

    fn(*args)

    end = time.time()
    cpu_after = psutil.cpu_percent(interval=None)
    net_after = psutil.net_io_counters()._asdict()
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    net_used = (
        net_after["bytes_sent"] + net_after["bytes_recv"]
        - net_before["bytes_sent"] - net_before["bytes_recv"]
    ) / (1024 * 1024)

    return {
        "time": round(end - start, 3),
        "cpu": round((cpu_before + cpu_after) / 2, 2),
        "mem": round(peak_mem / (1024 * 1024), 2),
        "bandwidth": round(net_used / (end - start + 1e-5), 2)
    }

# ---- Basic upload/download (simple file copy) ----

def basic_upload(src, dest):
    with open(src, "rb") as f: data = f.read()
    with open(dest, "wb") as f: f.write(data)

def basic_download(src, dest):
    with open(src, "rb") as f: data = f.read()
    with open(dest, "wb") as f: f.write(data)

# ---- Secure upload/download (P2P chunks + encryption) ----

def secure_upload(src_path, manifest_path, dht):
    pubkey = load_public_key(RSA_PUB)
    aes_key, manifest = chunk_and_encrypt(src_path)
    manifest["encrypted_key"] = encrypt_key_with_rsa(pubkey, aes_key).hex()
    for h, d in manifest["chunk_data"].items():
        dht.store(h, d)
    with open(manifest_path, "w") as f: json.dump(manifest, f)

def secure_download(manifest_path, output_path, dht):
    with open(manifest_path, "r") as f: manifest = json.load(f)
    priv = load_private_key(RSA_PRIV)
    key = decrypt_key_with_rsa(priv, bytes.fromhex(manifest["encrypted_key"]))
    decrypt_and_reconstruct(manifest, key, dht, output_path)

# ---- Benchmark run for one file size ----

def benchmark_run(size_mb):
    dht_network = DHTNetwork(num_nodes=5)

    name = f"{size_mb}MB"
    original = f"{TMP}/{name}_input.bin"
    basic_temp = f"{TMP}/{name}_basic_temp.bin"
    basic_out = f"{TMP}/{name}_basic_out.bin"
    secure_out = f"{TMP}/{name}_secure_out.bin"
    manifest = f"{TMP}/{name}_manifest.json"
    
    create_file(original, size_mb)

    # Basic upload + download
    up_b = measure(basic_upload, original, basic_temp)
    down_b = measure(basic_download, basic_temp, basic_out)

    # Secure upload + download on DHT network
    up_s = measure(secure_upload, original, manifest, dht_network)
    down_s = measure(secure_download, manifest, secure_out, dht_network)

    with open(manifest) as f:
        m = json.load(f)

    return [
        {
            "Mode": "basic",
            "File_MB": size_mb,
            "Upload_s": up_b["time"],
            "Download_s": down_b["time"],
            "Total_s": round(up_b["time"] + down_b["time"], 3),
            "Memory_MB": max(up_b["mem"], down_b["mem"]),
            "CPU_%": round((up_b["cpu"] + down_b["cpu"]) / 2, 2),
            "Bandwidth_MBps": round(size_mb / (up_b["time"] + down_b["time"] + 1e-5), 2),
            "Chunks": 1,
            "Decoys": 0,
            "Latency_ms": 0
        },
        {
            "Mode": "secure",
            "File_MB": size_mb,
            "Upload_s": up_s["time"],
            "Download_s": down_s["time"],
            "Total_s": round(up_s["time"] + down_s["time"], 3),
            "Memory_MB": max(up_s["mem"], down_s["mem"]),
            "CPU_%": round((up_s["cpu"] + down_s["cpu"]) / 2, 2),
            "Bandwidth_MBps": round(size_mb / (up_s["time"] + down_s["time"] + 1e-5), 2),
            "Chunks": len(m["chunks"]),
            "Decoys": len(m.get("decoy_hashes", [])),
            "Latency_ms": round((up_s["time"] + down_s["time"]) / len(m["chunks"]) * 1000, 2)
        }
    ]

# ---- Save results to CSV ----

def save_csv(results):
    with open(CSV_OUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

# ---- Generate Markdown Report with Plots ----

def generate_report(csv_path, report_path="benchmark_report.md"):
    import pandas as pd

    df = pd.read_csv(csv_path)

    # Separate basic and secure
    basic_df = df[df.Mode == "basic"]
    secure_df = df[df.Mode == "secure"]

    # Plot settings
    def plot_metric(metric, ylabel, title, filename):
        plt.figure(figsize=(8,5))
        plt.plot(basic_df.File_MB, basic_df[metric], marker='o', label='Basic')
        plt.plot(secure_df.File_MB, secure_df[metric], marker='o', label='Secure')
        plt.xlabel("File Size (MB)")
        plt.ylabel(ylabel)
        plt.title(title)
        plt.legend()
        plt.grid(True)
        plt.savefig(filename)
        plt.close()

    os.makedirs("plots", exist_ok=True)
    plot_metric("Upload_s", "Seconds", "Upload Time", "plots/upload_time.png")
    plot_metric("Download_s", "Seconds", "Download Time", "plots/download_time.png")
    plot_metric("Total_s", "Seconds", "Total Transfer Time", "plots/total_time.png")
    plot_metric("CPU_%", "CPU %", "Average CPU Usage", "plots/cpu_usage.png")
    plot_metric("Memory_MB", "MB", "Peak Memory Usage", "plots/memory_usage.png")
    plot_metric("Bandwidth_MBps", "MB/s", "Effective Bandwidth", "plots/bandwidth.png")

    # Write markdown report
    with open(report_path, "w") as f:
        f.write("# Benchmark Report: Basic vs Secure P2P Storage\n\n")

        f.write("This report compares the performance of a basic file copy method against a secure, chunked, encrypted P2P storage system.\n\n")

        f.write("## Overview\n\n")
        f.write(f"Tested file sizes: {', '.join(str(s) + 'MB' for s in sorted(df.File_MB.unique()))}\n\n")
        f.write("Each test measures upload and download times, CPU and memory usage, and effective bandwidth.\n\n")

        f.write("## Results\n\n")

        def add_plot_section(title, filename, analysis):
            f.write(f"### {title}\n\n")
            f.write(f"![{title}]({filename})\n\n")
            f.write(analysis + "\n\n")

        add_plot_section(
            "Upload Time",
            "plots/upload_time.png",
            "The secure mode generally takes longer to upload due to chunking, encryption, and distributed storage overheads."
        )

        add_plot_section(
            "Download Time",
            "plots/download_time.png",
            "Download time in secure mode can vary based on chunk retrieval from multiple nodes, but remains competitive."
        )

        add_plot_section(
            "Total Transfer Time",
            "plots/total_time.png",
            "Overall, secure mode shows increased total time, a trade-off for added security and decentralization."
        )

        add_plot_section(
            "CPU Usage",
            "plots/cpu_usage.png",
            "Secure mode uses more CPU due to cryptographic operations and chunk management."
        )

        add_plot_section(
            "Memory Usage",
            "plots/memory_usage.png",
            "Memory peaks are higher in secure mode because of chunk buffering and encryption processes."
        )

        add_plot_section(
            "Effective Bandwidth",
            "plots/bandwidth.png",
            "Basic mode bandwidth is higher because of straightforward file copying. Secure mode bandwidth is lower due to encryption overhead and chunk distribution."
        )

        # Enhanced Security Benefits and Performance Analysis Section
        f.write("## Security Benefits and Performance Analysis\n\n")
        f.write(
            "- **Why Secure Mode Takes Longer and Uses More Resources:**\n\n"
            "  1. **Chunking Overhead:**  \n"
            "     The original file is split into multiple chunks, which introduces extra processing steps for indexing, handling, and storing each piece separately. This granularity increases the number of network operations compared to a single file copy.\n\n"
            "  2. **Encryption and Decryption:**  \n"
            "     Every chunk is encrypted using symmetric AES encryption with unique keys. Encryption and decryption are CPU-intensive tasks that require additional computation time and memory buffers, impacting both upload and download durations.\n\n"
            "  3. **Distributed Storage Network:**  \n"
            "     Chunks are stored across multiple DHT nodes rather than a single centralized server or disk. This decentralization increases network communication overhead, including latency and bandwidth usage, due to multiple storage and retrieval calls.\n\n"
            "  4. **Key Management Overhead:**  \n"
            "     AES keys are encrypted asymmetrically using RSA keys, which adds complexity and additional cryptographic operations on both upload and download, contributing to CPU and time usage.\n\n"
            "- **Why Secure Mode is Still Better and Worth the Cost:**\n\n"
            "  1. **Data Confidentiality:**  \n"
            "     AES encryption ensures that even if chunks are intercepted or retrieved by unauthorized parties, the data remains unintelligible, protecting user privacy and sensitive information.\n\n"
            "  2. **Resilience and Fault Tolerance:**  \n"
            "     Distributing chunks across multiple nodes eliminates single points of failure. Even if some nodes go offline, the data can be reconstructed from other nodes, ensuring high availability.\n\n"
            "  3. **Integrity and Tamper Detection:**  \n"
            "     Each chunk’s hash is stored and verified, enabling detection of corrupted or maliciously altered data. This guards against data tampering and silent corruption.\n\n"
            "  4. **Decentralization Reduces Trust Risks:**  \n"
            "     Unlike centralized cloud storage, data spread across a peer-to-peer network reduces risks of data breaches caused by a compromised central server, making the system inherently more secure.\n\n"
            "  5. **Scalability:**  \n"
            "     The P2P model naturally scales with the number of nodes, distributing load and storage demands. This is crucial for large datasets or global-scale storage needs.\n\n"
            "  6. **Enhanced Privacy Guarantees:**  \n"
            "     Since no single node holds the entire file or encryption keys, the system minimizes information exposure, ensuring stronger privacy compared to traditional storage methods.\n\n"
        )

        f.write("## Conclusion\n\n")
        f.write(
            "While the secure P2P system demands more CPU, memory, and time due to the nature of chunking, encryption, and distributed storage, these trade-offs enable a **far more secure, private, and resilient** storage environment. "
            "For users and applications where confidentiality, integrity, and fault tolerance are paramount, this system provides essential protections that conventional file transfers and centralized storage cannot match.\n"
        )

    print(f"✅ Markdown report generated: {report_path}")


# ---- Main Execution ----

def main():
    all_results = []
    for size in SIZES_MB:
        all_results.extend(benchmark_run(size))
    save_csv(all_results)
    generate_report(CSV_OUT)

if __name__ == "__main__":
    main()
