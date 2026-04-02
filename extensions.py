from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

# So these are created here and executed later in create_app()

# This will avoid stupid circular imports between app.py, models.py and the routes.

db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()

# So this overall will hold the extension objects so they can be imported by both.py and route files :)
# Without circular imports. A standard flask pattern.