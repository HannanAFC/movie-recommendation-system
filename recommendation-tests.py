from app.recommender import CollaborativeRecommendationSystem, ContentRecommendationSystem, HybridRecommendationSystem
import unittest
from app import create_app, db
from config import Config
from app.models import User, MovieRating, LikedMovie
from random import randrange
import sqlalchemy as sa
import pandas as pd

class TestConfig(Config):
    Testing = True
    # Redirect SQLAlchemy to special in-memory database for tests
    SQLALCHEMY_DATABASE_URI = "sqlite://"

class TestCollaborativeRecommendationSystem(unittest.TestCase):
    
    """
    This test is technically flawed, the test assumes the movieIDs increment by 1 for each movie, however it turns
    out theres a couple gaps, for example look for movieId 51 in the movies.csv file - it isn't there. So if that
    number is randomly created for the test it won't be in the matrix so no recommendations are created.
    The recommendation system still works correctly though.
    """
    def setUp(self):

        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):

        db.session.close()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_has_ratings(self):

        rating_count = 20
        ratings = [1.1, 1.7, 3.5, 2.4, 3.8, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4]

        self.movies = pd.read_csv("app/datasets/movies.csv")
        self.ratings = pd.read_csv("app/datasets/ratings.csv")

        user = User(username=f"user", email=f"user@example.com")
        user.set_password(f"password")
        db.session.add(user)

        for i in range(rating_count):
            movie_rating = MovieRating(movie_id=randrange(1, 100), rating=ratings[i], rating_author=user)
            db.session.add(movie_rating)

        db.session.commit()

        self.crs = CollaborativeRecommendationSystem(movies=self.movies, ratings=self.ratings)
        self.crs.initialise()

        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            print("Number of recommendations:", len(recommendations))
        else:
            self.fail("User not found.")

    def test_has_no_ratings_has_likes(self):

        likes_count = 15
        self.movies = pd.read_csv("app/datasets/movies.csv")
        self.ratings = pd.read_csv("app/datasets/ratings.csv")

        user = User(username=f"user", email=f"user@example.com")
        user.set_password(f"password")
        db.session.add(user)

        for i in range(likes_count):
            liked_movie = LikedMovie(movie_id=randrange(1, 100), rating_author=user)
            db.session.add(liked_movie)

        db.session.commit()

        self.crs = CollaborativeRecommendationSystem(movies=self.movies, ratings=self.ratings)
        self.crs.initialise()

        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            print("Number of recommendations:", len(recommendations))
        else:
            self.fail("User not found.")

    def test_has_no_ratings_has_no_likes(self):

        self.movies = pd.read_csv("app/datasets/movies.csv")
        self.ratings = pd.read_csv("app/datasets/ratings.csv")

        user = User(username=f"user", email=f"user@example.com")
        user.set_password(f"password")
        db.session.add(user)

        db.session.commit()

        self.crs = CollaborativeRecommendationSystem(movies=self.movies, ratings=self.ratings)
        self.crs.initialise()

        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            print("Number of recommendations:", len(recommendations))
        else:
            self.fail("User not found.")

class TestContentRecommendationSystem(unittest.TestCase):

    def setUp(self):

        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):

        db.session.close()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_has_ratings(self):

        rating_count = 20
        ratings = [1.1, 1.7, 3.5, 2.4, 3.8, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4]

        self.movies = pd.read_csv("app/datasets/movies.csv")
        self.ratings = pd.read_csv("app/datasets/ratings.csv")

        user = User(username=f"user", email=f"user@example.com")
        user.set_password(f"password")
        db.session.add(user)

        for i in range(rating_count):
            movie_rating = MovieRating(movie_id=randrange(1, 100), rating=ratings[i], rating_author=user)
            db.session.add(movie_rating)

        db.session.commit()

        self.crs = ContentRecommendationSystem(self.movies, self.ratings)
        
        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            print("Number of recommendations:", len(recommendations))
        else:
            self.fail("User not found")
    
    def test_has_no_ratings(self):

        self.movies = pd.read_csv("app/datasets/movies.csv")
        self.ratings = pd.read_csv("app/datasets/ratings.csv")

        user = User(username=f"user", email=f"user@example.com")
        user.set_password(f"password")
        db.session.add(user)

        db.session.commit()

        self.crs = ContentRecommendationSystem(self.movies, self.ratings)

        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            print("Number of recommendations:", len(recommendations))
        else:
            self.fail("User not found")

class TestHybridRecommendationSystem(unittest.TestCase):

    def setUp(self):

        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def tearDown(self):

        db.session.close()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_has_ratings(self):

        rating_count = 20
        ratings = [1.1, 1.7, 3.5, 2.4, 3.8, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4]

        self.movies = pd.read_csv("app/datasets/movies.csv")
        self.ratings = pd.read_csv("app/datasets/ratings.csv")

        user = User(username=f"user", email=f"user@example.com")
        user.set_password(f"password")
        db.session.add(user)

        for i in range(rating_count):
            movie_rating = MovieRating(movie_id=randrange(1, 100), rating=ratings[i], rating_author=user)
            db.session.add(movie_rating)

        db.session.commit()

        self.crs = HybridRecommendationSystem(self.movies, self.ratings)

        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            print("Number of recommendations:", len(recommendations))
        else:
            self.fail()

    def test_has_no_ratings_has_likes(self):

        likes_count = 15
        self.movies = pd.read_csv("app/datasets/movies.csv")
        self.ratings = pd.read_csv("app/datasets/ratings.csv")

        user = User(username=f"user", email=f"user@example.com")
        user.set_password(f"password")
        db.session.add(user)

        for i in range(likes_count):
            liked_movie = LikedMovie(movie_id=randrange(1, 100), rating_author=user)
            db.session.add(liked_movie)

        db.session.commit()

        self.crs = HybridRecommendationSystem(self.movies, self.ratings)

        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            print("Number of recommendations:", len(recommendations))
        else:
            self.fail()

    def test_has_no_ratings_has_no_likes(self):

        self.movies = pd.read_csv("app/datasets/movies.csv")
        self.ratings = pd.read_csv("app/datasets/ratings.csv")

        user = User(username=f"user", email=f"user@example.com")
        user.set_password(f"password")
        db.session.add(user)

        db.session.commit()

        self.crs = HybridRecommendationSystem(self.movies, self.ratings)

        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            print("Number of recommendations:", len(recommendations))
        else:
            self.fail()

class TestMovieCaching(unittest.TestCase):

    def setUp(self):

        self.movies = pd.read_csv("app/datasets/movies.csv")
        self.ratings = pd.read_csv("app/datasets/ratings.csv")
        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def tearDown(self):

        db.session.close()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_find_movies_in_cache(self):

        rating_count = 20
        ratings = [1.1, 1.7, 3.5, 2.4, 3.8, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4]

        user = User(username=f"user", email=f"user@example.com")
        user.set_password(f"password")
        db.session.add(user)

        for i in range(rating_count):
            movie_rating = MovieRating(movie_id=randrange(1, 100), rating=ratings[i], rating_author=user)
            db.session.add(movie_rating)

        db.session.commit()

        self.crs = HybridRecommendationSystem(self.movies, self.ratings)

        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            for rec_obj in user.get_cached_recommendations():
                matching = False
                for rec in recommendations:
                    if rec["movieId"] == str(rec_obj.movie_id) and rec["score"] == rec_obj.score:
                        matching = True


                self.assertFalse(matching)
        else:
            self.fail()

if __name__ == "__main__":
    unittest.main()