import pytest
from app import create_app
from extensions import db as _db
from config import TestingConfig


@pytest.fixture(scope="session")
def app():
    """Create a test app with an in-memory database."""
    app = create_app(TestingConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """A test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    """
    Provides the database and rolls back changes after each test.
    Each test gets a clean slate without recreating the whole schema.
    """
    with app.app_context():
        yield _db
        _db.session.rollback()
        # Delete all data between tests
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


def register_user(client, username="testuser", email="test@example.com",
                  password="accountpass123", master_password="masterpass123"):
    """Helper to register a user through the web form."""
    return client.post("/register", data={
        "username": username,
        "email": email,
        "password": password,
        "confirm_password": password,
        "master_password": master_password,
        "confirm_master": master_password,
    }, follow_redirects=True)


def login_user(client, email="test@example.com", password="accountpass123"):
    """Helper to log in through the web form."""
    return client.post("/login", data={
        "email": email,
        "password": password,
    }, follow_redirects=True)


def unlock_vault(client, master_password="masterpass123"):
    """Helper to unlock the vault through the web form."""
    return client.post("/unlock", data={
        "master_password": master_password,
    }, follow_redirects=True)