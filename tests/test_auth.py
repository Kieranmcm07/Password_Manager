import pytest
from conftest import register_user, login_user


def test_register_new_user(client, db):
    response = register_user(client)
    assert b"Account created" in response.data


def test_register_duplicate_email(client, db):
    register_user(client)
    response = register_user(client)
    assert b"already registered" in response.data


def test_register_duplicate_username(client, db):
    register_user(client)
    # Different email, same username
    response = register_user(client, email="other@example.com")
    assert b"already taken" in response.data


def test_register_password_mismatch(client, db):
    response = client.post("/register", data={
        "username": "user1",
        "email": "user1@example.com",
        "password": "goodpassword1",
        "confirm_password": "differentpassword",
        "master_password": "masterpass123",
        "confirm_master": "masterpass123",
    }, follow_redirects=True)
    # Should stay on the register page with an error
    assert b"do not match" in response.data


def test_login_correct_credentials(client, db):
    register_user(client)
    response = login_user(client)
    # After login, redirected to unlock page
    assert b"Unlock" in response.data or b"Master Password" in response.data


def test_login_wrong_password(client, db):
    register_user(client)
    response = client.post("/login", data={
        "email": "test@example.com",
        "password": "wrongpassword",
    }, follow_redirects=True)
    assert b"Invalid email or password" in response.data


def test_login_wrong_email(client, db):
    register_user(client)
    response = client.post("/login", data={
        "email": "nobody@example.com",
        "password": "accountpass123",
    }, follow_redirects=True)
    assert b"Invalid email or password" in response.data


def test_logout(client, db):
    register_user(client)
    login_user(client)
    response = client.get("/logout", follow_redirects=True)
    assert b"logged out" in response.data.lower()


def test_vault_requires_login(client, db):
    response = client.get("/entries", follow_redirects=True)
    assert b"log in" in response.data.lower()