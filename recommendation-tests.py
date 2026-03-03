from app.recommender import CollaborativeRecommendationSystem, ContentRecommendationSystem, HybridRecommendationSystem
import unittest
from app import create_app, db
from config import Config
from app.models import User, MovieRating
from random import randrange
import sqlalchemy as sa
import pandas as pd

class TestConfig(Config):
    Testing = True
    # Redirect SQLAlchemy to special in-memory database for tests
    SQLALCHEMY_DATABASE_URI = "sqlite://"

class TestCollaborativeRecommendationSystem(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        user_count = 5
        rating_count = 5
        users = []

        self.movies = pd.read_csv("app/datasets/movies.csv")
        self.ratings = pd.read_csv("app/datasets/ratings.csv")

        for i in range(user_count):
            user = User(username=f"user{i}", email=f"user{i}@example.com")
            user.set_password(f"password{i}")
            users.append(user)
            db.session.add(user)
        
        for i in range(user_count):
            for j in range(rating_count):
                movie_rating = MovieRating(movie_id=randrange(1, 100), rating=randrange(1, 6), rating_author=users[i])
                db.session.add(movie_rating)

        db.session.commit()

        self.crs = CollaborativeRecommendationSystem(movies=self.movies, ratings=self.ratings)
        self.crs.initialise()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_valid_recommendations(self):
        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user, recs_per_rating=3)
            print("Number of recommendations:", len(recommendations))
        else:
            self.fail()

class TestContentRecommendationSystem(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        user_count = 5
        rating_count = 5
        users = []

        self.movies = pd.read_csv("app/datasets/movies.csv")
        self.ratings = pd.read_csv("app/datasets/ratings.csv")

        for i in range(user_count):
            user = User(username=f"user{i}", email=f"user{i}@example.com")
            user.set_password(f"password{i}")
            users.append(user)
            db.session.add(user)
        
        for i in range(user_count):
            for j in range(rating_count):
                movie_rating = MovieRating(movie_id=randrange(1, 100), rating=randrange(1, 6), rating_author=users[i])
                db.session.add(movie_rating)

        db.session.commit()

        self.crs = ContentRecommendationSystem(self.movies, self.ratings)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_valid_recommendations(self):
        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            print("Number of recommendations:", len(recommendations))
        else:
            self.fail()

class TestHybridRecommendationSystem(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        user_count = 5
        rating_count = 5
        users = []

        self.movies = pd.read_csv("app/datasets/movies.csv")
        self.ratings = pd.read_csv("app/datasets/ratings.csv")

        for i in range(user_count):
            user = User(username=f"user{i}", email=f"user{i}@example.com")
            user.set_password(f"password{i}")
            users.append(user)
            db.session.add(user)
        
        for i in range(user_count):
            for j in range(rating_count):
                movie_rating = MovieRating(movie_id=randrange(1, 100), rating=randrange(1, 6), rating_author=users[i])
                db.session.add(movie_rating)

        db.session.commit()

        self.crs = HybridRecommendationSystem(self.movies, self.ratings)

    def test_valid_recommendations(self):
        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            print("Number of recommendations:", len(recommendations))
        else:
            self.fail()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

if __name__ == "__main__":
    unittest.main()