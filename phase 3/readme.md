# 🔐 P2P Secure File Sharing (CLI-Based)

This is a CLI-based peer-to-peer secure file sharing system with the following features:
- File chunking and sub-chunking
- AES encryption per sub-chunk
- RSA encryption for key exchange
- Compression of sub-chunks
- Threaded parallel reconstruction
- Simulated DHT storage
- Simulated peer-to-peer connection

---

## 📁 Setup: Create Two Separate Folders

Create two folders to simulate the **Sender** and **Receiver**. Run the scripts from the root folder itself . 

### 1. 📦 Install Dependencies (pip install -r requirements.txt)
### 2.     python main.py
### 3.   SELECT OPTION 3:  Generate RSA Keypair

This will create:
my_private.pem
my_public.pem 
(Generate two pairs each for sender and receiver and move them to their respective folders)

### 4.  Select option 1: Upload file
Enter the file name to upload (e.g., example.pdf)
Enter the path to the receiver’s public key, e.g., receiver/my_public.pem
This will:

Encrypt and compress the file

Split it into chunks and sub-chunks

Store them in a simulated DHT

Create a manifest JSON file like example.pdf_manifest.json

### 5. Select option 2: Download file
Enter the path to the manifest (e.g., sender/example.pdf_manifest.json)

Enter the path to your private key (e.g., receiver/my_private.pem)

This will:

Retrieve chunks from DHT

Decrypt and decompress them in parallel

Reconstruct the file into the receiver/ directory as RECEIVED_example.pdf