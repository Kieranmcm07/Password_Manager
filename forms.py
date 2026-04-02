from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=80)],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
    )
    password = PasswordField(
        "Account Password",
        validators=[DataRequired(), Length(min=8, message="Use at least 8 characters.")],
    )
    confirm_password = PasswordField(
        "Confirm Account Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords do not match.")],
    )
    # The master password is separate from the account password.
    # It's used to derive the vault encryption key and is never stored.
    master_password = PasswordField(
        "Master Password",
        validators=[DataRequired(), Length(min=8, message="Use at least 8 characters.")],
    )
    confirm_master = PasswordField(
        "Confirm Master Password",
        validators=[DataRequired(), EqualTo("master_password", message="Passwords do not match.")],
    )


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()],
    )
    remember_me = BooleanField("Remember me")


class UnlockVaultForm(FlaskForm):
    master_password = PasswordField(
        "Master Password",
        validators=[DataRequired()],
    )


class VaultEntryForm(FlaskForm):
    site_name = StringField(
        "Site / App",
        validators=[DataRequired(), Length(max=200)],
    )
    url = StringField(
        "URL",
        validators=[Optional(), Length(max=500)],
    )
    username = StringField(
        "Username / Email",
        validators=[Optional(), Length(max=200)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()],
    )
    notes = TextAreaField(
        "Notes",
        validators=[Optional(), Length(max=2000)],
    )
    category = StringField(
        "Category",
        validators=[Optional(), Length(max=100)],
    )