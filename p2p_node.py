import asyncio
from kademlia.network import Server

class P2PNode:
    def __init__(self, port, bootstrap_node=None):
        self.port = port
        self.bootstrap_node = bootstrap_node
        self.node = Server()

    async def start(self):
        # Start the node
        await self.node.listen(self.port)

        # If there's a bootstrap node, connect to it
        if self.bootstrap_node:
            try:
                print(f"🔗 Connecting to bootstrap node {self.bootstrap_node}")
                await self.node.bootstrap([self.bootstrap_node])
            except Exception as e:
                print(f"⚠️ Failed to bootstrap: {e}")

        print(f"✅ Node running on port {self.port}")

    async def store_file(self, file_path):
        """Reads a file and stores its content in the DHT."""
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
            file_key = f"file:{file_path.split('/')[-1]}"
            print(f"📁 Storing file '{file_path}' under key '{file_key}'...")
            await self.node.set(file_key, file_content)
            print("✅ File stored successfully!")
            return file_key
        except Exception as e:
            print(f"❌ Failed to store file: {e}")
            return None

    async def retrieve_file(self, file_key, output_path):
        """Retrieves a file from the DHT and saves it locally."""
        print(f"🔍 Retrieving file with key '{file_key}'...")
        result = await self.node.get(file_key)

        if result:
            with open(output_path, "wb") as f:
                f.write(result)
            print(f"✅ File retrieved and saved as '{output_path}'!")
        else:
            print("❌ Failed to retrieve the file.")
        return result

    async def stop(self):
        self.node.stop()


# To run standalone (optional)
if __name__ == "__main__":
    import sys
    port = int(sys.argv[1])
    bootstrap = (sys.argv[2], int(sys.argv[3])) if len(sys.argv) == 4 else None
    node = P2PNode(port, bootstrap)

    asyncio.run(node.start())
