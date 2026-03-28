from __future__ import annotations

import random
import unittest
from unittest.mock import patch

import pandas as pd
import sqlalchemy as sa
from cryptography.fernet import Fernet

from app import create_app, db, dataset_manager
from app.models import CachedRecommendation, LikedMovie, MovieRating, RecommendationSet, User
from app.recommender import (
    CollaborativeRecommendationSystem,
    ContentRecommendationSystem,
    HybridRecommendationSystem,
    UserRecommendationContext
)
from app.utils import ensure_test_dataset
from config import Config

TEST_DATASET_LOCATION = "api/app/test_temp/"

DATASETS = {
    "small": {
        "url": "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip",
        "zip_name": "ml-latest-small.zip",
    },
    "large": {
        "url": "https://files.grouplens.org/datasets/movielens/ml-32m.zip",
        "zip_name": "ml-32m.zip",
    },
}

DEFAULT_DATASET_KEY = "small"

TEST_KEY = Fernet.generate_key()
RANDOM_SEED = 42
COLLAB_TEST_KWARGS = {
    "min_user_ratings": 5,
    "min_movie_ratings": 5,
    "n_components": 16,
    "n_neighbors": 10,
    "random_state": RANDOM_SEED,
}

class TestConfig(Config):
    Testing = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    DATASETS_BASE = "api/app/test_datasets"
    MOVIES_PATH = "api/app/test_datasets/movies.csv"
    RATINGS_PATH = "api/app/test_datasets/ratings.csv"
    LINKS_PATH = "api/app/test_datasets/links.csv"
    TAGS_PATH = "api/app/test_datasets/tags.csv"
    EXTRACTED_YEAR_PATH = "api/app/test_datasets/extracted_year.csv"
    USE_SOCKETIO = False


