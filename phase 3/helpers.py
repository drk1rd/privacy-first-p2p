import hashlib
import uuid

def obfuscate_filename(filename: str) -> str:
    return hashlib.sha256(filename.encode()).hexdigest() + ".bin"

def generate_obfuscated_id() -> str:
    return str(uuid.uuid4())
