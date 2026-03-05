from nh3 import clean
from email.utils import parseaddr
from flask import Request
from pandas import DataFrame
import progressbar
from urllib.request import urlretrieve
from typing import Callable

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

class FileDownloader:
    """
    File download helper for downloading the datasets, mainly for the progress bar.
    """
    def __init__(self):
        self.progress_bar = progressbar.ProgressBar(maxval=100)

    def download_file(self, url: str, callback: Callable) -> None:
        """
        Download a file from a url and call a callback function when done with the filepath as the parameter.
        Parameters:
           url (str): the url to download from.
           callback (Callable): the callback function to call when done with the filepath as the parameter.
        """
        self.progress_bar.start()
        response = urlretrieve(url, reporthook=self.update_progress)
        self.progress_bar.finish()
        if callback != None:
            callback(response[0])

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
            if ( download_percentage <= 100 ):
                self.progress_bar.update(download_percentage)