class RecommendationTestBase(unittest.TestCase):
    app = None
    movies: pd.DataFrame | None = None
    ratings: pd.DataFrame | None = None
    valid_movie_ids: list[int] | None = None
    dataset_key = DEFAULT_DATASET_KEY

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.app = create_app(config_class=TestConfig)
        dataset_config = DATASETS[cls.dataset_key]

        with cls.app.app_context():
            ensure_test_dataset(
                dataset_manager=dataset_manager,
                dataset_url=dataset_config["url"],
                test_dataset_location=TEST_DATASET_LOCATION,
                local_filename=dataset_config["zip_name"],
            )

            cls.movies = pd.read_csv(cls.app.config["MOVIES_PATH"])
            cls.ratings = pd.read_csv(cls.app.config["RATINGS_PATH"])
            cls.valid_movie_ids = cls.movies["movieId"].astype(int).tolist()

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.key_patcher = patch("app.models.get_encryption_key", return_value=TEST_KEY)
        self.key_patcher.start()

        self.user = User(username="user", email="user@example.com")
        self.user.set_password("password")
        db.session.add(self.user)
        db.session.commit()

        self.random = random.Random(RANDOM_SEED)

    def tearDown(self):
        db.session.rollback()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        self.key_patcher.stop()

    def build_user_context(self, user: User | None = None) -> UserRecommendationContext:
        if user is None:
            user = self.get_user()

        ratings = user.get_user_ratings()
        liked_movies = user.get_liked_movies()

        rated_movie_ids = [int(r.movie_id) for r in ratings]
        liked_movie_ids = [int(m.movie_id) for m in liked_movies]

        seen_movie_ids = set(rated_movie_ids)
        seen_movie_ids.update(liked_movie_ids)

        positive_rated_movie_ids = [int(r.movie_id) for r in ratings if float(r.rating) >= 4.0]

        return UserRecommendationContext(
            ratings=ratings,
            liked_movies=liked_movies,
            rated_movie_ids=rated_movie_ids,
            liked_movie_ids=liked_movie_ids,
            seen_movie_ids=seen_movie_ids,
            positive_rated_movie_ids=positive_rated_movie_ids,
        )
    
    def assert_recommendation_shape(self, recommendations: list[dict], score_key: str) -> None:
        self.assertIsInstance(recommendations, list)
        for rec in recommendations:
            self.assertIn("movieId", rec)
            self.assertIn(score_key, rec)

    def get_user(self) -> User:
        user = db.session.scalar(sa.select(User).where(User.id == self.user.id))
        self.assertIsNotNone(user)
        return user

    def pick_movie_ids(self, count: int, excluded: set[int] | None = None) -> list[int]:
        if excluded is None:
            excluded = set()

        available = [movie_id for movie_id in self.valid_movie_ids if movie_id not in excluded]
        self.assertGreaterEqual(len(available), count)
        return self.random.sample(available, count)
    
    def add_ratings(self, score_values: list[float], movie_ids: list[int]) -> None:
        self.assertEqual(len(movie_ids), len(score_values))
        for movie_id, rating in zip(movie_ids, score_values):
            db.session.add(
                MovieRating(movie_id=str(movie_id), rating=str(rating), rating_author=self.user)
            )
        db.session.commit()
    
    def add_likes(self, movie_ids: list[int]) -> None:
        for movie_id in movie_ids:
            db.session.add(LikedMovie(movie_id=movie_id, rating_author=self.user))
        db.session.commit()
    
    def generate_random_ratings(
        self,
        positive_count: int,
        negative_count: int = 0,
        positive_range: tuple[float, float] = (4.0, 5.0),
        negative_range: tuple[float, float] = (0.5, 3.9),
        included: list[int] | None = None,
        excluded: list[int] | None = None,
    ):
        total = positive_count + negative_count
        movie_ids = None
        if included is not None:
            self.assertEqual(len(included), total)
            movie_ids = included
        else:
            movie_ids = self.pick_movie_ids(total, excluded=excluded)

        positive_scores = [
            round(self.random.uniform(*positive_range), 1)
            for _ in range(positive_count)
        ]
        negative_scores = [
            round(self.random.uniform(*negative_range), 1)
            for _ in range(negative_count)
        ]

        score_values = positive_scores + negative_scores
        self.random.shuffle(score_values)

        return movie_ids, score_values
    
    def pick_collab_movie_ids(
        self,
        recommender: CollaborativeRecommendationSystem,
        count: int,
        excluded: set[int] | None = None,
    ) -> list[int]:
        if excluded is None:
            excluded = set()

        available = [
            int(movie_id)
            for movie_id in recommender.movie_id_to_idx.keys()
            if int(movie_id) not in excluded
        ]

        self.assertGreaterEqual(len(available), count)
        return self.random.sample(available, count)

