from datetime import datetime
from flask_login import UserMixin
from extension import db

class User(UserMixin, db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)