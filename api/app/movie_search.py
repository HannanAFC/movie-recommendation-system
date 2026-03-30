# This also feels to important to be in the utils.py file.

import re
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


class MovieSearchService:
    """
    Searches the local dataset catalog and enriches results with TMDB metadata. For performance the search index is stored locally.
    """

    def init_app(self, app) -> None:
        """
        Initialise the movie search service with the Flask application.
        Parameters:
            app (Flask): the Flask app.
        """
        self.app = app
        self.index_path = app.config["SEARCH_INDEX_PATH"]
        self.index_version = app.config["SEARCH_INDEX_VERSION"]

        self.movies_by_id: dict[int, dict[str, Any]] = {}
        self.token_index: dict[str, set[int]] = {}
        self.normalized_titles: dict[int, str] = {}

        self.is_ready = False
        self.status_message: str | None = None

    def _set_status(self, is_ready: bool, status_message: str | None = None) -> None:
        """
        Update the current status of the movie search service.
        Parameters:
            is_ready (bool):             whether the search service is currently ready to be used.
            status_message (str | None): message describing the current status.
        """
        self.is_ready = is_ready
        self.status_message = status_message

    def get_status(self) -> dict[str, Any]:
        """
        Get the current status of the movie search service for use by the application or web UI.
        """
        return {
            "is_ready": self.is_ready,
            "status_message": self.status_message
        }

    def _normalise_title(self, title: str) -> str:
        """
        Normalise a title into a search-friendly format.
        Parameters:
            title (str): title to normalise.
        """
        if not title:
            return ""

        title = title.lower()
        title = re.sub(r"[^a-z0-9\s]", " ", title)
        title = re.sub(r"\s+", " ", title).strip()
        return title

    def _tokenise(self, value: str) -> list[str]:
        """
        Tokenise a normalised string into search tokens.
        Parameters:
            value (str): normalised string to tokenise.
        """
        if not value:
            return []
        return [token for token in value.split(" ") if token]

    def _extract_year_from_query(self, query: str) -> tuple[str, int | None]:
        """
        Extract a year from a search query if one is present.
        Parameters:
            query (str): raw search query.
        """
        year_match = re.search(r"\b(18|19|20)\d{2}\b", query)
        year = int(year_match.group(0)) if year_match else None

        if year_match:
            query = re.sub(r"\b(18|19|20)\d{2}\b", " ", query)
            query = re.sub(r"\s+", " ", query).strip()

        return query, year

    def _build_index_metadata(self, dataset_id: str | None = None) -> dict[str, Any]:
        """
        Build the metadata used to determine whether a saved search index matches the current dataset/configuration.
        Parameters:
            dataset_id (str | None): identifier for the dataset being used.
        """
        return {
            "dataset_id": dataset_id,
            "index_version": self.index_version
        }

    def index_exists(self, index_path: str | None = None) -> bool:
        """
        Check whether a saved search index exists at the given local path.
        Parameters:
            index_path (str | None): local path to check for a saved search index.
        """
        path = Path(index_path or self.index_path)
        return path.exists()

    def index_is_compatible(
        self,
        dataset_id: str | None = None,
        index_path: str | None = None
    ) -> bool:
        """
        Check whether a saved search index matches the current dataset/configuration.
        Parameters:
            dataset_id (str | None): identifier for the dataset expected by the current application run.
            index_path (str | None): local path of the saved index to validate.
        """
        path = Path(index_path or self.index_path)
        if not path.exists():
            return False

        data = joblib.load(path)
        saved_metadata = data.get("metadata")

        if saved_metadata is None:
            return False

        expected_metadata = self._build_index_metadata(dataset_id)
        return saved_metadata == expected_metadata

    def save_index(self, dataset_id: str | None = None, index_path: str | None = None) -> None:
        """
        Save the preprocessed movie search index locally.
        Parameters:
            dataset_id (str | None): identifier for the dataset used to build the index.
            index_path (str | None): local path to save the search index to.
        """
        path = Path(index_path or self.index_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        index_data = {
            "metadata": self._build_index_metadata(dataset_id),
            "movies_by_id": self.movies_by_id,
            "token_index": self.token_index,
            "normalized_titles": self.normalized_titles
        }

        temp_path = path.with_suffix(path.suffix + ".tmp")
        joblib.dump(index_data, temp_path)
        temp_path.replace(path)

    def load_index(self, index_path: str | None = None) -> None:
        """
        Load a previously saved movie search index from local storage.
        Parameters:
            index_path (str | None): local path to load the search index from.
        """
        path = Path(index_path or self.index_path)
        if not path.exists():
            raise FileNotFoundError(f"Movie search index not found at {path}")

        data = joblib.load(path)

        self.movies_by_id = data["movies_by_id"]
        self.token_index = data["token_index"]
        self.normalized_titles = data["normalized_titles"]

        self._set_status(
            is_ready=True,
            status_message="Movie search index loaded successfully."
        )

    def build_index(self, movies: pd.DataFrame, links: pd.DataFrame) -> None:
        """
        Build the movie search index from the local dataset catalog.
        Parameters:
            movies (DataFrame): movies.csv converted to a dataframe to use.
            links (DataFrame):  links.csv converted to a dataframe to use.
        """
        if movies.empty or links.empty:
            raise ValueError("Movies and links dataframes must contain data.")

        movies = movies.copy()
        links = links.copy()

        movies["movieId"] = movies["movieId"].astype("int32")
        links["movieId"] = links["movieId"].astype("int32")

        tmdb_lookup = {}
        for row in links.itertuples(index=False):
            tmdb_id = getattr(row, "tmdbId", None)
            if pd.notna(tmdb_id):
                try:
                    tmdb_lookup[int(row.movieId)] = int(tmdb_id)
                except (TypeError, ValueError):
                    tmdb_lookup[int(row.movieId)] = None
            else:
                tmdb_lookup[int(row.movieId)] = None

        self.movies_by_id = {}
        self.token_index = {}
        self.normalized_titles = {}

        for row in movies.itertuples(index=False):
            movie_id = int(row.movieId)
            title = str(row.title)
            genres_raw = getattr(row, "genres", "")
            genres = [genre for genre in str(genres_raw).split("|") if genre and genre != "(no genres listed)"]

            title_without_year = re.sub(r"\s*\(\d{4}\)\s*$", "", title).strip()
            year_match = re.search(r"\((\d{4})\)\s*$", title)
            year = int(year_match.group(1)) if year_match else None

            normalized_title = self._normalise_title(title_without_year)
            tokens = self._tokenise(normalized_title)

            movie_record = {
                "movieId": movie_id,
                "title": title_without_year,
                "year": year,
                "genres": genres,
                "tmdbId": tmdb_lookup.get(movie_id),
                "normalized_title": normalized_title,
                "tokens": tokens
            }

            self.movies_by_id[movie_id] = movie_record
            self.normalized_titles[movie_id] = normalized_title

            for token in set(tokens):
                if token not in self.token_index:
                    self.token_index[token] = set()
                self.token_index[token].add(movie_id)

        self._set_status(
            is_ready=True,
            status_message="Movie search index built successfully."
        )

    def initialise_from_storage(
        self,
        movies: pd.DataFrame,
        links: pd.DataFrame,
        dataset_id: str | None = None
    ) -> None:
        """
        Load a saved movie search index when available, otherwise build and save a new one.
        Parameters:
            movies (DataFrame):      movies.csv converted to a dataframe to use.
            links (DataFrame):       links.csv converted to a dataframe to use.
            dataset_id (str | None): identifier for the dataset expected by the current application run.
        """
        if self.index_exists() and self.index_is_compatible(dataset_id):
            self.load_index()
            return

        self.build_index(movies, links)
        self.save_index(dataset_id)

    def _score_movie(
        self,
        movie_record: dict[str, Any],
        normalized_query: str,
        query_tokens: list[str],
        query_year: int | None
    ) -> float:
        """
        Score a movie record against the search query.
        Parameters:
            movie_record (dict[str, Any]): movie record from the local search index.
            normalized_query (str):        normalised search query.
            query_tokens (list[str]):      tokenised search query.
            query_year (int | None):       extracted year from the search query.
        """
        normalized_title = movie_record["normalized_title"]
        movie_tokens = set(movie_record["tokens"])

        score = 0.0

        if normalized_query == normalized_title:
            score += 100.0

        if normalized_title.startswith(normalized_query):
            score += 50.0

        if normalized_query and normalized_query in normalized_title:
            score += 30.0

        matched_tokens = len(movie_tokens.intersection(query_tokens))
        score += matched_tokens * 10.0

        if query_year is not None and movie_record["year"] == query_year:
            score += 20.0

        # Slight preference for shorter exact-ish titles
        score -= abs(len(normalized_title) - len(normalized_query)) * 0.1

        return score

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Search the local dataset catalog for matching movies.
        Parameters:
            query (str): search query entered by the user.
            limit (int): maximum number of results to return.
        """
        if not self.is_ready:
            raise RuntimeError(
                self.status_message or "Movie search service is not ready."
            )

        query = (query or "").strip()
        if not query:
            return []

        query_without_year, query_year = self._extract_year_from_query(query)
        normalized_query = self._normalise_title(query_without_year)
        query_tokens = self._tokenise(normalized_query)

        if not normalized_query:
            return []

        candidate_ids: set[int] = set()

        for token in query_tokens:
            token_matches = self.token_index.get(token)
            if token_matches:
                candidate_ids.update(token_matches)

        # Fallback to all titles if token match is empty, so substring search still works.
        if not candidate_ids:
            candidate_ids = set(self.movies_by_id.keys())

        scored_results: list[tuple[float, dict[str, Any]]] = []

        for movie_id in candidate_ids:
            movie_record = self.movies_by_id[movie_id]
            score = self._score_movie(
                movie_record=movie_record,
                normalized_query=normalized_query,
                query_tokens=query_tokens,
                query_year=query_year
            )

            if score <= 0:
                continue

            scored_results.append((score, movie_record))

        scored_results.sort(key=lambda item: item[0], reverse=True)

        results = []
        for _, movie_record in scored_results[:limit]:
            results.append({
                "movieId": movie_record["movieId"],
                "title": movie_record["title"],
                "year": movie_record["year"],
                "genres": movie_record["genres"],
                "tmdbId": movie_record["tmdbId"]
            })

        return results

    def search_and_enrich(
        self,
        query: str,
        limit: int,
        api_key: str | None,
        tmdb_service
    ) -> list[dict[str, Any]]:
        """
        Search the local dataset catalog and enrich the results with TMDB metadata when available.
        Parameters:
            query (str):          search query entered by the user.
            limit (int):          maximum number of results to return.
            api_key (str | None): TMDB API key for the current user.
            tmdb_service:         TMDB service used to fetch/cache movie metadata.
        """
        results = self.search(query, limit)

        if not api_key:
            for result in results:
                result["tmdb"] = None
            return results

        for result in results:
            result["tmdb"] = tmdb_service.get_cached_or_fetch_movie_metadata(
                movie_id=result["movieId"],
                tmdb_id=result["tmdbId"],
                api_key=api_key
            )

        return results

    def movie_exists(self, movie_id: int) -> bool:
        """
        Check whether a movie exists in the loaded dataset.
        Parameters:
            movie_id (int): dataset movie id to validate.
        """
        return int(movie_id) in self.movies_by_id
    
    def get_movie(self, movie_id: int) -> dict[str, Any] | None:
        """
        Get a movie record from the loaded dataset.
        Parameters:
            movie_id (int): dataset movie id to fetch.
        """
        return self.movies_by_id.get(int(movie_id))