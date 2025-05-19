# File Transfer System Usage

## Local Mode

### Setup

Open **3 terminals** on the same machine.

#### Terminal A (Sender)
```bash
python3 main.py
```
- Select: `1` to upload
- File will be uploaded.

#### Terminal C (Peer Server - Manifest/Key Retrieval Host)
```bash
python3 peer_server.py
```
- Enter manifest file path
- Server will listen on port `5000`

#### Terminal B (Receiver)
```bash
python3 main.py
```
- Select: `2` to download
- Enter manifest file path
- *(Since manifest and key are available locally, retrieval is skipped)*
- File is reconstructed at the output path

---

## Over the Network

**Terminal A (Sender)** and **Terminal C (Peer Server)** stay the same as in Local Mode.

#### Terminal B (Receiver on different machine)
```bash
python3 main.py
```
- Select: `2` to download
- Enter manifest file path
- Enter peer IP (IP of C)
- Enter peer port (default: `5000`)
- File is reconstructed at the output path
