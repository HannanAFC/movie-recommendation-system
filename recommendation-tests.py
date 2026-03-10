from app.recommender import CollaborativeRecommendationSystem, ContentRecommendationSystem, HybridRecommendationSystem
import unittest
from unittest.mock import patch
from app import create_app, db, dataset_manager
from config import Config
from app.models import User, MovieRating, LikedMovie, CachedRecommendation
from random import randrange
import sqlalchemy as sa
import pandas as pd
from app.utils import prepare_test_environment
import shutil
import os
from cryptography.fernet import Fernet

test_dataset_location = "app/test_temp/"
local_filename = "test_dataset.zip"

TEST_KEY = Fernet.generate_key()

class TestConfig(Config):
    Testing = True
    # Redirect SQLAlchemy to special in-memory database for tests
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    DATASETS_BASE = "app/test_datasets"
    MOVIES_PATH = "app/test_datasets/movies.csv"
    RATINGS_PATH = "app/test_datasets/ratings.csv"
    LINKS_PATH = "app/test_datasets/links.csv"
    TAGS_PATH = "app/test_datasets/tags.csv"
    EXTRACTED_YEAR_PATH = "app/test_datasets/extracted_year.csv"

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

        dataset_manager._DatasetManager__parse_downloaded_dataset(test_dataset_location + local_filename)
        dataset_manager.validate_download()

        self.user = User(username=f"user", email=f"user@example.com")
        self.user.set_password(f"password")
        db.session.add(self.user)
        db.session.commit()

        self.movies = pd.read_csv(self.app.config["MOVIES_PATH"])
        self.ratings = pd.read_csv(self.app.config["RATINGS_PATH"])

    def tearDown(self):

        db.session.close()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

        try:
            shutil.rmtree(self.app.config["DATASETS_BASE"])
        except FileNotFoundError:
            pass
        os.makedirs(self.app.config["DATASETS_BASE"], exist_ok=True)

    @patch("app.models.get_encryption_key")
    def test_has_ratings(self, mock_key):

        mock_key.return_value = TEST_KEY

        rating_count = 20
        ratings = [1.1, 1.7, 3.5, 2.4, 3.8, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4]        

        for i in range(rating_count):
            movie_rating = MovieRating(movie_id=randrange(1, 100), rating=ratings[i], rating_author=self.user)
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

    @patch("app.models.get_encryption_key")
    def test_has_no_ratings_has_likes(self, mock_key):

        mock_key.return_value = TEST_KEY

        likes_count = 15

        for i in range(likes_count):
            liked_movie = LikedMovie(movie_id=randrange(1, 100), rating_author=self.user)
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

    @patch("app.models.get_encryption_key")
    def test_has_no_ratings_has_no_likes(self, mock_key):

        mock_key.return_value = TEST_KEY

        self.crs = CollaborativeRecommendationSystem(movies=self.movies, ratings=self.ratings)
        self.crs.initialise()

        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            print("Number of recommendations:", len(recommendations))
            self.assertEqual(len(recommendations), 0)
        else:
            self.fail("User not found.")

