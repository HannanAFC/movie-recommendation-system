from nh3 import clean
from flask import Flask, Request
import pandas as pd
from pandas import DataFrame
import progressbar
from urllib.request import urlretrieve
from typing import Callable
from os import path, mkdir
from pathlib import Path
from zipfile import ZipFile
import warnings
import requests
import shutil

def sanitise_form_inputs(request: Request, fields: list[str]) -> dict[str, str | None]:
    """
    Sanitise the form inputs from a flask request and return as a dictionary.
    Parameters:
        request (flask.Request): the flask request object.
        fields (list[str]): a list of form inputs to sanitise.
    """
    values = {}
    for field in fields:
        value = request.form.get(field)
        if value != None:
            values[field] = clean(value)
        else:
            values[field] = None
    return values


def extract_year(movies: DataFrame, file_path: str) -> None:
    """
    Helper function - extracts the years in the movie title into a new column, only run once.
    Parameters:
       movies (pandas.DataFrame): the movies dataframe.
       file_path (str): the path to save the new csv file.
    """

    # Extract year from title string and place into new column
    movies["year"] = movies["title"].str.extract(r"\((\d{4})\)")
    movies["title"] = movies["title"].str.replace(r"\(\d{4}\)", "", regex=True)

    movies.to_csv(file_path, index=False)


def prepare_test_environment(url: str, test_dataset_location: str, local_filename: str) -> str:
    """
    Ensure that a local copy of the test dataset archive exists and return its filepath.
    """
    location = Path(test_dataset_location)
    location.mkdir(parents=True, exist_ok=True)

    archive_path = location / local_filename
    if not archive_path.exists():
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(archive_path, "wb") as f:
                shutil.copyfileobj(response.raw, f)

    return str(archive_path)

def ensure_test_dataset(
    dataset_manager,
    dataset_url: str,
    test_dataset_location: str,
    local_filename: str,
    marker_filename: str = "current_dataset.txt",
) -> str:
    location = Path(test_dataset_location)
    location.mkdir(parents=True, exist_ok=True)

    archive_path = Path(
        prepare_test_environment(dataset_url, test_dataset_location, local_filename)
    )

    current_dataset = read_current_dataset(test_dataset_location + "/" + marker_filename)

    extracted_files_exist = dataset_manager.dataset_exists()
    dataset_matches = current_dataset == local_filename

    if not (dataset_matches and extracted_files_exist):
        datasets_base = Path(dataset_manager.app.config["DATASETS_BASE"])
        shutil.rmtree(datasets_base, ignore_errors=True)
        datasets_base.mkdir(parents=True, exist_ok=True)

        dataset_manager._DatasetManager__parse_downloaded_dataset(str(archive_path))
        dataset_manager.validate_download()
        marker_path = location / marker_filename
        marker_path.write_text(local_filename, encoding="utf-8")

    return str(archive_path)

def write_current_dataset(dataset_id: str, marker_path: str) -> None:
    """
    Write the identifier of the current dataset to local storage.
    Parameters:
        dataset_id (str):  identifier of the dataset currently installed.
        marker_path (str): local path to the dataset marker file.
    """
    path = Path(marker_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dataset_id, encoding="utf-8")


def read_current_dataset(marker_path: str) -> str | None:
    """
    Read the identifier of the current dataset from local storage.
    Parameters:
        marker_path (str): local path to the dataset marker file.
    """
    path = Path(marker_path)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip() or None

class FileDownloader:
    """
    File download helper for downloading the datasets, mainly for the progress bar.
    """

    def __init__(self):
        self.progress_bar = progressbar.ProgressBar(maxval=100)

    def download_file(self, url: str, after_download_cb: Callable, progress_cb: Callable) -> None:
        """
        Download a file from a url and call a callback function when done with the filepath as the parameter.
        Parameters:
           url (str): the url to download from.
           callback (Callable): the callback function to call when done with the filepath as the parameter.
        """
        if callable(progress_cb):
            response = urlretrieve(url, reporthook=progress_cb)
        else:
            self.progress_bar.start()
            response = urlretrieve(url, reporthook=self.update_progress)
        if not callable(progress_cb):
            self.progress_bar.finish()
        if after_download_cb != None:
            after_download_cb(response[0])

    def update_progress(self, blocknum: int, blocksize: int, totalsize: int) -> None:
        """
        Update the progress bar with the current progress.
        Parameters:
            blocknum (int): the current block number.
            blocksize (int): the size of the current block.
            totalsize (int): the total size of the file.
        """
        readed_data = blocknum * blocksize
        if totalsize > 0:
            download_percentage = readed_data * 100 / totalsize
            if download_percentage <= 100:
                self.progress_bar.update(download_percentage)


