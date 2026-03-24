import sqlalchemy as sa
from unittest.mock import patch
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from app.recommender import *
from app import create_app, db, dataset_manager
from config import Config
from cryptography.fernet import Fernet
from random import randrange
from app.utils import prepare_test_environment
test_dataset_location = "app/test_temp/"
local_filename = "test_dataset.zip"
prepare_test_environment("https://files.grouplens.org/datasets/movielens/ml-latest-small.zip", test_dataset_location, local_filename)

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

with patch("app.models.get_encryption_key") as mock_function:
    mock_function.return_value = TEST_KEY
    app = create_app(config_class=TestConfig)
    app_context = app.app_context()
    app_context.push()
    db.create_all()

    dataset_manager._DatasetManager__parse_downloaded_dataset(test_dataset_location + local_filename)
    dataset_manager.validate_download()

    user = User(username=f"user", email=f"user@example.com")
    user.set_password(f"password")
    db.session.add(user)
    db.session.commit()

    rating_count = 20
    ratings = [1.1, 1.7, 3.5, 2.4, 3.8, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4, 4.1, 4.2, 4.2, 4.1, 4,4]        

    for i in range(rating_count):
        movie_rating = MovieRating(movie_id=randrange(1, 100), rating=ratings[i], rating_author=user)
        db.session.add(movie_rating)

    db.session.commit()

    movies = pd.read_csv(app.config["MOVIES_PATH"])
    ratings = pd.read_csv(app.config["RATINGS_PATH"])

    crs = HybridRecommendationSystem(movies, ratings)

    user = db.session.scalar(sa.select(User).where(User.id == 1))
    if (user != None):
        recommendations = crs.recommend(user=user)
        print("Number of recommendations:", len(recommendations))
        
    sns.histplot(ratings["rating"], bins=20)
    plt.title("Ratings Distribution")
    plt.xlabel("Rating")
    plt.ylabel("Count")
    plt.savefig("ratingDistribution.png")
    
    rec_df = pd.DataFrame(recommendations)

    # Merge titles if missing
    if "title" not in rec_df.columns:
        rec_df = rec_df.merge(movies, on="movieId")

    # Clean data
    rec_df = rec_df.drop_duplicates(subset="movieId")

    # ✅ DEFINE top_n HERE
    top_n = rec_df.sort_values(by="score", ascending=False).head(10)

    # ✅ THEN plot
    plt.figure(figsize=(10, 6))
    sns.barplot(data=top_n, x="score", y="title")

    plt.title("Top 10 Recommended Movies")
    plt.tight_layout()
    
    plt.savefig("topRecommendations.png")