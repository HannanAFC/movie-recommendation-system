import pandas as pd
from config import Config
from flask import Flask
from flask_cors import CORS

from app.extensions import db, jwt_manager, login, mail, migrate, socketio
from app.movie_search import MovieSearchService
from app.tmdb_service import TMDBService
from app.utils import DatasetManager, read_current_dataset

login.login_view = "auth.login"
login.login_message = "Login required to access this page."
dataset_manager = DatasetManager()
tmdb_service = TMDBService()
movie_search_service = MovieSearchService()

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

def initialise_movie_search(app: Flask) -> None:
    """
    Initialise the movie search service for the current application startup.
    If no dataset exists, the movie search service is left unavailable.
    """
    app.extensions["movie_search"] = None
    app.extensions["movie_search_status"] = {
        "is_ready": False,
        "status_message": "Movie search has not been initialised."
    }

    if not dataset_manager.dataset_exists():
        app.extensions["movie_search_status"] = {
            "is_ready": False,
            "status_message": "No dataset is currently installed."
        }
        return

    movies = pd.read_csv(app.config["MOVIES_PATH"])
    links = pd.read_csv(app.config["LINKS_PATH"])
    current_dataset_id = read_current_dataset(app.config["CURRENT_DATASET_PATH"])

    movie_search_service.initialise_from_storage(
        movies=movies,
        links=links,
        dataset_id=current_dataset_id
    )

    app.extensions["movie_search"] = movie_search_service
    app.extensions["movie_search_status"] = movie_search_service.get_status()

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

    CORS( app, origins=["http://localhost:5173"], supports_credentials=True )

    if ( app.config["USE_SOCKETIO"] == True ):
        socketio.init_app(
            app,
            cors_allowed_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
            cors_credentials=True,
            logger=True,
            engineio_logger=True
        )
    tmdb_service.init_app(app)
    app.extensions["tmdb_service"] = tmdb_service

    movie_search_service.init_app(app)
    if app.config["START_MOVIE_SEARCH_ON_APP_START"]:
        initialise_movie_search(app)


    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from app.main import bp as main_bp
    app.register_blueprint(main_bp, url_prefix="/api")

    from app.movies import bp as movies_bp
    app.register_blueprint(movies_bp, url_prefix="/api/movies")

    from app.recommendations import bp as recommendations_bp
    app.register_blueprint(recommendations_bp, url_prefix="/api/recommendations")

    from app.cli import bp as cli_bp
    app.register_blueprint(cli_bp)

    if app.config["START_RECOMMENDER_ON_APP_START"]:
        initialise_recommender(app)
    return app