class TestContentRecommendationSystem(unittest.TestCase):

    def setUp(self):

        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        dataset_manager._DatasetManager__parse_downloaded_dataset(test_dataset_location + local_filename)
        dataset_manager.validate_download()

        self.movies = pd.read_csv(self.app.config["MOVIES_PATH"])
        self.ratings = pd.read_csv(self.app.config["RATINGS_PATH"])

        self.user = User(username=f"user", email=f"user@example.com")
        self.user.set_password(f"password")
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):

        db.session.close()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

        try:
            shutil.rmtree(self.app.config["DATASETS_BASE"])
        except FileNotFoundError:
            pass
        os.makedirs(self.app.config["DATASETS_BASE"], exist_ok=True)

    @patch("app.models.get_encryption_key")
    def test_has_ratings(self, mock_key):

        mock_key.return_value = TEST_KEY

        rating_count = 20
        ratings = [1.1, 1.7, 3.5, 2.4, 3.8, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4]

        for i in range(rating_count):
            movie_rating = MovieRating(movie_id=randrange(1, 100), rating=ratings[i], rating_author=self.user)
            db.session.add(movie_rating)

        db.session.commit()

        self.crs = ContentRecommendationSystem(self.movies, self.ratings)
        
        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            print("Number of recommendations:", len(recommendations))
        else:
            self.fail("User not found")
    
    @patch("app.models.get_encryption_key")
    def test_has_no_ratings(self, mock_key):

        mock_key.return_value = TEST_KEY

        self.movies = pd.read_csv(self.app.config["MOVIES_PATH"])
        self.ratings = pd.read_csv(self.app.config["RATINGS_PATH"])

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

        dataset_manager._DatasetManager__parse_downloaded_dataset(test_dataset_location + local_filename)
        dataset_manager.validate_download()

        self.movies = pd.read_csv(self.app.config["MOVIES_PATH"])
        self.ratings = pd.read_csv(self.app.config["RATINGS_PATH"])

        self.user = User(username=f"user", email=f"user@example.com")
        self.user.set_password(f"password")
        db.session.add(self.user)
        db.session.commit()
    
    def tearDown(self):

        db.session.close()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch("app.models.get_encryption_key")
    def test_user_has_ratings(self, mock_key):

        mock_key.return_value = TEST_KEY

        rating_count = 20
        ratings = [1.1, 1.7, 3.5, 2.4, 3.8, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4]

        for i in range(rating_count):
            movie_rating = MovieRating(movie_id=randrange(1, 100), rating=ratings[i], rating_author=self.user)
            db.session.add(movie_rating)

        db.session.commit()

        self.crs = HybridRecommendationSystem(self.movies, self.ratings)

        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            print("Number of recommendations:", len(recommendations))
        else:
            self.fail()

    @patch("app.models.get_encryption_key")
    def test_has_no_ratings_has_likes(self, mock_key):

        mock_key.return_value = TEST_KEY

        likes_count = 15

        for i in range(likes_count):
            liked_movie = LikedMovie(movie_id=randrange(1, 100), rating_author=self.user)
            db.session.add(liked_movie)

        db.session.commit()

        self.crs = HybridRecommendationSystem(self.movies, self.ratings)

        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            print("Number of recommendations:", len(recommendations))
        else:
            self.fail()

    @patch("app.models.get_encryption_key")
    def test_has_no_ratings_has_no_likes(self, mock_key):

        mock_key.return_value = TEST_KEY

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

        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        dataset_manager._DatasetManager__parse_downloaded_dataset(test_dataset_location + local_filename)
        dataset_manager.validate_download()

        self.movies = pd.read_csv(self.app.config["MOVIES_PATH"])
        self.ratings = pd.read_csv(self.app.config["RATINGS_PATH"])

        self.user = User(username=f"user", email=f"user@example.com")
        self.user.set_password(f"password")
        db.session.add(self.user)
    
    def tearDown(self):

        db.session.close()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

        try:
            shutil.rmtree(self.app.config["DATASETS_BASE"])
        except FileNotFoundError:
            pass
        os.makedirs(self.app.config["DATASETS_BASE"], exist_ok=True)

    @patch("app.models.get_encryption_key")
    def test_find_movies_in_cache(self, mock_key):

        mock_key.return_value = TEST_KEY

        rating_count = 20
        ratings = [1.1, 1.7, 3.5, 2.4, 3.8, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4]

        for i in range(rating_count):
            movie_rating = MovieRating(movie_id=randrange(1, 100), rating=ratings[i], rating_author=self.user)
            db.session.add(movie_rating)

        db.session.commit()

        self.crs = HybridRecommendationSystem(self.movies, self.ratings)

        user = db.session.scalar(sa.select(User).where(User.id == 1))
        if (user != None):
            recommendations = self.crs.recommend(user=user)
            for rec_set in user.get_cached_recommendation_sets():
                matching = False
                for rec_obj in CachedRecommendation.query.filter_by(user_set_id = rec_set.id).limit(1):
                    for rec in recommendations:
                        if rec["movieId"] == str(rec_obj.movie_id) and rec["score"] == rec_obj.score:
                            matching = True

                self.assertFalse(matching)
        else:
            self.fail()

if __name__ == "__main__":
    prepare_test_environment("https://files.grouplens.org/datasets/movielens/ml-latest-small.zip", test_dataset_location, local_filename)
    unittest.main()