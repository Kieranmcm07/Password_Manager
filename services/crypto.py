import base64
import nacl.pwhash
import nacl.secret
import nacl.utils
# noqa: F401 - re-exported for convenience
from nacl.exceptions import CryptoError


# Argon2id "interactive" settings — good balance of security and speed for a local app.
# These are intentionally slow; that's what makes the derived key hard to brute-force.
# For a higher-traffic production app you'd tune these up.
OPS_LIMIT = nacl.pwhash.argon2id.OPSLIMIT_INTERACTIVE
MEM_LIMIT = nacl.pwhash.argon2id.MEMLIMIT_INTERACTIVE
# 32 bytes
KEY_SIZE = nacl.secret.SecretBox.KEY_SIZE

def generate_kdf_salt() -> str:
    """
    Generate a random salt for key derivation.
    Call this once per user at registration time and store it in the database.
    The salt is not secret, it just ensures that two users with the same
    master password end up with different vault keys.
    """
    raw = nacl.utils.random(nacl.pwhash.argon2id.SALTBYTES)
    return base64.b64encode(raw).decode("utf-8")


def derive_key(master_password: str, salt_b64: str) -> bytes:
    """
    Derive a 32-byte encryption key from the master password + the user's salt.
    This is the slow step, Argon2id is designed to be expensive to run, which
    makes offline brute-force attacks much harder if the database is ever leaked.
    """
    salt = base64.b64decode(salt_b64)
    key = nacl.pwhash.argon2id.kdf(
        KEY_SIZE,
        master_password.encode("utf-8"),
        salt,
        opslimit=OPS_LIMIT,
        memlimit=MEM_LIMIT,
    )
    return key


def encrypt(plaintext: str, key: bytes) -> str:
    """
    Encrypt a string using XSalsa20-Poly1305 via PyNaCl's SecretBox.
    A random nonce is generated automatically and prepended to the ciphertext.
    Returns a base64-encoded string safe to store in the database.
    """
    box = nacl.secret.SecretBox(key)
    encrypted = box.encrypt(plaintext.encode("utf-8"))
    return base64.b64encode(bytes(encrypted)).decode("utf-8")


def decrypt(ciphertext_b64: str, key: bytes) -> str:
    """
    Decrypt a base64-encoded ciphertext.
    Raises nacl.exceptions.CryptoError if the key is wrong or the data is tampered.
    The authentication check is built into SecretBox — we get that for free.
    """
    box = nacl.secret.SecretBox(key)
    raw = base64.b64decode(ciphertext_b64)
    plaintext_bytes = box.decrypt(raw)
    return plaintext_bytes.decode("utf-8")

def key_to_session_str(key: bytes) -> str:
    """Encode the key as a base64 string for storing in the Flask session."""
    return base64.b64encode(key).decode("utf-8")


def key_from_session_str(key_str: str) -> bytes:
    """Decode the base64 string back to raw key bytes."""
    return base64.b64decode(key_str)

# The whole crypto layer in one file. PyNaCl's SecretBox handles nonce generation, encryption, and authentication in one call.
# There's not much we can get wrong. The tricky part is key derivation, and Argon2id handles that.