from flask import Flask

from app.config import Config
from app.routes.admin import admin_bp
from app.routes.auth import auth_bp
from app.routes.cliente import cliente_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.register_blueprint(auth_bp)
    app.register_blueprint(cliente_bp)
    app.register_blueprint(admin_bp)

    return app

