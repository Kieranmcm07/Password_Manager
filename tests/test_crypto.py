import pytest
from nacl.exceptions import CryptoError
from services.crypto import (
    generate_kdf_salt,
    derive_key,
    encrypt,
    decrypt,
    key_to_session_str,
    key_from_session_str,
)


def test_generate_kdf_salt_is_unique():
    salt1 = generate_kdf_salt()
    salt2 = generate_kdf_salt()
    assert salt1 != salt2


def test_generate_kdf_salt_is_string():
    salt = generate_kdf_salt()
    assert isinstance(salt, str)
    assert len(salt) > 0


def test_derive_key_returns_bytes():
    salt = generate_kdf_salt()
    key = derive_key("my master password", salt)
    assert isinstance(key, bytes)
    assert len(key) == 32


def test_derive_key_is_deterministic():
    # Same password + salt should always produce the same key
    salt = generate_kdf_salt()
    key1 = derive_key("same password", salt)
    key2 = derive_key("same password", salt)
    assert key1 == key2


def test_derive_key_different_passwords():
    salt = generate_kdf_salt()
    key1 = derive_key("password one", salt)
    key2 = derive_key("password two", salt)
    assert key1 != key2


def test_derive_key_different_salts():
    key1 = derive_key("same password", generate_kdf_salt())
    key2 = derive_key("same password", generate_kdf_salt())
    assert key1 != key2


def test_encrypt_decrypt_roundtrip():
    salt = generate_kdf_salt()
    key = derive_key("master password", salt)
    plaintext = "super secret value"
    ciphertext = encrypt(plaintext, key)
    recovered = decrypt(ciphertext, key)
    assert recovered == plaintext


def test_encrypt_produces_different_ciphertext_each_time():
    # Each encryption should use a different random nonce
    salt = generate_kdf_salt()
    key = derive_key("master password", salt)
    ct1 = encrypt("same text", key)
    ct2 = encrypt("same text", key)
    assert ct1 != ct2


def test_decrypt_with_wrong_key_raises():
    salt = generate_kdf_salt()
    key = derive_key("correct password", salt)
    ciphertext = encrypt("secret", key)

    wrong_key = derive_key("wrong password", salt)
    with pytest.raises(CryptoError):
        decrypt(ciphertext, wrong_key)


def test_decrypt_tampered_ciphertext_raises():
    salt = generate_kdf_salt()
    key = derive_key("master password", salt)
    ciphertext = encrypt("secret value", key)

    # Flip a character to simulate tampering
    tampered = ciphertext[:-2] + "XX"
    with pytest.raises(Exception):
        decrypt(tampered, key)


def test_key_session_roundtrip():
    salt = generate_kdf_salt()
    key = derive_key("a password", salt)
    session_str = key_to_session_str(key)
    recovered = key_from_session_str(session_str)
    assert key == recovered


def test_encrypt_handles_special_characters():
    salt = generate_kdf_salt()
    key = derive_key("master password", salt)
    tricky = 'p@$$w0rd! "quotes" & <tags> 你好'
    assert decrypt(encrypt(tricky, key), key) == tricky
