from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

misc_bp = Blueprint("misc", __name__)


@misc_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("vault.entries"))
    return redirect(url_for("auth.login"))


@misc_bp.route("/generator")
@login_required
def generator():
    # The actual generation happens client-side in JavaScript.
    # No sensitive data goes to the server for this one.
    return render_template("misc/generator.html")


# Just two routes. Home redirects based on auth state, generator renders the password generator page.
