from flask import Flask, current_app, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from config import Config
from app.utils import DatasetManager

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = "auth.login"
login.login_message = "Login required to access this page."
mail = Mail()
dataset_manager = DatasetManager()
jwt_manager = JWTManager()
socketio = SocketIO()

SOCKET_NAMESPACE = "/api/datasets-download-progress"

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
    jwt_manager.init_app(app)
    if ( app.config["USE_SOCKETIO"] == True ):
        socketio.init_app(
            app,
            cors_allowed_origins=["http://localhost:5001", "http://127.0.0.1:5001"],
            cors_credentials=True,
            logger=True,
            engineio_logger=True
        )

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from app.main import bp as main_bp
    app.register_blueprint(main_bp, url_prefix="/api")

    from app.cli import bp as cli_bp
    app.register_blueprint(cli_bp)

    return app