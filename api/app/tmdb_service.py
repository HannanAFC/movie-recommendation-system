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
from datetime import timedelta

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

    def _normalise_tmdb_payload(self, moviePayload: dict[str, Any], creditsPayload: dict[str, Any] | None) -> dict[str, Any]:
        """
        Normalise a TMDB movie payload into the shape used by the application cache.
        Parameters:
            moviePayload (dict[str, Any]):   raw TMDB movie payload.
            creditsPayload (dict[str, Any]): raw TMDB movie credits payload
        """
        poster_url = f"{self._get_base_image_url()}{moviePayload.get("poster_path")}"
        backdrop_url = f"{self._get_base_image_url()}{moviePayload.get("backdrop_path")}"

        cast = creditsPayload.get("cast", [])
        normalised_cast = [
            {
                "id": member.get("id"),
                "name": member.get("name"),
                "character": member.get("character"),
                "profile_path": member.get("profile_path"),
                "profile_url": f"{self._get_base_image_url()}{member.get("profile_path")}",
                "order": member.get("order")
            }
            for member in cast[:10]
        ]

        return {
            "tmdb_id": moviePayload.get("id"),
            "title": moviePayload.get("title"),
            "overview": moviePayload.get("overview"),
            "poster_path": moviePayload.get("poster_path"),
            "poster_url": poster_url if moviePayload.get("poster_path") else None,
            "backdrop_path": moviePayload.get("backdrop_path"),
            "backdrop_url": backdrop_url if moviePayload.get("backdrop_path") else None,
            "release_date": moviePayload.get("release_date"),
            "vote_average": moviePayload.get("vote_average"),
            "cast": json.dumps(normalised_cast) if creditsPayload else None,
            "raw_payload": json.dumps(moviePayload)
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

    def fetch_movie_details(self, tmdb_id: str, api_key: str, append_cast: bool) -> dict[str, Any] | None:
        """
        Fetch movie metadata from TMDB for a given TMDB movie id.
        Parameters:
            tmdb_id (str): TMDB movie id to fetch metadata for.
            api_key (str): TMDB API key for the current user.
        """
        if not tmdb_id or not api_key:
            return None

        try:
            movieDetails = requests.get(
                f"{self._get_base_url()}/movie/{tmdb_id}",
                headers=self._build_headers(api_key),
                params={"language": "en-GB"},
                timeout=self.timeout
            )
            movieDetails.raise_for_status()
            movieDetailsPayload = movieDetails.json()

            if append_cast:
                creditsDetails = requests.get(
                    f"{self._get_base_url()}/movie/{tmdb_id}/credits",
                    headers=self._build_headers(api_key),
                    params={"language": "en-GB"},
                    timeout=self.timeout
                )
                creditsDetails.raise_for_status()
                creditsDetailsPayload = creditsDetails.json()
                return self._normalise_tmdb_payload(movieDetailsPayload, creditsDetailsPayload)
            
            return self._normalise_tmdb_payload(movieDetailsPayload, None)
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
        cached.cast = payload.get("cast")
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
            "vote_average": cached.vote_average,
            "cast": json.loads(cached.cast) if cached.cast else [],
            "runtime": json.loads(cached.raw_payload)["runtime"]
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
            "vote_average": cached.vote_average,
            "cast": json.loads(cached.cast) if cached.cast else [],
            "runtime": json.loads(cached.raw_payload)["runtime"]
        }
    
    def clear_cache(self) -> int:
        """
        Clear all cached TMDB movie metadata.
        """
        result = db.session.execute(
            sa.delete(CachedMovieMetadata)
        )
        db.session.commit()
        return result.rowcount or 0


    def clear_cached_movie_metadata(self, movie_id: int) -> int:
        """
        Clear cached TMDB movie metadata for a dataset movie id.
        Parameters:
            movie_id (int): dataset movie id whose cached metadata should be removed.
        """
        result = db.session.execute(
            sa.delete(CachedMovieMetadata).where(
                CachedMovieMetadata.movie_id == int(movie_id)
            )
        )
        db.session.commit()
        return result.rowcount or 0
    
    from datetime import datetime, timedelta, timezone

    def clear_stale_cache(self, max_age_hours: int = 168) -> int:
        """
        Clear cached TMDB movie metadata older than the given age.
        Parameters:
            max_age_hours (int): maximum cache age in hours.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

        result = db.session.execute(
            sa.delete(CachedMovieMetadata).where(
                CachedMovieMetadata.fetched_at < cutoff
            )
        )
        db.session.commit()
        return result.rowcount or 0

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

        payload = self.fetch_movie_details(tmdb_id, api_key, True)
        if payload is None:
            return None

        return self.cache_movie_metadata(movie_id, tmdb_id, payload)