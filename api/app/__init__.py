from flask import Flask, current_app, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
import pandas as pd
from config import Config
from app.utils import DatasetManager, read_current_dataset

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

def initialise_recommender(app: Flask) -> None:
    """
    Initialise the recommender system for the current application startup.
    If no dataset exists, the recommender is left unavailable.
    If a dataset exists but the collaborative model requires manual initialisation,
    the recommender is still created in a deferred state.
    """
    app.extensions["recommender"] = None
    app.extensions["recommender_status"] = {
        "is_ready": False,
        "needs_manual_initialisation": False,
        "status_message": "Recommender has not been initialised."
    }

    if not dataset_manager.dataset_exists():
        app.extensions["recommender_status"] = {
            "is_ready": False,
            "needs_manual_initialisation": False,
            "status_message": "No dataset is currently installed."
        }
        return

    movies = pd.read_csv(app.config["MOVIES_PATH"])
    ratings = pd.read_csv(app.config["RATINGS_PATH"])
    current_dataset_id = read_current_dataset(app.config["CURRENT_DATASET_PATH"])

    # Import here to prevent circular import with db
    from app.recommender import HybridRecommendationSystem

    recommender = HybridRecommendationSystem(
        movies=movies,
        ratings=ratings,
        collab_model_path=app.config["RECOMMENDER_MODEL_PATH"],
        collab_dataset_id=current_dataset_id,
        persist_collab_model=app.config["PERSIST_COLLAB_MODEL"],
        auto_train_if_missing=app.config["AUTO_TRAIN_IF_MISSING"],
        save_model_after_train=app.config["SAVE_MODEL_AFTER_TRAIN"],
        allow_uninitialised=True
    )

    app.extensions["recommender"] = recommender
    app.extensions["recommender_status"] = recommender.get_status()

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

    if app.config["START_RECOMMENDER_ON_APP_START"]:
        initialise_recommender(app)
    return app