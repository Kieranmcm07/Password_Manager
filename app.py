import os
from flask import Flask
from dotenv import load_dotenv

from extensions import db, login_manager, limiter, csrf
from config import DevelopmentConfig, ProductionConfig, TestingConfig
from models import User

load_dotenv()


def create_app(config_class=None):
    app = Flask(__name__)

    if config_class is None:
        env = os.environ.get("FLASK_ENV", "development")
        if env == "production":
            config_class = ProductionConfig
        elif env == "testing":
            config_class = TestingConfig
        else:
            config_class = DevelopmentConfig

    app.config.from_object(config_class)

    # Hook up extensions to this app instance
    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."
    login_manager.login_message_category = "info"

    # Import and register blueprints inside the factory to avoid circular imports
    from routes.auth import auth_bp
    from routes.vault import vault_bp
    from routes.misc import misc_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(vault_bp)
    app.register_blueprint(misc_bp)

    with app.app_context():
        db.create_all()

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

# The app factory. Running python app.py starts the dev server. Tests import create_app with the test config.
