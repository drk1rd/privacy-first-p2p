import time, random
from random import shuffle

# Shuffle the order of chunks
all_chunks = real_chunks + dummy_chunks
shuffle(all_chunks)

for chunk in all_chunks:
    dht.store(chunk)
    time.sleep(random.uniform(0.1, 0.7))  # Random delay
    