import asyncio
from kademlia.network import Server

class P2PNode:
    def __init__(self, port, bootstrap_node=None):
        self.port = port
        self.bootstrap_node = bootstrap_node
        self.node = Server()

    async def start(self):
        """Start the node and connect to the bootstrap node if provided."""
        await self.node.listen(self.port)

        if self.bootstrap_node:
            try:
                print(f"🔗 Connecting to bootstrap node {self.bootstrap_node}")
                await self.node.bootstrap([self.bootstrap_node])
            except Exception as e:
                print(f"⚠️ Failed to bootstrap: {e}")

        print(f"✅ Node running on port {self.port}")

    async def store_chunks(self, file_path, chunk_size=1024):
        """Reads a file, splits it into chunks, and stores each chunk in the DHT."""
        try:
            with open(file_path, "rb") as f:
                chunks = [f.read(chunk_size) for _ in iter(lambda: f.read(chunk_size), b"")]

            for i, chunk in enumerate(chunks):
                chunk_key = f"chunk:{file_path.split('/')[-1]}:{i}"
                print(f"📤 Storing chunk {i} under key '{chunk_key}'...")
                await self.node.set(chunk_key, chunk)

            print("✅ File split into chunks and stored successfully!")
            return len(chunks)

        except Exception as e:
            print(f"❌ Failed to store file: {e}")
            return None

    async def retrieve_chunks(self, file_name, total_chunks, output_path):
        """Retrieves all chunks of a file from the DHT and reassembles it."""
        print(f"🔍 Retrieving file '{file_name}' in {total_chunks} chunks...")
        chunks = []

        for i in range(total_chunks):
            chunk_key = f"chunk:{file_name}:{i}"
            print(f"⚡ Retrieving chunk {i}...")
            chunk = await self.node.get(chunk_key)

            if chunk:
                print(f"✅ Chunk {i} retrieved!")
                chunks.append(chunk)
            else:
                print(f"❌ Failed to retrieve chunk {i}!")
                return False

        with open(output_path, "wb") as f:
            for chunk in chunks:
                f.write(chunk)

        print(f"✅ File reassembled and saved as '{output_path}'!")
        return True

    async def stop(self):
        """Stops the node."""
        self.node.stop()


# To run standalone
if __name__ == "__main__":
    import sys
    port = int(sys.argv[1])
    bootstrap = (sys.argv[2], int(sys.argv[3])) if len(sys.argv) == 4 else None
    node = P2PNode(port, bootstrap)

    asyncio.run(node.start())