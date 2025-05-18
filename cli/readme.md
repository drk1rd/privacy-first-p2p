# 🔐 P2P Secure File Sharing (CLI-Based)

A CLI-based peer-to-peer secure file sharing system with advanced features for encryption, compression, and LAN-based socket transfer.

---

## 🚀 Features

- 📦 File chunking and sub-chunking  
- 🔐 AES encryption per sub-chunk  
- 🔑 RSA encryption for key exchange  
- 📉 Compression of sub-chunks  
- 🧵 Threaded parallel reconstruction  
- 🗃️ Simulated Distributed Hash Table (DHT)  
- 🌐 LAN-based P2P file transmission via sockets  

---

## FOR SIMULATING THE SENDER AND RECEIVER ON SAME PC 


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


## FOR USING P2P TRANSMISSION USING SOCKETS OVER LAN BETWEEN MULTIPLE NODES IN AN NETWORK OR OVER INTERNET

### 1. 📦 Install Dependencies (pip install -r requirements.txt)
### 2.     python main.py
### 3.   SELECT OPTION 3:  Generate RSA Keypair
This will create:

my_private.pem (keep safe) and transmit to receiver using a secure channel

my_public.pem (can be shared)

### 4. python main.py
# Select Option 1: Upload file

File name to upload (e.g., example.pdf)

Path to receiver’s public key (e.g., my_public.pem)

It Generate a manifest file: example.pdf_manifest.json (share to the receiver over a secure channel)

### 5.  Get Sender's Local IP
Windows:

bash
Copy
Edit
ipconfig
Look for: IPv4 Address

macOS/Linux:

bash
Copy
Edit
ifconfig

### 6. Start the Server (Sender Side)
python peer_server.py
Enter: ./example.pdf_manifest.json
✅ Server now listens for incoming chunk requests. (keep this file running on sender machine)

### 7. Start the Client (Receiver Side)
python peer_client.py
Enter: <Sender's LAN IP> (e.g., 192.168.1.15)
Enter: ./example.pdf_manifest.json (manifest path)
Enter: ./my_private.pem (private key path)
Enter: ./receiver (where you want the file to be downloaded) 

✅ Receiver pulls encrypted sub-chunks over LAN and reconstructs the file securely.
