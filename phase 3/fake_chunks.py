import os

def generate_dummy_chunks(n=5, size=1024):
    dummy_chunks = []
    for _ in range(n):
        dummy_chunks.append(os.urandom(size))
    return dummy_chunks
