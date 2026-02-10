# app/encryption.py
"""
AES-256 Fernet encryption for sensitive tokens stored in the database.
Tokens are encrypted before storage and decrypted on retrieval.
"""
import os
import base64
import hashlib
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()


def _get_encryption_key() -> bytes:
    """
    Derive a Fernet-compatible key from the ENCRYPTION_KEY env var.
    Falls back to SUPABASE_SERVICE_KEY + a salt if ENCRYPTION_KEY is not set.
    The key is derived via SHA-256 so any-length secret works.
    """
    raw_key = os.getenv("ENCRYPTION_KEY")
    if not raw_key:
        # Deterministic fallback so existing stored tokens can still be decrypted
        fallback = os.getenv("SUPABASE_SERVICE_KEY", "default-insecure-key")
        raw_key = f"llm-deploy-enc-{fallback}"
    # SHA-256 → 32 bytes → base64-url-safe = valid Fernet key
    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_get_encryption_key())
    return _fernet


def encrypt_token(plaintext: str) -> str:
    """Encrypt a token string and return a base64-encoded ciphertext."""
    if not plaintext:
        return plaintext
    cipher = _get_fernet()
    encrypted = cipher.encrypt(plaintext.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a previously encrypted token. Returns plaintext."""
    if not ciphertext:
        return ciphertext
    try:
        cipher = _get_fernet()
        decrypted = cipher.decrypt(ciphertext.encode("utf-8"))
        return decrypted.decode("utf-8")
    except Exception:
        # If decryption fails, the token was likely stored before encryption
        # was enabled — return as-is for backwards compatibility.
        return ciphertext


def is_encrypted(value: str) -> bool:
    """Quick heuristic: Fernet tokens start with 'gAAAAA'."""
    return value.startswith("gAAAAA") if value else False
