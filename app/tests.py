from Data_Loader import *
from manager import *
from database import *
import pandas as pd
from line_profiler import LineProfiler
from urllib.request import urlretrieve
from zipfile import ZipFile
from os import mkdir
from os import path
import warnings
import progressbar

movies = None
ratings = None
datasets_base = "app/datasets/"
movies_path = "app/datasets/movies.csv"
ratings_path = "app/datasets/ratings.csv"
links_path = "app/datasets/links.csv"
tags_path = "app/datasets/tags.csv"
extracted_year_path = "app/datasets/extracted_year.csv"

# File download helper for downloading the datasets, mainly for the progress bar
class FileDownloader:
    def __init__(self):
        self.progress_bar = progressbar.ProgressBar(maxval=100)

    def download_file(self, url, callback):
        self.progress_bar.start()
        response = urlretrieve(url, reporthook=self.update_progress)
        self.progress_bar.finish()
        if callback != None:
            callback(response[0])

    def update_progress(self, blocknum, blocksize, totalsize):
        readed_data = blocknum * blocksize
        if totalsize > 0:
            download_percentage = readed_data * 100 / totalsize
            if ( download_percentage <= 100 ):
                self.progress_bar.update(download_percentage)


# Not sure where this will be in the final project so will leave it here for now
def datasets_initialisation(url):
    movies_exists = path.exists(movies_path)
    ratings_exists = path.exists(ratings_path)
    links_exists = path.exists(links_path)
    extracted_year_exists = path.exists(extracted_year_path)

    if not movies_exists or not ratings_exists or not links_exists:
        print("Downloading datasets from " + url)
        download_datasets(url)

    try:
        movies = pd.read_csv(movies_path)
        ratings = pd.read_csv(ratings_path)
        links = pd.read_csv(links_path)
        tags = pd.read_csv(tags_path)
    except FileNotFoundError as e:
        warnings.warn( "Could not find the datasets even after attempted download, cannot continue." )
        return None, None, None, None, None
    
    extracted_year = None

    if not extracted_year_exists:
        extract_year(movies, extracted_year_path)
    else:
        extracted_year = pd.read_csv(extracted_year_path)
        if len(extracted_year) != len(movies):
            extracted_year = extract_year(movies, extracted_year_path)
    
    return movies, ratings, links, tags, extracted_year

def download_datasets_callback(filepath):
    with ZipFile(filepath, "r") as zip_file:
        for zip_info in zip_file.infolist():
            if zip_info.is_dir():
                continue
            else:
                zip_info.filename = path.basename(zip_info.filename)
                if not path.exists(datasets_base):
                    mkdir(datasets_base)
                zip_file.extract(zip_info, datasets_base)

def download_datasets(url):
    fd = FileDownloader()
    fd.download_file(url, download_datasets_callback)

def standard_collaborative_recommendation_test(movies, ratings):
    crs = CollaborativeRecommendationSystem(movies, ratings)
    crs.initialise()
    results = crs.recommend(1, 3)
    print(results)

def standard_content_recommendation_test(movies, ratings):
    content = ContentRecommendationSystem(movies, ratings)
    print(content.recommend(1))

def extraction_test(movies):
    extract_year(movies, extracted_year_path)

#movies, ratings, links, tags, extracted_year = datasets_initialisation("https://files.grouplens.org/datasets/movielens/ml-32m.zip")
movies, ratings, links, tags, extracted_year = datasets_initialisation("https://files.grouplens.org/datasets/movielens/ml-latest-small.zip")

#standard_content_recommendation_test(movies, ratings)
#standard_collaborative_recommendation_test(movies, ratings)

def create_user_test( ):
    init_db()
    register_user( "test", "test" )
    user, key = login_user( "test", "test" )
    if ( user != None and key != None ):
        print( f"User creation test passed\nUser: {user.username}\nKey: {key}" )
        remove_user(User=user)
        print("User deleted")
    else:
        print( "User creation test failed" )

create_user_test()