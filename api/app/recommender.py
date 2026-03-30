import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.decomposition import TruncatedSVD
import warnings
from typing import List, Tuple, Dict
from app.models import User
from scipy.sparse import csr_matrix
from dataclasses import dataclass
from pathlib import Path
import joblib

@dataclass(frozen=True)
class UserRecommendationContext:
    """
    This is passed to the two recommendation systems to pass consistent data to both from the hybrid system.
    """
    ratings: list
    liked_movies: list
    rated_movie_ids: list[int]
    liked_movie_ids: list[int]
    seen_movie_ids: set[int]
    positive_rated_movie_ids: list[int]

class CollaborativeRecommendationSystem:
    """
    The collaborative recommendation system. Provides recommendations by getting user ratings >= 4.0 or liked
    movies using the KNN algorithm on those. Need at least 10 positive ratings or else switches to liked movies.
    Parameters:
        movies (Dataframe):  movies.csv converted to a dataframe to use.
        ratings (DataFrame): ratings.csv converted to a dataframe to use, must be from the same dataset as movies.csv and vice versa.
        min_user_ratings:    minimum ratings a user must have to be included in training, increase to reduce training times.
        min_movie_ratings:   minimum ratings a movie must have to be included in training, increase to reduce training times.
        n_components:        dimensionality of the data when reduced, decrease to reduce training times.
        random_state:        reproducibility seed of reducing algorithm. 
    """
    def __init__(
        self,
        movies: pd.DataFrame,
        ratings: pd.DataFrame | None = None,
        min_user_ratings: int = 50,
        min_movie_ratings: int = 50,
        n_components: int = 64,
        n_neighbors: int = 20,
        random_state: int = 42
    ):
        if movies.empty:
            raise ValueError("Movies dataframe must contain data.")

        self.movies = movies.copy()
        self.ratings = ratings.copy() if ratings is not None else None

        self.min_user_ratings = min_user_ratings
        self.min_movie_ratings = min_movie_ratings
        self.n_components = n_components
        self.n_neighbors = n_neighbors
        self.random_state = random_state

        # Sparse movie x user matrix
        self.movie_user_matrix = None

        # Reduced movie embeddings after SVD
        self.movie_factors = None

        # ID/index mappings for sparse matrix rows
        self.movie_id_to_idx: Dict[int, int] = {}
        self.idx_to_movie_id: Dict[int, int] = {}

        # Faster title lookups than filtering the dataframe every time
        self.movie_titles = dict(zip(self.movies["movieId"], self.movies["title"]))

        self.svd = None
        self.knn = None
        self._similar_movies_cache: Dict[Tuple[int, int], List[Tuple[int, float]]] = {}

        self.is_ready = False
        self.needs_manual_initialisation = False
        self.status_message: str | None = None

    def _set_status(
        self,
        is_ready: bool,
        needs_manual_initialisation: bool,
        status_message: str | None = None
    ) -> None:
        """
        Updates the current status of the collaborative recommender so the application can determine whether it is ready.
        Parameters:
            is_ready (bool):                    whether the recommender is currently ready to be used.
            needs_manual_initialisation (bool): whether the recommender requires manual initialisation before use.
            status_message (str | None):        message describing the current status.
        """
        self.is_ready = is_ready
        self.needs_manual_initialisation = needs_manual_initialisation
        self.status_message = status_message

    def mark_manual_initialisation_required(self, reason: str) -> None:
        """
        Marks the collaborative recommender as requiring manual initialisation.
        Parameters:
            reason (str): reason why the recommender could not be automatically initialised.
        """
        self._set_status(
            is_ready=False,
            needs_manual_initialisation=True,
            status_message=reason
        )

    def get_status(self) -> dict:
        """
        Gets the current status of the collaborative recommender for use by the application or web UI.
        """
        return {
            "is_ready": self.is_ready,
            "needs_manual_initialisation": self.needs_manual_initialisation,
            "status_message": self.status_message
        }

    def _prune_ratings(self) -> None:
        """
        Removes ratings from users with number of ratings below min_user_ratings and removes movies with number of ratings below
        min_movie_ratings. The higher the number, the more that is removed so the quicker training is, however accuracy will be
        reduced. Increasing this number does the opposite.
        """
        if self.ratings is None:
            raise ValueError("Ratings dataframe is required to train the model.")

        ratings = self.ratings.copy()

        # Normalise types early
        ratings["userId"] = ratings["userId"].astype("int32")
        ratings["movieId"] = ratings["movieId"].astype("int32")
        ratings["rating"] = ratings["rating"].astype("float32")

        # Keep only users with enough ratings
        user_counts = ratings["userId"].value_counts()
        active_users = user_counts[user_counts >= self.min_user_ratings].index
        ratings = ratings[ratings["userId"].isin(active_users)]

        # Keep only movies with enough ratings
        movie_counts = ratings["movieId"].value_counts()
        active_movies = movie_counts[movie_counts >= self.min_movie_ratings].index
        ratings = ratings[ratings["movieId"].isin(active_movies)]

        if ratings.empty:
            raise ValueError(
                "Pruning removed all ratings. Lower min_user_ratings/min_movie_ratings."
            )

        self.ratings = ratings.reset_index(drop=True)

    def __prepare(self) -> None:
        """
        Builds the movie id to index mappings, and applies conversions for perfomance.
        """
        if self.ratings is None:
            raise ValueError("Ratings dataframe is required to prepare the model.")

        movie_ids = self.ratings["movieId"].astype("category")
        user_ids = self.ratings["userId"].astype("category")

        # Map real movieId <-> matrix row index
        self.movie_id_to_idx = {
            int(movie_id): int(idx)
            for idx, movie_id in enumerate(movie_ids.cat.categories)
        }
        self.idx_to_movie_id = {
            int(idx): int(movie_id)
            for idx, movie_id in enumerate(movie_ids.cat.categories)
        }

        row = movie_ids.cat.codes.to_numpy()
        col = user_ids.cat.codes.to_numpy()
        data = self.ratings["rating"].astype("float32").to_numpy()

        self.movie_user_matrix = csr_matrix((data, (row, col)))
        self._similar_movies_cache = {}

    def initialise(self) -> None:
        """
        Prunes data, prepares the data, applies dimensionality reduction and lastly, trains the KNN algorithm.
        """
        if self.ratings is None or self.ratings.empty:
            raise ValueError("Ratings dataframe is required to train the model.")

        self._prune_ratings()
        self.__prepare()

        # Guard against impossible component size
        max_components = min(self.movie_user_matrix.shape) - 1
        if max_components < 2:
            raise ValueError("Not enough data remaining after pruning to fit SVD.")

        n_components = min(self.n_components, max_components)

        self.svd = TruncatedSVD(
            n_components=n_components,
            random_state=self.random_state
        )

        # Dense latent movie vectors: shape = (n_movies, n_components)
        self.movie_factors = self.svd.fit_transform(self.movie_user_matrix).astype(np.float32)

        self.knn = NearestNeighbors(
            metric="cosine",
            algorithm="auto",
            n_neighbors=self.n_neighbors
        )

        self.knn.fit(self.movie_factors)

        self._set_status(
            is_ready=True,
            needs_manual_initialisation=False,
            status_message="Collaborative recommender initialised successfully."
        )

    def _build_model_metadata(self, dataset_id: str | None = None) -> dict:
        """
        Builds the metadata used to determine whether a saved model matches the current recommender configuration.
        Parameters:
            dataset_id (str | None): identifier for the dataset being used, e.g. zip filename or dataset name.
        """
        return {
            "dataset_id": dataset_id,
            "min_user_ratings": self.min_user_ratings,
            "min_movie_ratings": self.min_movie_ratings,
            "n_components": self.n_components,
            "n_neighbors": self.n_neighbors,
            "random_state": self.random_state,
        }
    
    def model_is_compatible(self, model_path: str, dataset_id: str | None = None) -> bool:
        """
        Checks whether a saved collaborative model matches the current recommender configuration.
        Parameters:
            model_path (str):        local path of the saved model to validate.
            dataset_id (str | None): identifier for the dataset expected by the current application run.
        """
        path = Path(model_path)
        if not path.exists():
            return False

        model_data = joblib.load(path)
        saved_metadata = model_data.get("metadata")

        if saved_metadata is None:
            return False

        expected_metadata = self._build_model_metadata(dataset_id)
        return saved_metadata == expected_metadata
    
    def get_model_mismatch_reason(self, model_path: str, dataset_id: str | None = None) -> str | None:
        """
        Returns the reason a saved model does not match the current recommender configuration.
        Parameters:
            model_path (str):        local path of the saved model to validate.
            dataset_id (str | None): identifier for the dataset expected by the current application run.
        """
        path = Path(model_path)
        if not path.exists():
            return "Model file does not exist."

        model_data = joblib.load(path)
        saved_metadata = model_data.get("metadata")
        if saved_metadata is None:
            return "Saved model metadata is missing."

        expected_metadata = self._build_model_metadata(dataset_id)

        for key, expected_value in expected_metadata.items():
            if saved_metadata.get(key) != expected_value:
                return f"Saved model metadata mismatch for '{key}'."

        return None

    def save_model(self, model_path: str, dataset_id: str | None = None) -> None:
        """
        Saves the trained collaborative model locally so it can be loaded later instead of retraining.
        Parameters:
            model_path (str):        local path to save the trained model to.
            dataset_id (str | None): identifier for the dataset used to train the model.
        """
        if self.movie_factors is None or self.knn is None:
            raise ValueError("Model must be trained before it can be saved.")

        model_data = {
            "movie_factors": self.movie_factors,
            "movie_id_to_idx": self.movie_id_to_idx,
            "idx_to_movie_id": self.idx_to_movie_id,
            "n_neighbors": self.n_neighbors,
            "min_user_ratings": self.min_user_ratings,
            "min_movie_ratings": self.min_movie_ratings,
            "n_components": self.n_components,
            "random_state": self.random_state,
            "knn": self.knn,
            "metadata": self._build_model_metadata(dataset_id)
        }

        path = Path(model_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Use temp path whilst saving creating the model so that if it fails, a partially saved model isn't present,
        # which would cause issues as the system would try to load it.
        temp_path = path.with_suffix(path.suffix + ".tmp")
        joblib.dump(model_data, temp_path)
        temp_path.replace(path)

    def load_model(self, model_path: str) -> None:
        """
        Loads a previously saved collaborative model from local storage.
        Parameters:
            model_path (str): local path to load the trained model from.
        """
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Collaborative model not found at {model_path}")

        model_data = joblib.load(path)

        self.movie_factors = model_data["movie_factors"]
        self.movie_id_to_idx = model_data["movie_id_to_idx"]
        self.idx_to_movie_id = model_data["idx_to_movie_id"]
        self.knn = model_data["knn"]

        self.n_neighbors = model_data.get("n_neighbors", self.n_neighbors)
        self.min_user_ratings = model_data.get("min_user_ratings", self.min_user_ratings)
        self.min_movie_ratings = model_data.get("min_movie_ratings", self.min_movie_ratings)
        self.n_components = model_data.get("n_components", self.n_components)
        self.random_state = model_data.get("random_state", self.random_state)

        self.movie_user_matrix = None
        self.svd = None
        self._similar_movies_cache = {}

        self._set_status(
            is_ready=True,
            needs_manual_initialisation=False,
            status_message="Collaborative recommender model loaded successfully."
        )

    @staticmethod
    def model_exists(model_path: str) -> bool:
        """
        Checks whether a saved collaborative model exists at the given local path.
        Parameters:
            model_path (str): local path to check for a saved model.
        """
        return Path(model_path).exists()

    def initialise_from_storage(
        self,
        model_path: str,
        dataset_id: str | None = None,
        persist_model: bool = True,
        auto_train_if_missing: bool = True,
        save_after_train: bool = True
    ) -> None:
        """
        Loads a saved collaborative model when available, otherwise optionally trains and saves a new one.
        Parameters:
            model_path (str):             local path to load/save the trained model.
            dataset_id (str | None):      identifier for the dataset expected by the current application run.
            persist_model (bool):         whether local model persistence should be used.
            auto_train_if_missing (bool): whether the model should be trained if no saved model is found or is incompatible.
            save_after_train (bool):      whether a newly trained model should be saved locally.
        """
        if persist_model and self.model_exists(model_path):
            if self.model_is_compatible(model_path, dataset_id):
                self.load_model(model_path)
                return
            else:
                warnings.warn(self.get_model_mismatch_reason(model_path, dataset_id))

            if not auto_train_if_missing:
                raise ValueError(
                    f"Collaborative model at {model_path} does not match the current dataset/configuration."
                )

        elif not auto_train_if_missing:
            raise FileNotFoundError(f"Collaborative model not found at {model_path}")

        self.initialise()

        if persist_model and save_after_train:
            self.save_model(model_path, dataset_id=dataset_id)

    def get_similar_movies(self, movie_id: int, n: int = 10) -> List[Tuple[int, float]]:
        """
        Gets similar movies to the movie that is supplied via the KNN algorithm.
        Parameters:
            movies_id (int): the movie id of th movie to get similar movies for.
            n (int):         the amount of similar movies to find.
        """
        if self.movie_factors is None or self.knn is None:
            warnings.warn("Model not prepared. Please call initialise() first.")
            return []

        movie_id = int(movie_id)
        cache_key = (movie_id, int(n))
        cached = self._similar_movies_cache.get(cache_key)
        if cached is not None:
            return cached

        movie_index = self.movie_id_to_idx.get(movie_id)
        if movie_index is None:
            warnings.warn(f"Warning - movie with id {movie_id} not found in the matrix.")
            return []

        n = min(n, len(self.idx_to_movie_id))

        try:
            movie_vector = self.movie_factors[movie_index].reshape(1, -1)
            distances, indices = self.knn.kneighbors(movie_vector, n_neighbors=n)
        except Exception as e:
            raise RuntimeError(f"Error in k-neighbors search: {str(e)}") from e

        similar_movies = []
        for i in range(1, len(indices[0])):
            similar_index = int(indices[0][i])
            similar_movie_id = self.idx_to_movie_id[similar_index]
            similarity = float(1 - distances[0][i])
            similar_movies.append((similar_movie_id, similarity))

        self._similar_movies_cache[cache_key] = similar_movies
        return similar_movies

    def recommend_from_context(
        self,
        context: UserRecommendationContext,
        top_n: int = 50
    ) -> List[Dict[str, float]]:
        """
        Creates recommendations for the user.
        Parameters:
            context (UserRecommendationContext): Context containing ratings etc. generated by hybrid system.
            top_n (int):                         Amount of recommendations to generate.
        """
        if len(context.positive_rated_movie_ids) < 10:
            if len(context.liked_movie_ids) == 0:
                warnings.warn("User didn't have any ratings or liked movies.")
                return []
            seed_movie_ids = context.liked_movie_ids
        else:
            seed_movie_ids = context.positive_rated_movie_ids

        seed_movie_ids = [
            movie_id
            for movie_id in seed_movie_ids
            if movie_id in self.movie_id_to_idx
        ]

        if not seed_movie_ids:
            return []

        recommendations: List[Tuple[int, float]] = []
        for movie_id in seed_movie_ids:
            recommendations.extend(self.get_similar_movies(movie_id, n=top_n))

        movie_scores: Dict[int, float] = {}
        for movie_id, score in recommendations:
            if movie_id in context.seen_movie_ids:
                continue
            movie_scores[movie_id] = movie_scores.get(movie_id, 0.0) + float(score)

        sorted_movies = sorted(
            movie_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        return [
            {
                "movieId": int(movie_id),
                "similarity": float(score)
            }
            for movie_id, score in sorted_movies
        ]

    
class ContentRecommendationSystem:
    """
    The content recommendation system. Finds similarities based off of genre using the multilabel binarizer.
    Parameters:
        movies (Dataframe):  movies.csv converted to a dataframe to use.
        ratings (DataFrame): ratings.csv converted to a dataframe to use, must be from the same dataset as movies.csv and vice versa.
    """
    def __init__(self, movies: pd.DataFrame, ratings: pd.DataFrame):
        if movies.empty or ratings.empty:
            raise ValueError("Movies and ratings dataframes must contain data.")
        
        self.movies = movies.copy()
        self.ratings = ratings

        self.movies["movieId"] = self.movies["movieId"].astype("int32")
        # Split genres into a list
        self.movies["genres"] = self.movies["genres"].fillna("").str.split("|")
        self.movies["genres"] = [
            [] if genres == [""] else genres
            for genres in self.movies["genres"]
        ]

        self.movie_id_to_idx = {
            int(movie_id): int(idx)
            for idx, movie_id in enumerate(self.movies["movieId"].astype("int32"))
        }
        self.mlb = MultiLabelBinarizer()
        self.movie_ids = self.movies["movieId"].to_numpy(dtype=np.int32)

        self.genre_matrix = self.mlb.fit_transform(self.movies["genres"]).astype(np.float32)

        genre_counts = self.genre_matrix.sum(axis=0).astype(np.float32)
        idf = np.log((1.0 + self.genre_matrix.shape[0]) / (1.0 + genre_counts)) + 1.0
        self.genre_matrix *= idf

        movie_norms = np.linalg.norm(self.genre_matrix, axis=1, keepdims=True)
        movie_norms[movie_norms == 0] = 1.0
        self.genre_matrix = self.genre_matrix / movie_norms

    def create_user_profile(self, context: UserRecommendationContext) -> np.ndarray:
        """
        Creates profile of user based on their ratings, uses movie rating to provide weightings to each genre.
        Parameters:
            context (UserRecommendationContext): Context containing ratings etc. generated by hybrid system.
        """
        if not context.ratings:
            return np.zeros(self.genre_matrix.shape[1], dtype=np.float32)

        movie_indices = []
        weights = []

        for rating in context.ratings:
            idx = self.movie_id_to_idx.get(int(rating.movie_id))
            if idx is not None:
                movie_indices.append(idx)
                weights.append(float(rating.rating))

        if not movie_indices:
            return np.zeros(self.genre_matrix.shape[1], dtype=np.float32)

        weights = np.asarray(weights, dtype=np.float32)
        movie_vectors = self.genre_matrix[movie_indices]

        user_vector = (movie_vectors * weights[:, None]).sum(axis=0)

        total_ratings = weights.sum()
        if total_ratings == 0:
            return np.zeros(self.genre_matrix.shape[1], dtype=np.float32)

        return user_vector / total_ratings

    def recommend_from_context(
        self,
        context: UserRecommendationContext,
        top_n: int = 50
    ) -> List[Dict[str, float]]:
        """
        Creates recommendations for the user.
        Parameters:
            context (UserRecommendationContext): Context containing ratings etc. generated by hybrid system.
            top_n (int):                         Amount of recommendations to generate.
        """
        user_profile = self.create_user_profile(context)
        norm = np.linalg.norm(user_profile)
        if norm == 0:
            return []

        user_profile = user_profile / norm
        similarities = self.genre_matrix @ user_profile

        candidate_count = min(max(top_n * 5, top_n), len(similarities))
        candidate_indices = np.argpartition(similarities, -candidate_count)[-candidate_count:]
        candidate_indices = candidate_indices[np.argsort(similarities[candidate_indices])[::-1]]

        results = []
        for idx in candidate_indices:
            movie_id = int(self.movie_ids[idx])
            if movie_id in context.seen_movie_ids:
                continue

            results.append({
                "movieId": movie_id,
                "similarity": float(similarities[idx])
            })

            if len(results) == top_n:
                break

        return results

class HybridRecommendationSystem:
    """
    Hybrid recommendation system, acts an interface for the recommendation system, should be used rather than directly interacting with the indivdual
    recommendation systems.
    Parameters:
        movies (Dataframe):   movies.csv converted to a dataframe to use.
        ratings (DataFrame):  ratings.csv converted to a dataframe to use, must be from the same dataset as movies.csv and vice versa.
        collab_weight (int):  weighting to provide to the collaborative system recommendations, by defualt, collaborative recommendations are favoured.
        content_weight (int): weighting to provide to the content system recommendations.
    """
    def __init__(
        self,
        movies: pd.DataFrame,
        ratings: pd.DataFrame,
        collab_weight: float = 0.6,
        content_weight: float = 0.4,
        collab_model_path: str | None = None,
        collab_dataset_id: str | None = None,
        persist_collab_model: bool = False,
        auto_train_if_missing: bool = True,
        save_model_after_train: bool = True,
        allow_uninitialised: bool = False
    ):
        self.collab_weight = collab_weight
        self.content_weight = content_weight
        self.collab_model_path = collab_model_path
        self.collab_dataset_id = collab_dataset_id
        self.persist_collab_model = persist_collab_model
        self.auto_train_if_missing = auto_train_if_missing
        self.save_model_after_train = save_model_after_train

        self.is_ready = False
        self.needs_manual_initialisation = False
        self.status_message: str | None = None

        self.collab = CollaborativeRecommendationSystem(movies, ratings)
        self.content = ContentRecommendationSystem(movies, ratings)

        self.movies = movies
        self.ratings = ratings

        try:
            if collab_model_path is None:
                self.collab.initialise()
            else:
                self.collab.initialise_from_storage(
                    model_path=collab_model_path,
                    dataset_id=collab_dataset_id,
                    persist_model=persist_collab_model,
                    auto_train_if_missing=auto_train_if_missing,
                    save_after_train=save_model_after_train
                )
        except (FileNotFoundError, ValueError) as e:
            if not allow_uninitialised:
                raise

            self.collab.mark_manual_initialisation_required(str(e))

        self._sync_status_from_collab()
    
    def _sync_status_from_collab(self) -> None:
        """
        Synchronises the hybrid recommender status with the collaborative recommender status.
        """
        self.is_ready = self.collab.is_ready
        self.needs_manual_initialisation = self.collab.needs_manual_initialisation
        self.status_message = self.collab.status_message

    def get_status(self) -> dict:
        """
        Gets the current status of the hybrid recommender for use by the application or web UI.
        """
        return {
            "is_ready": self.is_ready,
            "needs_manual_initialisation": self.needs_manual_initialisation,
            "status_message": self.status_message
        }

    def manual_initialise(self) -> None:
        """
        Manually trains the collaborative part of the hybrid recommender and saves the model when configured.
        Used when automatic initialisation was deferred at application startup.
        """
        self.collab.initialise()

        if (
            self.collab_model_path is not None and
            self.persist_collab_model and
            self.save_model_after_train
        ):
            self.collab.save_model(
                model_path=self.collab_model_path,
                dataset_id=self.collab_dataset_id
            )

        self._sync_status_from_collab()

    def _build_user_context(self, user: User) -> UserRecommendationContext:
        """
        Creates the shared context that both recommendation systems use to get data, e.g. user ratings.
        Parameters:
            user (User): user to generate recommendations for.
        """
        ratings = user.get_user_ratings()
        liked_movies = user.get_liked_movies()

        rated_movie_ids = [int(r.movie_id) for r in ratings]
        liked_movie_ids = [int(m.movie_id) for m in liked_movies]
        seen_movie_ids = set(rated_movie_ids)
        seen_movie_ids.update(liked_movie_ids)

        positive_rated_movie_ids = [
            int(r.movie_id)
            for r in ratings
            if float(r.rating) >= 4.0
        ]

        return UserRecommendationContext(
            ratings=ratings,
            liked_movies=liked_movies,
            rated_movie_ids=rated_movie_ids,
            liked_movie_ids=liked_movie_ids,
            seen_movie_ids=seen_movie_ids,
            positive_rated_movie_ids=positive_rated_movie_ids,
        )

    @staticmethod
    def _normalise_scores(scores: Dict[int, float]) -> Dict[int, float]:
        if not scores:
            return {}

        values = np.asarray(list(scores.values()), dtype=np.float32)
        min_v = float(values.min())
        max_v = float(values.max())

        if max_v == min_v:
            return {movie_id: 1.0 for movie_id in scores}

        return {
            movie_id: (float(score) - min_v) / (max_v - min_v)
            for movie_id, score in scores.items()
        }

    def recommend(
        self,
        user: User,
        top_n: int = 10,
        candidate_n: int = 50,
        cache_result: bool = True
    ) -> List[Dict[str, float]]:
        """
        Generate hybrid movie recommendations for a user.
        Parameters:
            user (User):          user to generate recommendations for.
            top_n (int):          maximum number of recommendations to return.
            candidate_n (int):    number of recommendations each system should return.
            cache_results (bool): whether to cache the recommendations as a set in the database.
        """
                
        if not self.is_ready:
            raise RuntimeError(
                self.status_message or "Recommender is not ready and requires manual initialisation."
            )
        
        context = self._build_user_context(user)

        collab_recs = self.collab.recommend_from_context(context, top_n=candidate_n)
        content_recs = self.content.recommend_from_context(context, top_n=candidate_n)

        collab_scores = {
            int(rec["movieId"]): float(rec["similarity"])
            for rec in collab_recs
        }
        content_scores = {
            int(rec["movieId"]): float(rec["similarity"])
            for rec in content_recs
        }

        collab_scores = self._normalise_scores(collab_scores)
        content_scores = self._normalise_scores(content_scores)

        hybrid_scores: Dict[int, float] = {}
        all_movie_ids = set(collab_scores.keys()) | set(content_scores.keys())

        for movie_id in all_movie_ids:
            hybrid_scores[movie_id] = (
                self.collab_weight * collab_scores.get(movie_id, 0.0) +
                self.content_weight * content_scores.get(movie_id, 0.0)
            )

        sorted_movies = sorted(
            hybrid_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        results = [
            {
                "movieId": int(movie_id),
                "score": float(score)
            }
            for movie_id, score in sorted_movies
        ]

        if cache_result:
            user.cache_recommendation_set(results)

        return results