import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship, WriteOnlyMapped
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import jwt
from app import db, login
from time import time
import pickle
import os
from dotenv import load_dotenv

load_dotenv(".flaskenv")
encryption_key = os.environ["DB_SECRET_KEY"]


class User(UserMixin, db.Model):
    """
    User model for the application, inherits UserMixin to work properly with Flask and it's required methods and attributes.\n
    Parameters:\n
        username (str):      desired username
        email (str):         desired email address
        password_hash (str): hashed password of the user (set using set_password)
    """
    id:            Mapped[int]                    = mapped_column(primary_key=True)
    username:      Mapped[str]                    = mapped_column(sa.String(64), unique=True, index=True, nullable=False)
    email:         Mapped[str]                    = mapped_column(sa.String(128), unique=True, index=True, nullable=False)
    password_hash: Mapped[str]                    = mapped_column(sa.String(256), nullable=False)
    movie_ratings: WriteOnlyMapped["MovieRating"] = relationship(back_populates="rating_author")

    def __repr__(self):
        return f"<User\n\tid: {self.id}\n\tusername: {self.username}\n\temail: {self.email}\n>"

    def set_password(self, password) -> None:
        self.password_hash = generate_password_hash(password=password)

    def check_password(self, password) -> bool:
        return check_password_hash(pwhash=self.password_hash, password=password)
    
    def get_password_reset_token(self, expires_in=600) -> str:
        return jwt.encode(
            payload={
                "user_id": self.id,
                "exp": time() + expires_in
            },
            key=current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )
    
    def get_user_ratings(self):
        return db.session.scalars(sa.select(MovieRating).where(MovieRating.user_id == self.id)).all()

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {
                "user_id": self.id,
                "exp": time() + expires_in
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )
    
    @staticmethod
    def verify_reset_password_token(token):
        try:
            decoded = jwt.decode(
                jwt=token,
                key=current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
            id = decoded["user_id"]
        except Exception:
            return
        return db.session.get(User, id)
    
@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class Encrypted(sa.TypeDecorator):
    """
    Encrypted data type for SQLAlchemy, used for storing the actual storing of tmdb_ids and rating_ids however in application use the data is unencrypted.\n
    Parameter:\n
        encryption_key (str): The encryption key used to encrypt the data. Can be generated using generate_key.py
    """
    impl = sa.Text
    cache_ok = True

    def __init__(self, encryption_key: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.encryption_key = encryption_key
        self.fernet = Fernet(encryption_key.encode())

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = self.fernet.encrypt(pickle.dumps(value)).decode()
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = pickle.loads(self.fernet.decrypt(value.encode()))
        return value

class MovieRating(db.Model):
    """
    Movie rating model, stores the tmdb_id and rating of a movie for a user in encrypted form.\n
    Parameters:\n
        movie_id(str): the id of the movie to be rated - str as it will be encrypted.
        rating(str):   the rating of the movie - str as it will be encrypted as well.
        rating_author: User object of the user who the rating is associated with.
    """
    id:            Mapped[int]  = mapped_column(primary_key=True)
    user_id:       Mapped[int]  = mapped_column(sa.ForeignKey(User.id), index=True, nullable=False)
    movie_id:      Mapped[str]  = mapped_column(Encrypted(encryption_key), nullable=False)
    rating:        Mapped[str]  = mapped_column(Encrypted(encryption_key), nullable=False)
    rating_author: Mapped[User] = relationship(back_populates="movie_ratings")

    def __repr__(self):
        return f"<MovieRating\n\tid: {self.id}\n\tuser_id: {self.user_id}\n\ttmdb_id: {self.movie_id}\n\trating_author: {self.rating_author}\n>"