from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from extensions import db, limiter
from models import User
from forms import RegistrationForm, LoginForm
from services.crypto import generate_kdf_salt, derive_key, encrypt

auth_bp = Blueprint("auth", __name__)
ph = PasswordHasher()


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("vault.entries"))

    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("That email is already registered.", "error")
            return render_template("auth/register.html", form=form)

        if User.query.filter_by(username=form.username.data).first():
            flash("That username is already taken.", "error")
            return render_template("auth/register.html", form=form)

        # Hash the account login password with Argon2 — this is never reversible
        password_hash = ph.hash(form.password.data)

        # Generate a per-user salt, then derive the vault key from the master password.
        # We immediately encrypt a known string ("vault_ok") with that key and store
        # the ciphertext. Later, on unlock, we try to decrypt it — if it fails, the
        # master password is wrong. This way we never store the master password itself.
        kdf_salt = generate_kdf_salt()
        vault_key = derive_key(form.master_password.data, kdf_salt)
        master_verify = encrypt("vault_ok", vault_key)

        user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            password_hash=password_hash,
            kdf_salt=kdf_salt,
            master_verify=master_verify,
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("vault.entries"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()

        # Use the same error message for wrong email and wrong password.
        # Separate messages would let someone enumerate registered emails.
        if user is None:
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html", form=form)

        try:
            ph.verify(user.password_hash, form.password.data)
        except VerifyMismatchError:
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html", form=form)

        # argon2-cffi can tell if the stored hash uses older parameters.
        # If so, re-hash while we still have the plaintext password.
        if ph.check_needs_rehash(user.password_hash):
            user.password_hash = ph.hash(form.password.data)
            db.session.commit()

        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get("next")
        return redirect(next_page or url_for("vault.unlock"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    # Clear the vault key from the session first, then log out
    session.pop("vault_key", None)
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


# Handles registration and login. The key thing: account password and master password are handled completely separately. Logging in does not unlock the vault.
