# KeyVault — A Password Manager Learning Project

A full-stack password manager built with Flask, SQLAlchemy, and PyNaCl. I built this as a portfolio project to learn how password managers actually work under the hood — specifically how to handle encryption, key derivation, and keeping sensitive data out of the database.

> **⚠️ Warning:** This is a learning project. It's not audited, hasn't had a security review, and shouldn't be used to store passwords you actually care about without doing your own review first. That said, the cryptographic design is intentional and documented — it's not just `base64("password")`. This is also build with the help of Claude.ai, which guides me on how to use the libraries correctly as
im new to using libraries. Code is open source, so you can see exactly how everything works.

---

## What it does

- Register an account with a separate master password for vault encryption
- Log in and unlock your vault with the master password
- Store saved entries (site, URL, username, password, notes, category)
- All sensitive fields are encrypted with a key derived from your master password
- Search entries by site name, URL, or category
- Copy passwords to clipboard with one click
- Generate secure random passwords in the browser
- Add, edit, and delete vault entries

---

## Why Flask?

Flask is a good fit here because the project is small enough that a micro-framework makes sense, and it doesn't hide much — you can see exactly what's happening with requests, sessions, and the database. Django would have been fine too, but Flask means I'm not fighting conventions to understand the flow.

---

## How the encryption works

There are two separate passwords:

**Account password** — hashed with Argon2id via `argon2-cffi`. Never stored in a reversible form. Used only to log in.

**Master password** — never stored at all. When you unlock your vault, the master password is run through Argon2id as a KDF (key derivation function) with a per-user random salt to produce a 32-byte encryption key. That key is used with PyNaCl's `SecretBox` (XSalsa20-Poly1305) to encrypt each vault entry individually.
```
Master Password + Salt → Argon2id KDF → 32-byte key → SecretBox encrypt/decrypt
```

The derived key lives in the Flask session while the vault is unlocked. When you lock or log out, it's gone.

**What's stored in the database:**
- Username and password: Argon2 hash, KDF salt, encrypted verification blob
- Vault entries: encrypted ciphertext + nonce (bundled by PyNaCl), site name and URL in plaintext

**What's never stored:**
- Account passwords in plaintext
- Master passwords in any form
- Decrypted vault entry values

---

## Known limitations

**Session storage:** The vault key is stored in Flask's default signed cookie session. The cookie is signed (can't be tampered with) but the content is base64-visible to the client. A production version would use server-side sessions (Flask-Session with Redis) to keep the key off the client. For a local app this is acceptable, but worth knowing.

**Site name and URL are plaintext:** Encrypting them would break search without a client-side search implementation. The tradeoff is that the database reveals which sites you have saved, but not the credentials for them.

**No password strength meter:** Would be a reasonable addition.

**No two-factor auth:** Out of scope for this project.

**Rate limiting uses in-memory storage:** Fine for a single-process local app. In production with multiple workers you'd need Redis.

---

## Tech stack

| Thing | Library |
|---|---|
| Web framework | Flask |
| Database ORM | SQLAlchemy (SQLite for dev) |
| Login/sessions | Flask-Login |
| Forms + CSRF | Flask-WTF |
| Rate limiting | Flask-Limiter |
| Account password hashing | argon2-cffi |
| Vault encryption | PyNaCl (libsodium) |
| Config management | python-dotenv |

---

## Setup

**Requirements:** Python 3.10+
```bash
git clone <repo-url>
cd password-manager

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and set a real SECRET_KEY
```

Generate a proper secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Run the app:
```bash
python app.py
```

The database is created automatically on first run at `vault.db`.

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask session signing key. Must be long and random. |
| `DATABASE_URL` | No | SQLAlchemy connection string. Defaults to `sqlite:///vault.db`. |
| `FLASK_ENV` | No | `development` or `production`. Defaults to `development`. |

---

## Running tests
```bash
pytest tests/ -v
```

Tests use an in-memory SQLite database and have CSRF + rate limiting disabled. No setup needed beyond installing requirements.

---

## Project structure
```
password-manager/
├── app.py              # App factory and entry point
├── config.py           # Config classes
├── extensions.py       # SQLAlchemy, Flask-Login, Flask-Limiter instances
├── models.py           # Database models
├── forms.py            # WTForms form classes
├── routes/
│   ├── auth.py         # Register, login, logout
│   ├── vault.py        # Unlock, entries CRUD
│   └── misc.py         # Home redirect, password generator
├── services/
│   ├── crypto.py       # Key derivation, encrypt, decrypt
│   └── vault_service.py # Business logic for vault entries
├── templates/
│   ├── base.html
│   ├── auth/
│   └── vault/
├── static/
│   ├── css/style.css
│   └── js/vault.js
└── tests/
```

---

## Future improvements

- Server-side sessions to keep the vault key off the client cookie
- Password strength indicator on entry forms
- Import/export (CSV or a standard format like CSV from Bitwarden)
- Entry history / change log
- Browser extension for autofill
- Two-factor authentication
- Dark mode
- Configurable Argon2 parameters via environment variables

---

## Security notes

If you plan to use this for anything real, you should:

1. Run it behind HTTPS (Nginx + Let's Encrypt or similar)
2. Set `SESSION_COOKIE_SECURE = True` and `SESSION_COOKIE_HTTPONLY = True`
3. Switch Flask-Limiter to a Redis backend if running multiple processes
4. Consider adding `flask-talisman` for security headers (CSP, HSTS, etc.)
5. Switch to server-side sessions (Flask-Session)
6. Have someone else look at the code

The cryptographic primitives used (Argon2id, XSalsa20-Poly1305) are solid. The gaps are mostly around session handling and deployment configuration, not the encryption itself.