import os
from dotenv import load_dotenv
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".flaskenv"))

class Config():
    SECRET_KEY = os.environ.get("SECRET_KEY") or "b520d14f89f5469ab9d212a7b220c24839fd1864e7a0c29bf9b62dfe02fbd6bf"
    # Actually set a URI for deployment
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI") or "sqlite:///" + os.path.join(basedir, "app.db")
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
    DATASETS_BASE = "api/app/datasets/"
    MOVIES_PATH = "api/app/datasets/movies.csv"
    RATINGS_PATH = "api/app/datasets/ratings.csv"
    LINKS_PATH = "api/app/datasets/links.csv"
    TAGS_PATH = "api/app/datasets/tags.csv"
    EXTRACTED_YEAR_PATH = "api/app/datasets/extracted_year.csv"
    CURRENT_DATASET_PATH = "api/app/datasets/current_dataset.txt"
    RECOMMENDER_MODEL_PATH = "api/models/collab_model.joblib"
    PERSIST_COLLAB_MODEL = True
    AUTO_TRAIN_IF_MISSING = False
    SAVE_MODEL_AFTER_TRAIN = True
    START_RECOMMENDER_ON_APP_START = True
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