class TestCollaborativeRecommendationSystem(RecommendationTestBase):
    def build_recommender(self) -> CollaborativeRecommendationSystem:
        recommender = CollaborativeRecommendationSystem(
            movies=self.movies,
            ratings=self.ratings,
            **COLLAB_TEST_KWARGS,
        )
        recommender.initialise()
        return recommender

    def test_uses_positive_ratings_when_user_has_at_least_ten(self):
        recommender = self.build_recommender()
        
        movie_ids = self.pick_collab_movie_ids(recommender=recommender, count=20)
        movie_ids, score_values = self.generate_random_ratings(
                                        positive_count=10,
                                        negative_count=10,
                                        included=movie_ids
                                    )
        
        self.add_ratings(score_values=score_values, movie_ids=movie_ids)

        context = self.build_user_context()
        recommendations = recommender.recommend_from_context(context=context, top_n=10)

        self.assertGreaterEqual(len(context.positive_rated_movie_ids), 10)
        self.assertLessEqual(len(recommendations), 10)
        self.assertGreater(len(recommendations), 0)
        self.assert_recommendation_shape(recommendations, "similarity")
    
    def test_falls_back_to_likes_when_not_enough_positive_ratings(self):
        recommender = self.build_recommender()

        movie_ids = self.pick_collab_movie_ids(recommender, 20)
        movie_ids, score_values = self.generate_random_ratings(
                                        positive_count=9,
                                        negative_count=11,
                                        included=movie_ids
                                    )
        self.add_ratings(score_values, movie_ids)
        liked_movie_ids = self.pick_collab_movie_ids(recommender, 10, excluded=movie_ids)
        self.add_likes(liked_movie_ids)
        context = self.build_user_context()

        self.assertEqual(len(context.positive_rated_movie_ids), 9)
        self.assertEqual(len(context.liked_movie_ids), 10)

        recommendations = recommender.recommend_from_context(context, top_n=10)

        self.assertLessEqual(len(recommendations), 10)
        self.assertGreater(len(recommendations), 0)
        self.assert_recommendation_shape(recommendations, "similarity")

    def test_has_no_ratings_has_likes(self):
        recommender = self.build_recommender()

        liked_movie_ids = self.pick_collab_movie_ids(recommender, 10)
        self.add_likes(liked_movie_ids)
        context = self.build_user_context()

        self.assertEqual(len(context.ratings), 0)
        self.assertEqual(set(context.liked_movie_ids), set(liked_movie_ids))

        recommendations = recommender.recommend_from_context(context, top_n=10)

        self.assertLessEqual(len(recommendations), 10)
        self.assertLessEqual(len(recommendations), 10)
        self.assertGreater(len(recommendations), 0)
        self.assert_recommendation_shape(recommendations, "similarity")

    def test_has_no_ratings_has_no_likes(self):
        recommender = self.build_recommender()
        context = self.build_user_context()
        recommendations = recommender.recommend_from_context(context)
        self.assertEqual(recommendations, [])


class TestContentRecommendationSystem(RecommendationTestBase):
    def build_recommender(self) -> ContentRecommendationSystem:
        return ContentRecommendationSystem(self.movies, self.ratings)

    def test_has_ratings(self):
        movie_ids, score_values = self.generate_random_ratings(
                                        positive_count=10,
                                        negative_count=10,
                                    )
        self.add_ratings(score_values, movie_ids)
        recommender = self.build_recommender()
        context = self.build_user_context()
        recommendations = recommender.recommend_from_context(context, 10)

        self.assertLessEqual(len(recommendations), 10)
        self.assertGreater(len(recommendations), 0)
        self.assert_recommendation_shape(recommendations, "similarity")

    def test_has_no_ratings(self):
        recommender = self.build_recommender()
        context = self.build_user_context()
        recommendations = recommender.recommend_from_context(context)
        self.assertEqual(recommendations, [])


class LightweightHybridRecommendationSystem(HybridRecommendationSystem):
    def __init__(self, movies: pd.DataFrame, ratings: pd.DataFrame, collab_weight: float = 0.6, content_weight: float = 0.4):
        self.collab_weight = collab_weight
        self.content_weight = content_weight
        self.collab = CollaborativeRecommendationSystem(movies, ratings, **COLLAB_TEST_KWARGS)
        self.collab.initialise()
        self.content = ContentRecommendationSystem(movies, ratings)
        self.movies = movies
        self.ratings = ratings


class TestHybridRecommendationSystem(RecommendationTestBase):
    def build_recommender(self) -> HybridRecommendationSystem:
        return LightweightHybridRecommendationSystem(self.movies, self.ratings)

    def test_user_has_ratings(self):
        recommender = self.build_recommender()

        movie_ids = self.pick_collab_movie_ids(recommender=recommender.collab, count=20)
        movie_ids, score_values = self.generate_random_ratings(
                                        positive_count=10,
                                        negative_count=10,
                                        included=movie_ids
                                    )
        self.add_ratings(score_values, movie_ids)

        recommendations = recommender.recommend(self.get_user(), top_n=10, cache_result=False)

        self.assertLessEqual(len(recommendations), 10)
        self.assertGreater(len(recommendations), 0)
        self.assert_recommendation_shape(recommendations, "score")

    def test_has_no_ratings_has_likes(self):
        recommender = self.build_recommender()

        movie_ids = self.pick_collab_movie_ids(recommender=recommender.collab, count=20)
        self.add_likes(movie_ids)

        recommendations = recommender.recommend(self.get_user(), top_n=10, cache_result=False)

        self.assertLessEqual(len(recommendations), 10)
        self.assertGreater(len(recommendations), 0)
        self.assert_recommendation_shape(recommendations, "score")

    def test_has_no_ratings_has_no_likes(self):
        recommender = self.build_recommender()
        recommendations = recommender.recommend(self.get_user())
        self.assertEqual(recommendations, [])


