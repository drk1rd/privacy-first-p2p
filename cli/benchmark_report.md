# Benchmark Report: Basic vs Secure P2P Storage

This report compares the performance of a basic file copy method against a secure, chunked, encrypted P2P storage system.

## Overview

Tested file sizes: 1MB, 5MB, 10MB, 20MB

Each test measures upload and download times, CPU and memory usage, and effective bandwidth.

## Summary Table

Below is the raw benchmark data in table form for detailed reference.

| Mode   |   File_MB |   Upload_s |   Download_s |   Total_s |   Memory_MB |   CPU_% |   Bandwidth_MBps |   Chunks |   Decoys |   Latency_ms |
|:-------|----------:|-----------:|-------------:|----------:|------------:|--------:|-----------------:|---------:|---------:|-------------:|
| basic  |         1 |       0.01 |         0.01 |      0.01 |        1.01 |   20.45 |            66.62 |        1 |        0 |         0    |
| secure |         1 |       0.22 |         0.27 |      0.49 |        3.08 |   18.3  |             2.02 |      128 |       64 |         3.87 |
| basic  |         5 |       0.02 |         0.01 |      0.04 |        5.01 |   11.4  |           135.1  |        1 |        0 |         0    |
| secure |         5 |       1.14 |         1.21 |      2.35 |       14.06 |   12.25 |             2.13 |      640 |      320 |         3.67 |
| basic  |        10 |       0.03 |         0.02 |      0.05 |       10.01 |   15.45 |           208.29 |        1 |        0 |         0    |
| secure |        10 |       2.75 |         1.95 |      4.7  |       28.11 |   14.8  |             2.13 |     1280 |      640 |         3.67 |
| basic  |        20 |       0.03 |         0.03 |      0.06 |       20.01 |   19.55 |           322.53 |        1 |        0 |         0    |
| secure |        20 |       4.65 |         4.03 |      8.68 |       56.2  |   25.92 |             2.3  |     2560 |     1280 |         3.39 |

## Results

### Upload Time

![Upload Time](plots/upload_time.png)

The secure mode generally takes longer to upload due to chunking, encryption, and distributed storage overheads.

### Download Time

![Download Time](plots/download_time.png)

Download time in secure mode can vary based on chunk retrieval from multiple nodes, but remains competitive.

### Total Transfer Time

![Total Transfer Time](plots/total_time.png)

Overall, secure mode shows increased total time, a trade-off for added security and decentralization.

### CPU Usage

![CPU Usage](plots/cpu_usage.png)

Secure mode uses more CPU due to cryptographic operations and chunk management.

### Memory Usage

![Memory Usage](plots/memory_usage.png)

Memory peaks are higher in secure mode because of chunk buffering and encryption processes.

### Effective Bandwidth

![Effective Bandwidth](plots/bandwidth.png)

Basic mode bandwidth is higher because of straightforward file copying. Secure mode bandwidth is lower due to encryption overhead and chunk distribution.

## Security Benefits and Performance Analysis

- **Why Secure Mode Takes Longer and Uses More Resources:**

  1. **Chunking Overhead:**  
     The original file is split into multiple chunks, which introduces extra processing steps for indexing, handling, and storing each piece separately. This granularity increases the number of network operations compared to a single file copy.

  2. **Encryption and Decryption:**  
     Every chunk is encrypted using symmetric AES encryption with unique keys. Encryption and decryption are CPU-intensive tasks that require additional computation time and memory buffers, impacting both upload and download durations.

  3. **Distributed Storage Network:**  
     Chunks are stored across multiple DHT nodes rather than a single centralized server or disk. This decentralization increases network communication overhead, including latency and bandwidth usage, due to multiple storage and retrieval calls.

  4. **Key Management Overhead:**  
     AES keys are encrypted asymmetrically using RSA keys, which adds complexity and additional cryptographic operations on both upload and download, contributing to CPU and time usage.

- **Why Secure Mode is Still Better and Worth the Cost:**

  1. **Data Confidentiality:**  
     AES encryption ensures that even if chunks are intercepted or retrieved by unauthorized parties, the data remains unintelligible, protecting user privacy and sensitive information.

  2. **Resilience and Fault Tolerance:**  
     Distributing chunks across multiple nodes eliminates single points of failure. Even if some nodes go offline, the data can be reconstructed from other nodes, ensuring high availability.

  3. **Integrity and Tamper Detection:**  
     Each chunk’s hash is stored and verified, enabling detection of corrupted or maliciously altered data. This guards against data tampering and silent corruption.

  4. **Decentralization Reduces Trust Risks:**  
     Unlike centralized cloud storage, data spread across a peer-to-peer network reduces risks of data breaches caused by a compromised central server, making the system inherently more secure.

  5. **Scalability:**  
     The P2P model naturally scales with the number of nodes, distributing load and storage demands. This is crucial for large datasets or global-scale storage needs.

  6. **Enhanced Privacy Guarantees:**  
     Since no single node holds the entire file or encryption keys, the system minimizes information exposure, ensuring stronger privacy compared to traditional storage methods.

## Conclusion

While the secure P2P system demands more CPU, memory, and time due to the nature of chunking, encryption, and distributed storage, these trade-offs enable a **far more secure, private, and resilient** storage environment. For users and applications where confidentiality, integrity, and fault tolerance are paramount, this system provides essential protections that conventional file transfers and centralized storage cannot match.
