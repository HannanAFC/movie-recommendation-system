import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship, WriteOnlyMapped
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import jwt
from app import db, jwt_manager
from time import time
import pickle
from datetime import datetime, timezone
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import base64
import secrets

def get_encryption_key() -> bytes | None:
    """Gets the encryption key from the flask session."""
    from flask import g
    return getattr(g, "dek", None)

class Encrypted(sa.TypeDecorator):
    """
    Encrypted data type for SQLAlchemy, used for storing the actual storing of tmdb_ids and rating_ids however in application use the data is unencrypted.
    """
    impl = sa.Text
    cache_ok = True

    def _get_fernet(self):
        key = get_encryption_key()
        if not key:
            raise RuntimeError("User encryption key not loaded")
        return Fernet(key)

    def process_bind_param(self, value, dialect):

        if value is None:
            return None

        f = self._get_fernet()
        return f.encrypt(pickle.dumps(value)).decode()

    def process_result_value(self, value, dialect):

        if value is None:
            return None

        f = self._get_fernet()
        return pickle.loads(f.decrypt(value.encode()))

class User(UserMixin, db.Model):
    """
    User model for the application, inherits UserMixin to work properly with Flask and it's required methods and attributes.
    Parameters:
        username (str):      desired username
        email (str):         desired email address
        password_hash (str): hashed password of the user (set using set_password)
    """
    id:                     Mapped[int]                              = mapped_column(primary_key=True)
    username:               Mapped[str]                              = mapped_column(sa.String(64), unique=True, index=True, nullable=False)
    email:                  Mapped[str]                              = mapped_column(sa.String(128), unique=True, index=True, nullable=False)
    tmdb_api_key:           Mapped[str]                              = mapped_column(Encrypted(), nullable=True)
    password_hash:          Mapped[str]                              = mapped_column(sa.String(256), nullable=False)
    encrypted_dek:          Mapped[str]                              = mapped_column(sa.LargeBinary, nullable=False)
    dek_salt:               Mapped[str]                              = mapped_column(sa.LargeBinary, nullable=False)
    movie_ratings:          WriteOnlyMapped["MovieRating"]           = relationship(back_populates="rating_author")
    liked_movies:           WriteOnlyMapped["LikedMovie"]            = relationship(back_populates="rating_author")
    recommendation_sets:    WriteOnlyMapped["RecommendationSet"]     = relationship(back_populates="user")

    def __repr__(self):
        return f"<User\n\tid: {self.id}\n\tusername: {self.username}\n\temail: {self.email}\n>"

    def set_password(self, password) -> None:
        self.password_hash = generate_password_hash(password=password)

        if not self.encrypted_dek:
            dek = Fernet.generate_key()

            salt = secrets.token_bytes(16)

            kek = self.derive_kek(password, salt)

            f = Fernet(kek)

            self.encrypted_dek = f.encrypt(dek)
            self.dek_salt = salt

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
    
    def change_password(self, old_password, new_password) -> None:

        old_kek = self.derive_kek(old_password, self.dek_salt)
        dek = Fernet(old_kek).decrypt(self.encrypted_dek)

        new_salt = secrets.token_bytes(16)
        new_kek = self.derive_kek(new_password, new_salt)

        self.encrypted_dek = Fernet(new_kek).encrypt(dek)
        self.dek_salt = new_salt

        self.password_hash = generate_password_hash(new_password)
    
    def derive_kek(self, password: str, salt: bytes) -> bytes:
        """
        Create KEK to encrypt DEK, using password and salt, creation is repeatable given the same password and salt.
        Parameters:
           password (str): Password to derive KEK from.
            salt (bytes):  Salt to use in the derivation process.
        """
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2**14,
            r=8,
            p=1
        )

        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def unlock_dek(self, password):
        """
        Unlock DEK using password and salt.
        Parameters:
            password (str): Password to unlock DEK with.
        """
        if not self.check_password(password):
            raise ValueError("Invalid password")
        kek = self.derive_kek(password, self.dek_salt)
        f = Fernet(kek)

        return f.decrypt(self.encrypted_dek)
    
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
    
    def get_cached_recommendation_sets(self, pagination: int = 10) -> list[RecommendationSet]:
        """
        Get the cached recommendation sets for the current user.
        Parameters:
            pagination (int): The maximum number of recommendation sets to return. Defaults to 10.
        """
        return db.session.scalars(sa.select(RecommendationSet).where(RecommendationSet.user == self).limit(pagination)).all()
    
    def cache_recommendation_set(self, recommendations: list[dict[str, float]]) -> None:
        """
        Cache the given list of recommendations for the current user. Maximum of 10 sets cand be stored, when this limit is reached the oldest will be removed.
        Parameters:
           recommendations (list[dict[str, float]]): A list of dictionaries containing the movie ID and score for each recommendation.
        """
        recommendation_objects = []

        recommendation_set = RecommendationSet(user=self)

        for recommendation in recommendations:
            recommendation_object = CachedRecommendation(
                movie_id=recommendation["movieId"],
                score=recommendation["score"],
                user_set=recommendation_set
            )
            
            recommendation_objects.append(recommendation_object)

        db.session.add(recommendation_set)
        db.session.add_all(recommendation_objects)
        db.session.commit()

        current_sets = db.session.scalars(sa.select(RecommendationSet).where(RecommendationSet.user == self).order_by(RecommendationSet.timestamp.desc()).limit(10)).all()
        if len(current_sets) > 10:
            db.session.delete(current_sets[0])
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
    
