import asyncio
import time
import random
from p2p_node import P2PNode

async def run_file_test_with_random_source(num_nodes=5, file_path="test_file.txt", output_path="downloaded_file.txt"):
    print(f"🚀 Starting multi-node file-sharing test with {num_nodes} nodes...")

    nodes = []

    # Step 1: Start the bootstrap node
    bootstrap_port = 8468
    print("🌟 Starting Node 1 (Bootstrap Node)")
    bootstrap_node = P2PNode(bootstrap_port)
    await bootstrap_node.start()
    nodes.append(bootstrap_node)

    # Step 2: Start the remaining nodes connected to the bootstrap node
    for i in range(1, num_nodes):
        port = 8468 + i
        print(f"🔧 Starting Node {i+1}")
        node = P2PNode(port, ("127.0.0.1", bootstrap_port))
        await node.start()
        nodes.append(node)

    # Give time for nodes to sync
    time.sleep(2)

    # Step 3: Node 1 stores the file
    print("\n📝 Node 1 storing the file...")
    file_key = await nodes[0].store_file(file_path)

    # Step 4: Randomly replicate the file to other nodes
    print("\n🔄 Replicating file to random nodes...")
    nodes_to_replicate = random.sample(nodes[:-1], max(1, len(nodes)//2))  # Pick random nodes to hold the file
    for i, node in enumerate(nodes_to_replicate, start=1):
        print(f"🔁 Node {i+1} replicating the file...")
        await node.store_file(file_path)

    # Step 5: Last node retrieves the file (fetches from a random node)
    print(f"\n🔍 Node {num_nodes} fetching the file from the network...")
    last_node = nodes[-1]

    # Shuffle nodes to simulate random fetch source
    random.shuffle(nodes[:-1])
    retrieved_data = None

    # Try retrieving the file from nodes one by one
    for i, node in enumerate(nodes[:-1], start=1):
        print(f"⚡ Node {num_nodes} attempting to fetch from Node {i}")
        try:
            retrieved_data = await last_node.retrieve_file(file_key, output_path)
            if retrieved_data:
                print(f"✅ Node {num_nodes} successfully retrieved the file from Node {i}!")
                break
        except Exception as e:
            print(f"❌ Node {i} failed to serve the file. Error: {e}")

    # Step 6: Verify file content integrity
    if retrieved_data:
        with open(file_path, "rb") as original, open(output_path, "rb") as downloaded:
            assert original.read() == downloaded.read(), "❌ File content mismatch!"
        print("\n✅ Test passed: File retrieved successfully and content matches!")
    else:
        print("\n❌ Test failed: No node could provide the file.")

    # Step 7: Shut down all nodes
    print("\n🛑 Shutting down all nodes...")
    for i, node in enumerate(nodes, start=1):
        print(f"🛑 Stopping Node {i}")
        await node.stop()


# Prepare a test file
with open("test_file.txt", "w") as f:
    f.write("This is a test file for our P2P file-sharing network with random source selection!")

# Run the file-sharing test with 5 nodes
asyncio.run(run_file_test_with_random_source(5))
