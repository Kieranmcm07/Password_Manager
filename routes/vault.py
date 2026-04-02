from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from flask_login import login_required, current_user
from nacl.exceptions import CryptoError

from extensions import limiter
from forms import UnlockVaultForm, VaultEntryForm
from services.crypto import derive_key, key_to_session_str, decrypt
from services import vault_service

vault_bp = Blueprint("vault", __name__)


def _vault_unlocked() -> bool:
    """Check whether the vault key is present in the session."""
    return "vault_key" in session


@vault_bp.route("/unlock", methods=["GET", "POST"])
@login_required
@limiter.limit("10 per minute")
def unlock():
    if _vault_unlocked():
        return redirect(url_for("vault.entries"))

    form = UnlockVaultForm()
    if form.validate_on_submit():
        try:
            key = derive_key(form.master_password.data, current_user.kdf_salt)

            # Try to decrypt the verification blob. If the master password is wrong,
            # PyNaCl will raise CryptoError here and we'll show an error.
            result = decrypt(current_user.master_verify, key)
            if result != "vault_ok":
                raise ValueError("Verification string mismatch")

        except (CryptoError, ValueError):
            flash("Wrong master password.", "error")
            return render_template("vault/unlock.html", form=form)

        # NOTE: The vault key is stored in the Flask session, which is a signed
        # cookie. The contents are visible to the client (just base64 JSON).
        # A production version would use server-side sessions to keep the key
        # off the client entirely. For a local learning project this is acceptable,
        # but don't use this for real sensitive data without addressing that.
        session["vault_key"] = key_to_session_str(key)
        flash("Vault unlocked.", "success")
        return redirect(url_for("vault.entries"))

    return render_template("vault/unlock.html", form=form)


@vault_bp.route("/lock")
@login_required
def lock():
    session.pop("vault_key", None)
    flash("Vault locked.", "info")
    return redirect(url_for("vault.unlock"))


@vault_bp.route("/")
@vault_bp.route("/entries")
@login_required
def entries():
    if not _vault_unlocked():
        return redirect(url_for("vault.unlock"))

    query = request.args.get("query", "").strip()

    try:
        if query:
            items = vault_service.search_entries(current_user.id, session["vault_key"], query)
        else:
            items = vault_service.get_all_entries(current_user.id, session["vault_key"])
    except CryptoError:
        flash("Decryption failed. Try locking and unlocking the vault.", "error")
        items = []

    return render_template("vault/entries.html", entries=items, query=query)


@vault_bp.route("/entries/add", methods=["GET", "POST"])
@login_required
def add_entry():
    if not _vault_unlocked():
        return redirect(url_for("vault.unlock"))

    form = VaultEntryForm()
    if form.validate_on_submit():
        vault_service.create_entry(
            user_id=current_user.id,
            vault_key_str=session["vault_key"],
            form_data={
                "site_name": form.site_name.data,
                "url": form.url.data,
                "username": form.username.data,
                "password": form.password.data,
                "notes": form.notes.data,
                "category": form.category.data,
            },
        )
        flash("Entry saved.", "success")
        return redirect(url_for("vault.entries"))

    return render_template("vault/add_entry.html", form=form)


@vault_bp.route("/entries/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    if not _vault_unlocked():
        return redirect(url_for("vault.unlock"))

    entry = vault_service.get_entry(entry_id, current_user.id, session["vault_key"])
    if entry is None:
        flash("Entry not found.", "error")
        return redirect(url_for("vault.entries"))

    form = VaultEntryForm()

    if form.validate_on_submit():
        vault_service.update_entry(
            entry_id=entry_id,
            user_id=current_user.id,
            vault_key_str=session["vault_key"],
            form_data={
                "site_name": form.site_name.data,
                "url": form.url.data,
                "username": form.username.data,
                "password": form.password.data,
                "notes": form.notes.data,
                "category": form.category.data,
            },
        )
        flash("Entry updated.", "success")
        return redirect(url_for("vault.entries"))

    # Pre-fill the form on GET with the decrypted values
    if request.method == "GET":
        form.site_name.data = entry["site_name"]
        form.url.data = entry["url"]
        form.username.data = entry["username"]
        form.password.data = entry["password"]
        form.notes.data = entry["notes"]
        form.category.data = entry["category"]

    return render_template("vault/edit_entry.html", form=form, entry=entry)


@vault_bp.route("/entries/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_entry(entry_id):
    if not _vault_unlocked():
        return redirect(url_for("vault.unlock"))

    deleted = vault_service.delete_entry(entry_id, current_user.id)
    if deleted:
        flash("Entry deleted.", "success")
    else:
        flash("Entry not found.", "error")

    return redirect(url_for("vault.entries"))

# All the vault routes. Every route checks _vault_unlocked() before doing anything, and every database call passes user_id to prevent one user from touching another's entries.