class DatasetManager:
    def init_app(self, app: Flask) -> None:
        """
        Initialize the dataset manager.
        Parameters:
            app (Flask): the Flask app.
        """
        self.app = app
        self.datasets_base = app.config["DATASETS_BASE"]
        self.movies_path = app.config["MOVIES_PATH"]
        self.ratings_path = app.config["RATINGS_PATH"]
        self.links_path = app.config["LINKS_PATH"]
        self.tags_path = app.config["TAGS_PATH"]
        self.extracted_year_path = app.config["EXTRACTED_YEAR_PATH"]
        self.movies = None
        self.ratings = None
        self.links = None
        self.tags = None
        self.extracted_year = None
        self.file_downloader = FileDownloader()

    def dataset_exists(self) -> bool:
        """
        Check for the presence of the datasets.
        """
        movies_exists = path.exists(self.movies_path)
        ratings_exists = path.exists(self.ratings_path)
        links_exists = path.exists(self.links_path)

        extracted_year_exists = path.exists(self.extracted_year_path)

        datasets_exist = movies_exists and ratings_exists and links_exists

        if not datasets_exist:
            return False

        if not extracted_year_exists and self.movies != None:
            extract_year(self.movies, self.extracted_year_path)

        return True

    def downloadable_datasets(self) -> list[str]:
        """
        Return a list of identifiers for downloadable datasets.
        """
        return self.app.config["DATASET_URLS"]

    def download_dataset(self, dataset_identifier: str, progress_callback: Callable = None) -> None:
        """
        Download the dataset based on the selected dataset identifier.
        Parameters:
            dataset_identifier (str): identifier of the dataset to download.
        """
        dataset = next(
            (dataset for dataset in self.app.config["DATASET_URLS"]
            if dataset["identifier"] == dataset_identifier),
            None
        )

        if dataset is None:
            raise ValueError(f"Unknown dataset identifier: {dataset_identifier}")

        url = dataset["url"]

        print("Downloading datasets from " + url)
        self.file_downloader.download_file(
            url=url,
            after_download_cb=lambda filepath: self.__parse_downloaded_dataset(
                filepath,
                dataset_identifier
            ),
            progress_cb=progress_callback,
        )

        self.validate_download()

    def __parse_downloaded_dataset(self, filepath: str, dataset_identifier: str) -> None:
        """
        Callback for filedownloader to call after download finish.
        Parameters:
            filepath (str): filepath of the zipfile.
            dataset_identifier (str): identifier of the dataset being extracted.
        """
        with ZipFile(filepath, "r") as zip_file:
            for zip_info in zip_file.infolist():
                if zip_info.is_dir():
                    continue
                zip_info.filename = path.basename(zip_info.filename)
                if not path.exists(self.datasets_base):
                    mkdir(self.datasets_base)
                zip_file.extract(zip_info, self.datasets_base)
            write_current_dataset(dataset_identifier, self.app.config["CURRENT_DATASET_PATH"])

    def validate_download(self):
        try:
            movies = pd.read_csv(self.movies_path)
            ratings = pd.read_csv(self.ratings_path)
            links = pd.read_csv(self.links_path)
            tags = pd.read_csv(self.tags_path)
        except FileNotFoundError:
            warnings.warn(
                "Could not find the datasets even after attempted download, cannot continue."
            )
            return

        self.movies = movies
        self.ratings = ratings
        self.links = links
        self.tags = tags

        extracted_year = None

        if not path.exists(self.extracted_year_path):
            extract_year(movies, self.extracted_year_path)
        else:
            extracted_year = pd.read_csv(self.extracted_year_path)
            if len(extracted_year) != len(movies):
                extracted_year = extract_year(movies, self.extracted_year_path)

        self.extracted_year = extracted_year