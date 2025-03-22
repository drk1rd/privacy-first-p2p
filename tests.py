import asyncio
import time
import os
import base64
import zlib
from p2p_node_chunked import P2PNode

CHUNK_SIZE = 16 * 1024  # Reduced chunk size to 16KB
SUB_CHUNK_SIZE = 8 * 1024  # Sub-chunk size to stay within 8KB limit

async def setup_nodes(num_nodes=5, base_port=8468):
    """Initialize nodes and connect them into a network."""
    nodes = []
    bootstrap_node = P2PNode(base_port)
    await bootstrap_node.start()
    nodes.append(bootstrap_node)

    for i in range(1, num_nodes):
        node = P2PNode(base_port + i, ("127.0.0.1", base_port))
        await node.start()
        nodes.append(node)

    time.sleep(3)  # Ensure nodes have enough time to join the DHT
    return nodes

async def store_sub_chunk_with_retry(node, key, sub_chunk, retries=3):
    """Try to store a sub-chunk with retries on different nodes."""
    for attempt in range(retries):
        try:
            await node.node.set(key, sub_chunk)
            return True
        except Exception as e:
            print(f"⚠️ Retry {attempt + 1}/{retries} failed to store {key}: {e}")
    return False

async def distribute_file(nodes, file_path):
    """Distribute a file to multiple nodes in chunked form."""
    with open(file_path, "rb") as file:
        file_data = file.read()

    num_chunks = (len(file_data) + CHUNK_SIZE - 1) // CHUNK_SIZE
    print(f"📦 File split into {num_chunks} chunks!")

    # Split, compress, encode, and further split into sub-chunks if needed
    for i in range(num_chunks):
        chunk_data = file_data[i * CHUNK_SIZE:(i + 1) * CHUNK_SIZE]
        compressed_chunk = zlib.compress(chunk_data)
        encoded_chunk = base64.b64encode(compressed_chunk).decode('utf-8')

        # Recursive sub-chunking to avoid failures
        def create_sub_chunks(data):
            """Recursive splitter to ensure all sub-chunks fit the size limit."""
            if len(data) <= SUB_CHUNK_SIZE:
                return [data]
            mid = len(data) // 2
            return create_sub_chunks(data[:mid]) + create_sub_chunks(data[mid:])

        sub_chunks = create_sub_chunks(encoded_chunk)

        # Store each sub-chunk on different nodes
        for sub_idx, sub_chunk in enumerate(sub_chunks):
            sub_key = f"chunk:{file_path}:{i}:{sub_idx}"
            node_index = (i + sub_idx) % len(nodes)
            node = nodes[node_index]
            if await store_sub_chunk_with_retry(node, sub_key, sub_chunk):
                print(f"✅ Stored sub-chunk {i}-{sub_idx} on Node {node_index + 1}")
            else:
                print(f"❌ Failed to store sub-chunk {i}-{sub_idx} on Node {node_index + 1}")

    return num_chunks

async def download_file_from_peers(nodes, file_name, total_chunks, output_path):
    """Retrieve chunks from multiple nodes in parallel and reconstruct the file."""
    last_node = nodes[-1]
    print(f"⚡ Node {len(nodes)} downloading file in parallel...")

    chunks = [None] * total_chunks

    async def fetch_chunk(i):
        chunk_key = f"chunk:{file_name}:{i}"
        print(f"🛠️ Retrieving chunk key: {chunk_key}")

        for attempt in range(3):
            for node in nodes:
                encoded_chunk = await node.node.get(chunk_key)

                # If chunk retrieval fails, try sub-chunks
                if not encoded_chunk:
                    sub_chunks = []
                    sub_idx = 0
                    while True:
                        sub_key = f"chunk:{file_name}:{i}:{sub_idx}"
                        sub_chunk = await node.node.get(sub_key)
                        if sub_chunk:
                            sub_chunks.append(sub_chunk)
                            sub_idx += 1
                        else:
                            break

                    if sub_chunks:
                        encoded_chunk = ''.join(sub_chunks)

                if encoded_chunk:
                    compressed_chunk = base64.b64decode(encoded_chunk)
                    chunk_data = zlib.decompress(compressed_chunk)
                    print(f"✅ Chunk {i} retrieved from Node {nodes.index(node) + 1} on attempt {attempt + 1}")
                    chunks[i] = chunk_data
                    return
        print(f"❌ Failed to retrieve chunk {i} after retries.")

    # Fetch all chunks in parallel
    await asyncio.gather(*[fetch_chunk(i) for i in range(total_chunks)])

    # Check if all chunks were retrieved
    if None in chunks:
        print("❌ Not all chunks were retrieved.")
        return False

    with open(output_path, "wb") as f:
        for chunk in chunks:
            f.write(chunk)

    print(f"✅ File reassembled and saved as '{output_path}'!")
    return True

async def run_chunked_file_sharing_test():
    """Complete end-to-end test for parallel chunk sharing."""
    nodes = await setup_nodes(5)
    file_path = "test_file.txt"
    output_path = "retrieved_file.txt"

    # Prepare a larger test file
    with open(file_path, "wb") as f:
        f.write(os.urandom(512 * 1024))  # 512KB random data

    total_chunks = await distribute_file(nodes, file_path)
    success = await download_file_from_peers(nodes, "test_file.txt", total_chunks, output_path)

    if success:
        # Verify file integrity
        with open(file_path, "rb") as original, open(output_path, "rb") as downloaded:
            assert original.read() == downloaded.read(), "❌ File content mismatch!"
        print("✅ Test passed: File retrieved successfully and content matches!")
    else:
        print("❌ Test failed: Not all chunks were retrieved.")

    # Shut down nodes
    for node in nodes:
        await node.stop()

asyncio.run(run_chunked_file_sharing_test())
