from datetime import datetime
from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    # Argon2 hash of the account loging password but not reversible
    password_hash = db.Column(db.String(255), nullable=False)

    # Per user random salt used to derive the vault encryption key.
    kdf_salt = db.Column(db.String(64), nullable=False)

    # A small encrpted blob ("vault_ok") that we decrypt on unlock
    # to confirm the master password is correct without storing the password itself
    master_verify = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    entries = db.relationship(
        "VaultEntry", backref="owner", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.username}>"


class VaultEntry(db.Model):
    __tablename__ = "vault_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # These three are stored in plaintext so we can search without decrypting everything.
    # This leaks which sites you have saved, but not the credentials. Worth noting in README.
    site_name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(100), nullable=True)

    # Sensitive fields: encrypted with the vault key before storage
    username_enc = db.Column(db.Text, nullable=True)
    password_enc = db.Column(db.Text, nullable=False)
    notes_enc = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<VaultEntry {self.site_name}>"


# Two tables. The master_verify field is the mechanism that lets u check the master password
# without storing it, we try to descrypt it, and if fail then password was wrong.
