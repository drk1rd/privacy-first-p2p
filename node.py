import asyncio
from kademlia.network import Server

# Configuration
PORT = 8468
BOOTSTRAP_NODE = ("127.0.0.1", 8468)

async def run_node():
    # Create and start the node
    node = Server()
    await node.listen(PORT)

    # If this is the first node, bootstrap to itself
    if PORT == BOOTSTRAP_NODE[1]:
        print("This is the bootstrap node.")
    else:
        try:
            print(f"Connecting to bootstrap node at {BOOTSTRAP_NODE}")
            await node.bootstrap([BOOTSTRAP_NODE])
        except Exception as e:
            print(f"Bootstrap failed: {e}")

    # Store a file hash (key) and its "location" (value)
    file_key = "file:example.txt"
    file_data = "This is the content of the file!"
    print(f"Storing file under key '{file_key}'...")
    await node.set(file_key, file_data)

    # Retrieve the file content from the DHT
    print(f"Retrieving file from key '{file_key}'...")
    result = await node.get(file_key)
    print(f"File content: {result}")

    # Keep the node running
    await asyncio.sleep(3600)

# Run the node
asyncio.run(run_node())
