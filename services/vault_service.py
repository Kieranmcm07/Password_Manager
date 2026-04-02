from datetime import datetime

from sqlalchemy import or_
from nacl.exceptions import CryptoError  # noqa: F401

from extensions import db
from models import VaultEntry
from services.crypto import encrypt, decrypt, key_from_session_str


def get_all_entries(user_id: int, vault_key_str: str) -> list:
    """Fetch and decrypt all entries for a user, sorted by site name."""
    key = key_from_session_str(vault_key_str)
    entries = (
        VaultEntry.query
        .filter_by(user_id=user_id)
        .order_by(VaultEntry.site_name)
        .all()
    )
    return [_decrypt_entry(e, key) for e in entries]


def search_entries(user_id: int, vault_key_str: str, query: str) -> list:
    """
    Search by site name, URL, or category.
    These fields are stored in plaintext specifically so we can search them
    without having to decrypt every row.
    """
    key = key_from_session_str(vault_key_str)
    like = f"%{query}%"
    entries = (
        VaultEntry.query
        .filter(
            VaultEntry.user_id == user_id,
            or_(
                VaultEntry.site_name.ilike(like),
                VaultEntry.url.ilike(like),
                VaultEntry.category.ilike(like),
            ),
        )
        .order_by(VaultEntry.site_name)
        .all()
    )
    return [_decrypt_entry(e, key) for e in entries]


def get_entry(entry_id: int, user_id: int, vault_key_str: str):
    """
    Fetch and decrypt a single entry.
    Returns None if the entry doesn't exist or belongs to a different user.
    Always pass user_id so one user can never read another's entry.
    """
    key = key_from_session_str(vault_key_str)
    entry = VaultEntry.query.filter_by(id=entry_id, user_id=user_id).first()
    if entry is None:
        return None
    return _decrypt_entry(entry, key)


def create_entry(user_id: int, vault_key_str: str, form_data: dict) -> VaultEntry:
    """Encrypt the sensitive fields and write a new entry to the database."""
    key = key_from_session_str(vault_key_str)
    entry = VaultEntry(
        user_id=user_id,
        site_name=form_data["site_name"],
        url=form_data.get("url") or "",
        category=form_data.get("category") or "",
        username_enc=encrypt(form_data.get("username") or "", key),
        password_enc=encrypt(form_data["password"], key),
        notes_enc=encrypt(form_data.get("notes") or "", key),
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def update_entry(entry_id: int, user_id: int, vault_key_str: str, form_data: dict):
    """
    Update an existing entry with new encrypted values.
    Returns None if the entry isn't found or doesn't belong to this user.
    """
    key = key_from_session_str(vault_key_str)
    entry = VaultEntry.query.filter_by(id=entry_id, user_id=user_id).first()
    if entry is None:
        return None

    entry.site_name = form_data["site_name"]
    entry.url = form_data.get("url") or ""
    entry.category = form_data.get("category") or ""
    entry.username_enc = encrypt(form_data.get("username") or "", key)
    entry.password_enc = encrypt(form_data["password"], key)
    entry.notes_enc = encrypt(form_data.get("notes") or "", key)
    entry.updated_at = datetime.utcnow()

    db.session.commit()
    return entry


def delete_entry(entry_id: int, user_id: int) -> bool:
    """Delete an entry. Returns False if not found or if user_id doesn't match."""
    entry = VaultEntry.query.filter_by(id=entry_id, user_id=user_id).first()
    if entry is None:
        return False
    db.session.delete(entry)
    db.session.commit()
    return True


def _decrypt_entry(entry: VaultEntry, key: bytes) -> dict:
    """
    Small helper that decrypts an entry's fields and returns a plain dict.
    Keeping this separate means routes just get a dict back —
    they don't have to know anything about encryption.
    """
    return {
        "id": entry.id,
        "site_name": entry.site_name,
        "url": entry.url or "",
        "category": entry.category or "",
        "username": decrypt(entry.username_enc, key) if entry.username_enc else "",
        "password": decrypt(entry.password_enc, key),
        "notes": decrypt(entry.notes_enc, key) if entry.notes_enc else "",
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
    }