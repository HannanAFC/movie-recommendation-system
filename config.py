import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".flaskenv"))

class Config():
    SECRET_KEY = os.environ.get("SECRET_KEY") or "b520d14f89f5469ab9d212a7b220c24839fd1864e7a0c29bf9b62dfe02fbd6bf"
    # Actually set a URI for deployment
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI") or "sqlite:///" + os.path.join(basedir, "app.db")
    LANGUAGES = ["en"]