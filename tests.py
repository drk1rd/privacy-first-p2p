import asyncio
import time
from node import P2PNode

async def run_multi_node_test(num_nodes=5):
    print(f"🚀 Starting test with {num_nodes} nodes...")

    nodes = []

    # Step 1: Start the bootstrap node
    bootstrap_port = 8468
    bootstrap_node = P2PNode(bootstrap_port)
    await bootstrap_node.start()
    nodes.append(bootstrap_node)

    # Step 2: Start multiple peer nodes connected to the bootstrap node
    for i in range(1, num_nodes):
        port = 8468 + i
        node = P2PNode(port, ("127.0.0.1", bootstrap_port))
        await node.start()
        nodes.append(node)

    # Give time for nodes to sync
    time.sleep(2)

    # Step 3: Store data on the first node
    file_key = "file:test_multi_node.txt"
    file_content = "This is a test file for our multi-node P2P network!"
    print("\n📝 Storing file on bootstrap node...")
    await bootstrap_node.store_file(file_key, file_content)

    # Step 4: Attempt to retrieve data from **all** other nodes
    print("\n🔍 Retrieving file from all nodes...")
    for i, node in enumerate(nodes[1:], start=1):
        print(f"Node {i} trying to retrieve the file...")
        retrieved_data = await node.retrieve_file(file_key)
        assert retrieved_data == file_content, f"❌ Node {i} failed to retrieve correct data!"

    print("\n✅ Test passed: All nodes successfully retrieved the correct data!")

    # Step 5: Stop all nodes
    print("\n🛑 Shutting down all nodes...")
    for node in nodes:
        await node.stop()

# Run the test with 5 nodes
asyncio.run(run_multi_node_test(5))
