# P2P Chunked File Sharing Test

## Overview
This project simulates a peer-to-peer (P2P) network that distributes and retrieves files in smaller, chunked pieces across multiple nodes.

## Files
- **p2p_node_chunked.py**: Defines the `P2PNode` class, handling node communication, data storage, and retrieval.
- **test.py**: Main script that sets up nodes, splits files into chunks, distributes chunks across nodes, and retrieves/reassembles the file.

## How to Run
1. Ensure Python 3.8+ is installed.
2. Install required packages (if any).
3. Run the main script:
   ```bash
   python P2p Chunk Test.py
   ```
4. The script generates a test file, distributes it, retrieves it, and verifies its integrity.

✅ If successful, you'll see a confirmation that the retrieved file matches the original.

