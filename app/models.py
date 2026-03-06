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
from datetime import datetime, timezone

load_dotenv(".flaskenv")
encryption_key = os.environ["DB_SECRET_KEY"]


class User(UserMixin, db.Model):
    """
    User model for the application, inherits UserMixin to work properly with Flask and it's required methods and attributes.
    Parameters:
        username (str):      desired username
        email (str):         desired email address
        password_hash (str): hashed password of the user (set using set_password)
    """
    id:                     Mapped[int]                             = mapped_column(primary_key=True)
    username:               Mapped[str]                             = mapped_column(sa.String(64), unique=True, index=True, nullable=False)
    email:                  Mapped[str]                             = mapped_column(sa.String(128), unique=True, index=True, nullable=False)
    password_hash:          Mapped[str]                             = mapped_column(sa.String(256), nullable=False)
    movie_ratings:          WriteOnlyMapped["MovieRating"]          = relationship(back_populates="rating_author")
    liked_movies:           WriteOnlyMapped["LikedMovie"]           = relationship(back_populates="rating_author")
    cached_recommendations: WriteOnlyMapped["CachedRecommendation"] = relationship(back_populates="user")

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
    
    def get_user_ratings(self) -> list[MovieRating]:
        return db.session.scalars(sa.select(MovieRating).where(MovieRating.rating_author == self)).all()

    def get_liked_movies(self) -> list[LikedMovie]:
        return db.session.scalars(sa.select(LikedMovie).where(LikedMovie.rating_author == self)).all()

    def get_reset_password_token(self, expires_in=600) -> str:
        return jwt.encode(
            {
                "user_id": self.id,
                "exp": time() + expires_in
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )
    
    def get_cached_recommendations(self) -> list[CachedRecommendation]:
        return db.session.scalars(sa.select(CachedRecommendation).where(CachedRecommendation.user == self)).all()
    
    def cache_recommendations(self, recommendations: list[dict[str, float]]) -> None:
        """
        Cache the given list of recommendations for the current user. Removes all old recommendations for the user before adding the new ones.
        Parameters:
           recommendations (list[dict[str, float]]): A list of dictionaries containing the movie ID and score for each recommendation.
        """
        recommendation_objects = []

        db.session.query(CachedRecommendation).where(CachedRecommendation.user == self).delete()

        for recommendation in recommendations:
            recommendation_object = CachedRecommendation(
                movie_id=recommendation["movieId"],
                score=recommendation["score"],
                user=self
            )
            
            recommendation_objects.append(recommendation_object)

        db.session.add_all(recommendation_objects)
        db.session.commit()

    @staticmethod
    def verify_reset_password_token(token) -> User | None:
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
    Encrypted data type for SQLAlchemy, used for storing the actual storing of tmdb_ids and rating_ids however in application use the data is unencrypted.
    Parameter:
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
    Movie rating model, stores the movieId and rating of a movie for a user in encrypted form.
    Parameters:
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
        return f"<MovieRating\n\tid: {self.id}\n\tuser_id: {self.user_id}\n\nmovie_id: {self.movie_id}\n\trating_author: {self.rating_author}\n>"
    
class LikedMovie(db.Model):
    """
    Liked movies model, stored the movieId of a movie for a user in encrypted form.
    Parameters:
        movie_id(str): the id of the movie to be rated - str as it will be encrypted.
        rating_author: User object of the user who the rating is associated with.
    """
    id:            Mapped[int]  = mapped_column(primary_key=True)
    user_id:       Mapped[int]  = mapped_column(sa.ForeignKey(User.id), index=True, nullable=False)
    movie_id:      Mapped[str]  = mapped_column(Encrypted(encryption_key), nullable=False)
    rating_author: Mapped[User] = relationship(back_populates="liked_movies")

    def __repr__(self):
        return f"<MovieRating\n\tid: {self.id}\n\tuser_id: {self.user_id}\n\nmovie_id: {self.movie_id}\n>"
    
class CachedRecommendation(db.Model):
    """
    Model to securely store cached recommendations with timestamps, prevents having to constantly create new recommendations.
    Parameters:
        movie_id (str): id of the movie to be cached.
        score (float):  hybrid recommendation score.
        user (User):    the user who is associated with the recommendation.
    """
    id:        Mapped[int]      = mapped_column(primary_key=True)
    user_id:   Mapped[int]      = mapped_column(sa.ForeignKey(User.id), index=True, nullable=False)
    movie_id:  Mapped[str]      = mapped_column(Encrypted(encryption_key), nullable=False)
    score:     Mapped[float]    = mapped_column(nullable=False)
    timestamp: Mapped[datetime] = mapped_column(sa.DateTime, default=datetime.now(timezone.utc))
    user:      Mapped[User]     = relationship(back_populates="cached_recommendations")

    def __repr__(self):
        return f"<CachedRecommendation\n\tid: {self.id}\n\tuser_id: {self.user_id}\n\tmovie_id: {self.movie_id}\n\tscore: {self.score}\n\ttimestamp: {self.timestamp}\n>"