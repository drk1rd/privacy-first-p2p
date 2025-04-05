from cryptography.fernet import Fernet

def generate_key() -> bytes:
    """
    Generate a secure symmetric encryption key (Fernet uses AES in CBC mode with HMAC).
    You can store this key per session or per file.
    """
    return Fernet.generate_key()

def get_cipher(key: bytes) -> Fernet:
    """
    Create a Fernet cipher object using the given key.
    """
    return Fernet(key)

def encrypt_chunk(cipher: Fernet, data: bytes) -> bytes:
    """
    Encrypt a chunk of bytes using the provided Fernet cipher.
    
    Args:
        cipher: Fernet object initialized with a secret key.
        data: Plaintext bytes to encrypt.
    
    Returns:
        Encrypted bytes (token).
    """
    return cipher.encrypt(data)

def decrypt_chunk(cipher: Fernet, token: bytes) -> bytes:
    """
    Decrypt an encrypted chunk using the provided Fernet cipher.
    
    Args:
        cipher: Fernet object initialized with the same key used to encrypt.
        token: Encrypted bytes to decrypt.
    
    Returns:
        Decrypted original plaintext bytes.
    """
    return cipher.decrypt(token)
