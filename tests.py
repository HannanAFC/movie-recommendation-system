from app.utils import extract_year, FileDownloader
import pandas as pd
from line_profiler import LineProfiler
from zipfile import ZipFile
from os import mkdir
from os import path
import warnings

movies = None
ratings = None
datasets_base = "app/datasets/"
movies_path = "app/datasets/movies.csv"
ratings_path = "app/datasets/ratings.csv"
links_path = "app/datasets/links.csv"
tags_path = "app/datasets/tags.csv"
extracted_year_path = "app/datasets/extracted_year.csv"

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

#movies, ratings, links, tags, extracted_year = datasets_initialisation("https://files.grouplens.org/datasets/movielens/ml-32m.zip")
movies, ratings, links, tags, extracted_year = datasets_initialisation("https://files.grouplens.org/datasets/movielens/ml-latest-small.zip")
