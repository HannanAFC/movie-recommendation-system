import unittest
from app import create_app, db, dataset_manager
import os
import shutil
from config import Config
from app.utils import prepare_test_environment

test_dataset_location = "app/test_temp/"
local_filename = "test_dataset.zip"

class TestConfig(Config):
    Testing = True
    SQLALCHEMY_DATABASE_URI = "sqlite:////app/data/db/app.db"
    DATASETS_BASE = "app/test_datasets"
    MOVIES_PATH = "app/test_datasets/movies.csv"
    RATINGS_PATH = "app/test_datasets/ratings.csv"
    LINKS_PATH = "app/test_datasets/links.csv"
    TAGS_PATH = "app/test_datasets/tags.csv"
    EXTRACTED_YEAR_PATH = "app/test_datasets/extracted_year.csv"

class TestDatasetManager(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

        try:
            shutil.rmtree(self.app.config["DATASETS_BASE"])
        except FileNotFoundError:
            pass
        os.makedirs(self.app.config["DATASETS_BASE"], exist_ok=True)

    def test_full_parsing(self):
        try:
            shutil.rmtree(self.app.config["DATASETS_BASE"])
        except FileNotFoundError:
            pass
        os.makedirs(self.app.config["DATASETS_BASE"], exist_ok=True)

        if not os.path.exists(test_dataset_location + local_filename):
            self.fail("Test dataset not found, can't start test.")

        dataset_manager._DatasetManager__parse_downloaded_dataset(test_dataset_location + local_filename)
        dataset_manager.validate_download()
        
        paths_exist = (
            os.path.exists(self.app.config["DATASETS_BASE"]) and
            os.path.exists(self.app.config["MOVIES_PATH"]) and
            os.path.exists(self.app.config["RATINGS_PATH"]) and
            os.path.exists(self.app.config["TAGS_PATH"]) and
            os.path.exists(self.app.config["LINKS_PATH"]) and
            os.path.exists(self.app.config["EXTRACTED_YEAR_PATH"])
        )
        self.assertTrue(paths_exist)

    def test_partial_missing(self):
        try:
            shutil.rmtree(self.app.config["DATASETS_BASE"])
        except FileNotFoundError:
            print("Base path not found")
            
        dataset_manager._DatasetManager__parse_downloaded_dataset(test_dataset_location + local_filename)
        dataset_manager.validate_download()
        os.remove(self.app.config["MOVIES_PATH"] )

        dataset_manager._DatasetManager__parse_downloaded_dataset(test_dataset_location + local_filename)
        dataset_manager.validate_download()

        paths_exist = (
            os.path.exists(self.app.config["DATASETS_BASE"]) and
            os.path.exists(self.app.config["MOVIES_PATH"]) and
            os.path.exists(self.app.config["RATINGS_PATH"]) and
            os.path.exists(self.app.config["TAGS_PATH"]) and
            os.path.exists(self.app.config["LINKS_PATH"]) and
            os.path.exists(self.app.config["EXTRACTED_YEAR_PATH"])
        )
        self.assertTrue(paths_exist)

if __name__ == "__main__":
    prepare_test_environment("https://files.grouplens.org/datasets/movielens/ml-latest-small.zip", test_dataset_location, local_filename)
    unittest.main()