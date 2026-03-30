# I put this in its own file because it feels important...

import json
from datetime import datetime, timezone
from typing import Any
from flask import Flask
import requests
import sqlalchemy as sa
from flask import current_app
from app.extensions import db
from app.models import CachedMovieMetadata

class TMDBService:
    """
    Helper service for validating TMDB API keys and fetching TMDB movie metadata.
    Parameters:
        timemout (int): amount of time before a request timesout.
    """

    def init_app(self, app: Flask) -> None:
        """
        Initialise the TMDB service with the Flask application.
        Parameters:
            app (Flask): the Flask app.
        """
        self.app = app
        self.timeout = 10

    def _get_base_url(self) -> str:
        """
        Get the configured TMDB API base URL.
        """
        return str(current_app.config["TMDB_API_BASE_URL"]).rstrip("/")
    
    def _get_base_image_url(self) -> str:
        """
        Get the configured TMDB image API base URL.
        """
        return str(current_app.config["TMDB_API_IMAGE_BASE_URL"]).rstrip("/")

    def _build_headers(self, api_key: str) -> dict[str, str]:
        """
        Build the headers required for TMDB API requests.
        Parameters:
            api_key (str): TMDB API key for the current user.
        """
        return {
            "accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def _normalise_tmdb_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Normalise a TMDB movie payload into the shape used by the application cache.
        Parameters:
            payload (dict[str, Any]): raw TMDB movie payload.
        """
        poster_url = f"{self._get_base_image_url()}{payload.get("backdrop_path")}"
        backdrop_url = f"{self._get_base_image_url()}{payload.get("backdrop_path")}"

        return {
            "tmdb_id": payload.get("id"),
            "title": payload.get("title"),
            "overview": payload.get("overview"),
            "poster_path": payload.get("backdrop_path"),
            "poster_url": poster_url if {payload.get("backdrop_path")} else None,
            "backdrop_path": payload.get("backdrop_path"),
            "backdrop_url": backdrop_url if {payload.get("backdrop_path")} else None,
            "release_date": payload.get("release_date"),
            "vote_average": payload.get("vote_average"),
            "raw_payload": json.dumps(payload)
        }

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate a TMDB API key by calling the TMDB authentication endpoint.
        Parameters:
            api_key (str): TMDB API key to validate.
        """
        if not api_key:
            return False

        try:
            response = requests.get(
                f"{self._get_base_url()}/authentication",
                headers=self._build_headers(api_key),
                timeout=self.timeout
            )
            response.raise_for_status()

            payload = response.json()
            return bool(payload.get("success", False))
        except (requests.RequestException, ValueError):
            return False

    def fetch_movie_details(self, tmdb_id: str, api_key: str) -> dict[str, Any] | None:
        """
        Fetch movie metadata from TMDB for a given TMDB movie id.
        Parameters:
            tmdb_id (str): TMDB movie id to fetch metadata for.
            api_key (str): TMDB API key for the current user.
        """
        if not tmdb_id or not api_key:
            return None

        try:
            response = requests.get(
                f"{self._get_base_url()}/movie/{tmdb_id}",
                headers=self._build_headers(api_key),
                params={"language": "en-GB"},
                timeout=self.timeout
            )
            response.raise_for_status()
            payload = response.json()
            print(payload)
            return self._normalise_tmdb_payload(payload)
        except (requests.RequestException, ValueError):
            return None

    def get_cached_movie_metadata(self, movie_id: int) -> CachedMovieMetadata | None:
        """
        Get cached TMDB metadata for a dataset movie id.
        Parameters:
            movie_id (int): dataset movie id.
        """
        return db.session.scalar(
            sa.select(CachedMovieMetadata).where(
                CachedMovieMetadata.movie_id == int(movie_id)
            )
        )

    def cache_movie_metadata(
        self,
        movie_id: int,
        tmdb_id: int | None,
        payload: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Store TMDB movie metadata in the local database cache.
        Parameters:
            movie_id (int):           dataset movie id.
            tmdb_id (int | None):     TMDB movie id associated with the dataset movie.
            payload (dict[str, Any]): normalised TMDB movie payload.
        """
        cached = self.get_cached_movie_metadata(movie_id)

        if cached is None:
            cached = CachedMovieMetadata(movie_id=int(movie_id))
            db.session.add(cached)

        cached.tmdb_id = int(tmdb_id) if tmdb_id is not None else None
        cached.title = payload.get("title")
        cached.overview = payload.get("overview")
        cached.poster_path = payload.get("poster_path")
        cached.backdrop_path = payload.get("backdrop_path")
        cached.release_date = payload.get("release_date")
        cached.vote_average = payload.get("vote_average")
        cached.raw_payload = payload.get("raw_payload")
        cached.fetched_at = datetime.now(timezone.utc)

        db.session.commit()

        return {
            "tmdb_id": cached.tmdb_id,
            "title": cached.title,
            "overview": cached.overview,
            "poster_path": cached.poster_path,
            "poster_url": f"{self._get_base_image_url()}{cached.poster_path}" if cached.poster_path else None,
            "backdrop_path": cached.backdrop_path,
            "backdrop_url": f"{self._get_base_image_url()}{cached.backdrop_path}" if cached.backdrop_path else None,
            "release_date": cached.release_date,
            "vote_average": cached.vote_average
        }

    def serialise_cached_movie_metadata(
        self,
        cached: CachedMovieMetadata
    ) -> dict[str, Any]:
        """
        Convert a cached movie metadata row into the shape returned by the application.
        Parameters:
            cached (CachedMovieMetadata): cached metadata row to serialise.
        """
        return {
            "tmdb_id": cached.tmdb_id,
            "title": cached.title,
            "overview": cached.overview,
            "poster_path": cached.poster_path,
            "poster_url": f"{self._get_base_image_url()}{cached.poster_path}" if cached.poster_path else None,
            "backdrop_path": cached.backdrop_path,
            "backdrop_url": f"{self._get_base_image_url()}{cached.backdrop_path}" if cached.backdrop_path else None,
            "release_date": cached.release_date,
            "vote_average": cached.vote_average
        }

    def get_cached_or_fetch_movie_metadata(
        self,
        movie_id: int,
        tmdb_id: str | None,
        api_key: str
    ) -> dict[str, Any] | None:
        """
        Get cached TMDB metadata when available, otherwise fetch it from TMDB and cache it.
        Parameters:
            movie_id (int):       dataset movie id.
            tmdb_id (int | None): TMDB movie id associated with the dataset movie.
            api_key (str):        TMDB API key for the current user.
        """
        if tmdb_id is None:
            return None

        cached = self.get_cached_movie_metadata(movie_id)
        if cached is not None:
            return self.serialise_cached_movie_metadata(cached)

        payload = self.fetch_movie_details(tmdb_id, api_key)
        if payload is None:
            return None

        return self.cache_movie_metadata(movie_id, tmdb_id, payload)