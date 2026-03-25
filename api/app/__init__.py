from flask import Flask, current_app, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from app.utils import DatasetManager
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = "auth.login"
login.login_message = "Login required to access this page."
mail = Mail()
dataset_manager = DatasetManager()
cors = CORS()
jwt_manager = JWTManager()
socketio = SocketIO(async_mode="eventlet")

def create_app(config_class=Config):
    # Initialise flask and get the settings from the config class
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Use the .init_app function of the flask extensions to bind them to the the flask context
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    dataset_manager.init_app(app)
    cors.init_app(app, resources={r"/*":{"origins":"*"}})
    jwt_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="http://127.0.0.1:5174")

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from app.main import bp as main_bp
    app.register_blueprint(main_bp, url_prefix="/api")

    from app.cli import bp as cli_bp
    app.register_blueprint(cli_bp)

    return app