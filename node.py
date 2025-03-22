import asyncio
from kademlia.network import Server

class P2PNode:
    def __init__(self, port, bootstrap_node=None):
        self.port = port
        self.bootstrap_node = bootstrap_node
        self.node = Server()

    async def start(self):
        # Start node
        await self.node.listen(self.port)

        # If it's a new node, try bootstrapping to an existing node
        if self.bootstrap_node:
            try:
                print(f"Connecting to bootstrap node {self.bootstrap_node}")
                await self.node.bootstrap([self.bootstrap_node])
            except Exception as e:
                print(f"Failed to bootstrap: {e}")

        print(f"Node running on port {self.port}")

    async def store_file(self, key, value):
        print(f"Storing file: {key}")
        await self.node.set(key, value)

    async def retrieve_file(self, key):
        print(f"Retrieving file: {key}")
        result = await self.node.get(key)
        if result:
            print(f"File content: {result}")
        else:
            print("Failed to retrieve the file.")
        return result

    async def stop(self):
        self.node.stop()

# To run this node standalone (optional)
if __name__ == "__main__":
    import sys
    port = int(sys.argv[1])
    bootstrap = (sys.argv[2], int(sys.argv[3])) if len(sys.argv) == 4 else None
    node = P2PNode(port, bootstrap)

    asyncio.run(node.start())
