import os
from datetime import timedelta

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".flaskenv"))

class Config():
    SECRET_KEY = os.environ.get("SECRET_KEY") or "b520d14f89f5469ab9d212a7b220c24839fd1864e7a0c29bf9b62dfe02fbd6bf"
    # Actually set a URI for deployment
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI") or "sqlite:///" + os.path.join(basedir, "data/db/app.db")
    DATASET_URLS = [
        {
            "identifier": "development",
            "client_name": "Development",
            "url":        "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
        },
        {
            "identifier": "standard",
            "client_name": "Standard",
            "url":        "https://files.grouplens.org/datasets/movielens/ml-32m.zip"
        }
    ]
    DATASETS_BASE = "data/datasets/"
    MOVIES_PATH = "data/datasets/movies.csv"
    RATINGS_PATH = "data/datasets/ratings.csv"
    LINKS_PATH = "data/datasets/links.csv"
    TAGS_PATH = "data/datasets/tags.csv"
    EXTRACTED_YEAR_PATH = "data/datasets/extracted_year.csv"
    CURRENT_DATASET_PATH = "data/datasets/current_dataset.txt"
    RECOMMENDER_MODEL_PATH = "data/models/collab_model.joblib"
    SEARCH_INDEX_PATH = "data/models/movie_search_index.joblib"
    SEARCH_INDEX_VERSION = 1
    START_MOVIE_SEARCH_ON_APP_START = True
    PERSIST_COLLAB_MODEL = True
    AUTO_TRAIN_IF_MISSING = False
    SAVE_MODEL_AFTER_TRAIN = True
    START_RECOMMENDER_ON_APP_START = True
    TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
    TMDB_API_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/original"
    LANGUAGES = ["en"]
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    ADMINS = ["your-email@example.com"]
    SOCKET_NAMESPACE = "/api/datasets-download-progress"
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_ACCESS_COOKIE_PATH = "/"
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_ACCESS_COOKIE_NAME = "access_token_cookie"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    USE_SOCKETIO = True
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True