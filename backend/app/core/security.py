import os
import re
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from fastapi import HTTPException

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    # Work factor is managed natively by passlib defaults (currently 12)
    return pwd_context.hash(password)

def validate_password_complexity(password: str):
    """Enforce: min 8 chars, 1 uppercase, 1 number, 1 special char."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one number.")
    if not re.search(r"[@$!%*?&._\-]", password):
        raise ValueError("Password must contain at least one special character.")

# Symmetric Encryption (Data at rest)
_encryption_key_env = os.getenv("ENCRYPTION_KEY")
if not _encryption_key_env:
    raise ValueError("ENCRYPTION_KEY must be set in the environment variables.")

fernet_cipher = Fernet(_encryption_key_env.encode())

def encrypt_data(data: str) -> str:
    if not data:
        return data
    return fernet_cipher.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    if not encrypted_data:
        return encrypted_data
    return fernet_cipher.decrypt(encrypted_data.encode()).decode()
