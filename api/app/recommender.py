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
        ratings: pd.DataFrame,
        min_user_ratings: int = 50,
        min_movie_ratings: int = 50,
        n_components: int = 64,
        n_neighbors: int = 20,
        random_state: int = 42
    ):
        if movies.empty or ratings.empty:
            raise ValueError("Movies and ratings dataframes must contain data.")

        self.movies = movies.copy()
        self.ratings = ratings.copy()

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

    def _prune_ratings(self) -> None:
        """
        Removes ratings from users with number of ratings below min_user_ratings and removes movies with number of ratings below
        min_movie_ratings. The higher the number, the more that is removed so the quicker training is, however accuracy will be
        reduced. Increasing this number does the opposite.
        """
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

        self._similar_movies_cache: Dict[Tuple[int, int], List[Tuple[int, float]]] = {}

    def initialise(self) -> None:
        """
        Prunes data, prepares the data, applies dimensionality reduction and lastly, trains the KNN algorithm.
        """
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
        self.movie_factors = self.svd.fit_transform(self.movie_user_matrix)

        self.knn = NearestNeighbors(
            metric="cosine",
            algorithm="auto",
            n_neighbors=self.n_neighbors
        )

        self.knn.fit(self.movie_factors)

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
        content_weight: float = 0.4
    ):
        self.collab_weight = collab_weight
        self.content_weight = content_weight

        self.collab = CollaborativeRecommendationSystem(movies, ratings)
        self.collab.initialise()

        self.content = ContentRecommendationSystem(movies, ratings)

        self.movies = movies
        self.ratings = ratings

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