@jwt_manager.user_identity_loader
def user_identity_lookup(user):
    return user.username

@jwt_manager.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(username=identity).first()

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
    movie_id:      Mapped[str]  = mapped_column(Encrypted(), nullable=False)
    rating:        Mapped[str]  = mapped_column(Encrypted(), nullable=False)
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
    movie_id:      Mapped[str]  = mapped_column(Encrypted(), nullable=False)
    rating_author: Mapped[User] = relationship(back_populates="liked_movies")

    def __repr__(self):
        return f"<MovieRating\n\tid: {self.id}\n\tuser_id: {self.user_id}\n\nmovie_id: {self.movie_id}\n>"
    
class RecommendationSet(db.Model):
    """
    Model to store a set of recommendations for a user, all generated at once.
    Parameters:
        user (User):          the user associated with the recommendation set.
        timestamp (datetime): when the set was generated.
    """
    id:                      Mapped[int]                             = mapped_column(primary_key=True)
    user_id:                 Mapped[int]                             = mapped_column(sa.ForeignKey(User.id), index=True, nullable=False)
    timestamp:               Mapped[datetime]                        = mapped_column(sa.DateTime, default=datetime.now(timezone.utc))
    user:                    Mapped[User]                            = relationship(back_populates="recommendation_sets")
    cached_recommendations:  WriteOnlyMapped["CachedRecommendation"] = relationship(back_populates="user_set")

    def __repr__(self):
        return f"<RecommendationSet\n\tid: {self.id}\n\tuser_id: {self.user_id}\n\ttimestamp: {self.timestamp}\n>"

class CachedRecommendation(db.Model):
    """
    Model to store individual recommendations within a set.
    Parameters:
        movie_id (str):               id of the movie.
        score (float):                hybrid recommendation score.
        user_set (RecommendationSet): the set these recommendations belong to.
    """
    id:          Mapped[int]               = mapped_column(primary_key=True)
    user_set_id: Mapped[int]               = mapped_column(sa.ForeignKey(RecommendationSet.id), index=True, nullable=False)
    movie_id:    Mapped[str]               = mapped_column(Encrypted(), nullable=False)
    score:       Mapped[float]             = mapped_column(nullable=False)
    user_set:    Mapped[RecommendationSet] = relationship(back_populates="cached_recommendations")

    def __repr__(self):
        return f"<CachedRecommendation\n\tid: {self.id}\n\tuser_set_id: {self.user_set_id}\n\tmovie_id: {self.movie_id}\n\tscore: {self.score}\n>"