class TestMovieCaching(RecommendationTestBase):
    def build_recommender(self) -> HybridRecommendationSystem:
        return LightweightHybridRecommendationSystem(self.movies, self.ratings)

    def test_recommendations_are_written_to_cache(self):
        recommender = self.build_recommender()

        movie_ids = self.pick_collab_movie_ids(recommender=recommender.collab, count=20)
        movie_ids, score_values = self.generate_random_ratings(
                                        positive_count=10,
                                        negative_count=10,
                                        included=movie_ids
                                    )
        self.add_ratings(score_values, movie_ids)
        
        user = self.get_user()
        recommendations = recommender.recommend(user)

        if not recommendations:
            self.skipTest("Hybrid recommender returned no recommendations for this fixture.")

        cached_sets = user.get_cached_recommendation_sets()
        self.assertEqual(len(cached_sets), 1)

        cached_rows = db.session.scalars(
            sa.select(CachedRecommendation).where(
                CachedRecommendation.user_set_id == cached_sets[0].id
            )
        ).all()

        self.assertEqual(len(cached_rows), len(recommendations))

        cached_by_movie = {int(row.movie_id): float(row.score) for row in cached_rows}
        expected_by_movie = {
            int(rec["movieId"]): float(rec["score"])
            for rec in recommendations
        }

        self.assertEqual(set(cached_by_movie.keys()), set(expected_by_movie.keys()))
        for movie_id, score in expected_by_movie.items():
            self.assertAlmostEqual(cached_by_movie[movie_id], score)

    def test_cache_keeps_latest_ten_sets(self):
        user = self.get_user()
        movie_ids = self.pick_movie_ids(12)
        for i in range(12):
            user.cache_recommendation_set([
                {"movieId": movie_ids[i], "score": float(i)}
            ])

        cached_sets = db.session.scalars(
            sa.select(RecommendationSet)
            .where(RecommendationSet.user == user)
            .order_by(RecommendationSet.timestamp.desc())
        ).all()
        self.assertEqual(len(cached_sets), 10)

        cached_movie_ids = {
            int(row.movie_id)
            for set_ in cached_sets
            for row in db.session.scalars(
                sa.select(CachedRecommendation).where(CachedRecommendation.user_set_id == set_.id)
            ).all()
        }

        self.assertNotIn(movie_ids[0], cached_movie_ids)
        self.assertNotIn(movie_ids[1], cached_movie_ids)
        self.assertIn(movie_ids[11], cached_movie_ids)

    def test_recommendation_set_cascade_delete(self):
        user = self.get_user()

        user.cache_recommendation_set([
            {"movieId": 1, "score": 4.0}
        ])

        rec_set = db.session.scalar(
            sa.select(RecommendationSet)
            .where(RecommendationSet.user == user)
        )

        cached_rows = db.session.scalars(
            sa.select(CachedRecommendation)
            .where(CachedRecommendation.user_set_id == rec_set.id)
        ).all()

        self.assertGreater(len(cached_rows), 0)

        db.session.delete(rec_set)
        db.session.commit()

        remaining = db.session.scalars(
            sa.select(CachedRecommendation)
        ).all()

        self.assertEqual(len(remaining), 0)

if __name__ == "__main__":
    unittest.main()