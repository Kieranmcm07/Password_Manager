import pytest
from conftest import register_user, login_user, unlock_vault
from models import VaultEntry
from extensions import db as _db


def setup_authenticated_session(client):
    """Register, log in, and unlock the vault. Returns the client ready to use."""
    register_user(client)
    login_user(client)
    unlock_vault(client)
    return client


def test_unlock_with_correct_master_password(client, db):
    register_user(client)
    login_user(client)
    response = unlock_vault(client)
    assert b"Vault unlocked" in response.data


def test_unlock_with_wrong_master_password(client, db):
    register_user(client)
    login_user(client)
    response = client.post(
        "/unlock",
        data={
            "master_password": "completely wrong password",
        },
        follow_redirects=True,
    )
    assert b"Wrong master password" in response.data


def test_create_entry(client, db):
    setup_authenticated_session(client)
    response = client.post(
        "/entries/add",
        data={
            "site_name": "GitHub",
            "url": "https://github.com",
            "username": "myuser",
            "password": "mysecretpassword",
            "notes": "Work account",
            "category": "Work",
        },
        follow_redirects=True,
    )
    assert b"Entry saved" in response.data
    assert b"GitHub" in response.data


def test_created_entry_is_not_stored_in_plaintext(client, db, app):
    """Make sure sensitive data is encrypted in the database."""
    setup_authenticated_session(client)
    client.post(
        "/entries/add",
        data={
            "site_name": "SomeBank",
            "url": "https://somebank.com",
            "username": "myemail@example.com",
            "password": "plaintextpassword123",
            "notes": "",
            "category": "",
        },
        follow_redirects=True,
    )

    with app.app_context():
        entry = VaultEntry.query.filter_by(site_name="SomeBank").first()
        assert entry is not None

        # The raw database fields should not contain the plaintext password
        assert "plaintextpassword123" not in (entry.password_enc or "")
        assert "plaintextpassword123" not in (entry.username_enc or "")

        # The password_enc field should contain encrypted data (not empty)
        assert entry.password_enc is not None
        assert len(entry.password_enc) > 10


def test_view_entries_shows_site_names(client, db):
    setup_authenticated_session(client)
    client.post(
        "/entries/add",
        data={
            "site_name": "Netflix",
            "url": "",
            "username": "user@mail.com",
            "password": "mypassword",
            "notes": "",
            "category": "",
        },
        follow_redirects=True,
    )

    response = client.get("/entries")
    assert b"Netflix" in response.data


def test_edit_entry(client, db, app):
    setup_authenticated_session(client)
    client.post(
        "/entries/add",
        data={
            "site_name": "Twitter",
            "url": "",
            "username": "twitteruser",
            "password": "oldpassword",
            "notes": "",
            "category": "",
        },
        follow_redirects=True,
    )

    with app.app_context():
        entry = VaultEntry.query.filter_by(site_name="Twitter").first()
        entry_id = entry.id

    response = client.post(
        f"/entries/{entry_id}/edit",
        data={
            "site_name": "Twitter (X)",
            "url": "https://x.com",
            "username": "twitteruser",
            "password": "newpassword",
            "notes": "updated",
            "category": "Social",
        },
        follow_redirects=True,
    )
    assert b"Entry updated" in response.data
    assert b"Twitter (X)" in response.data


def test_delete_entry(client, db, app):
    setup_authenticated_session(client)
    client.post(
        "/entries/add",
        data={
            "site_name": "ToDelete",
            "url": "",
            "username": "user",
            "password": "password",
            "notes": "",
            "category": "",
        },
        follow_redirects=True,
    )

    with app.app_context():
        entry = VaultEntry.query.filter_by(site_name="ToDelete").first()
        entry_id = entry.id

    response = client.post(f"/entries/{entry_id}/delete", follow_redirects=True)
    assert b"Entry deleted" in response.data
    assert b"ToDelete" not in response.data


def test_entries_page_requires_vault_unlocked(client, db):
    register_user(client)
    login_user(client)
    # Logged in but vault not unlocked
    response = client.get("/entries", follow_redirects=True)
    assert b"Master Password" in response.data or b"Unlock" in response.data


def test_search_returns_matching_entries(client, db):
    setup_authenticated_session(client)
    client.post(
        "/entries/add",
        data={
            "site_name": "Amazon",
            "url": "https://amazon.com",
            "username": "shopper",
            "password": "pw1",
            "notes": "",
            "category": "Shopping",
        },
        follow_redirects=True,
    )
    client.post(
        "/entries/add",
        data={
            "site_name": "Google",
            "url": "https://google.com",
            "username": "gshopper",
            "password": "pw2",
            "notes": "",
            "category": "Work",
        },
        follow_redirects=True,
    )

    response = client.get("/entries?query=Amazon")
    assert b"Amazon" in response.data
    assert b"Google" not in response.data
