import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer
import warnings
from typing import List, Tuple, Dict, Any
from app.models import User, MovieRating, CachedRecommendation
from app import db

class CollaborativeRecommendationSystem():

    def __init__(self, movies: pd.DataFrame, ratings: pd.DataFrame):
        if movies.empty or ratings.empty:
            raise ValueError("Movies and ratings dataframes must contain data.")
        self.movies = movies
        self.ratings = ratings
        self.movie_user_matrix = None
        self.knn = NearestNeighbors(
            metric="cosine",
            algorithm="brute"
        )

    def __prepare(self):
        """Prepare the movie-user matrix for collaborative filtering."""
        self.movie_user_matrix = self.ratings.pivot_table(
            index="movieId",
            columns="userId",
            values="rating",
            fill_value=0
        )

        self.movie_user_matrix = self.movie_user_matrix.fillna(0)

    def get_similar_movies(self, movie_id: int, n: int = 10) -> List[Tuple[int, float]]:
        """
        Get similar movies for a given movie ID using collaborative filtering.
        Parameters:
            movie_id (int): The ID of the movie to find similar movies for.
            n (int): The maximum number of similar movies to return.

        """
        # Check if the movie user matrix is already prepared
        if type(self.movie_user_matrix) == pd.DataFrame:
            # Find the given movie in the matrix
            try:
                movie_index = self.movie_user_matrix.index.get_loc(movie_id)
            except KeyError:
                warnings.warn(f"Warning - movie with id {movie_id} not found in the matrix.")
                return []

            # Get the indices of the n nearest neighbors
            try:
                distances, indices = self.knn.kneighbors(
                    self.movie_user_matrix.iloc[movie_index].to_numpy().reshape(1, -1),
                    n_neighbors=n
                )
            except Exception as e:
                raise RuntimeError(f"Error in k-neighbors search: {str(e)}") from e

            # Calculate similarities (1 - cosine distance)
            similar_movies = []
            for i in range(1, len(indices[0])):
                similar_movie_id = self.movie_user_matrix.index[indices[0][i]]
                similarity = 1 - distances[0][i]
                similar_movies.append((similar_movie_id, similarity))

            return similar_movies

        else:
            warnings.warn("Movie-user matrix not prepared. Please call initialise() first.")
            return []

    def initialise(self) -> None:
        """Prepare the movie-user matrix and fit the k-NN model."""
        self.__prepare()
        try:
            self.knn.fit(self.movie_user_matrix)
        except Exception as e:
            raise RuntimeError(f"Error during model fitting: {str(e)}") from e

    def recommend(self, user: User) -> List[Dict[str, Any]]:
        """
        Generate movie recommendations for a user based on collaborative filtering.
        Parameters:
            user (User): The user to make recommendations for.
        """
        # Get user's ratings (only those >=4.0) or if no ratings - get liked movies
        user_ratings = [rating for rating in user.get_user_ratings() if float(rating.rating) >= 4.0]
        movie_ids = []
        if len(user_ratings) < 10:
            liked_movies = user.get_liked_movies()
            if len(liked_movies) == 0:
                warnings.warn("User didn't have any ratings or liked movies.")
                return []
            else:
                movie_ids = [liked_movie.movie_id for liked_movie in liked_movies]
        else:
            movie_ids = [rating.movie_id for rating in user_ratings]
        
        # Get similar movies for each rated/liked movie
        recommendations = []
        for movie_id in movie_ids:
            similar_movies = self.get_similar_movies(int(movie_id))
            recommendations.extend(similar_movies)

        # Remove duplicates and sort by similarity
        movie_scores = {}
        for movie_id, score in recommendations:
            if movie_id not in movie_scores:
                movie_scores[movie_id] = score
            else:
                movie_scores[movie_id] += score

        # Sort by score and return top 10
        sorted_movies = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)[:10]
        results = []
        for movie_id, score in sorted_movies:
            # Get the movie title from the movies dataframe
            movie_title = self.movies[self.movies.movieId == movie_id].title.values[0]
            results.append({
                "movieId": int(movie_id),
                "title": str(movie_title),
                "similarity": float(score)
            })

        return results

    
class ContentRecommendationSystem:

    def __init__(self, movies: pd.DataFrame, ratings: pd.DataFrame):
        if movies.empty or ratings.empty:
            raise ValueError("Movies and ratings dataframes must contain data.")
        self.movies = movies
        self.ratings = ratings
        # Split genres into a list
        try:
            self.movies["genres"] = movies["genres"].apply(lambda x: x.split("|"))
        except Exception as e:
            raise ValueError("Error splitting genres: {str(e)}") from e
        self.mlb = MultiLabelBinarizer()
        self.genre_matrix = self.mlb.fit_transform(self.movies["genres"])
        self.genre_matrix = self.genre_matrix / self.genre_matrix.sum(axis=0)

    def create_user_profile(self, user: User) -> np.ndarray:
        """
        Create a user profile vector based on their ratings and the genre matrix.
        Parameters:
            user (User): The user to create the profile for.
        """
        def calculate_vector(movie: MovieRating) -> np.ndarray:
            """
            Calculate the vector for a given movie using its rating.
            Parameters:
                movie (MovieRating): The movie to calculate the vector for.
            """
            try:
                movie_index = np.where(self.movies["movieId"] == movie.movie_id)[0][0]
            except IndexError:
                return np.zeros(self.genre_matrix.shape[1])
            return self.genre_matrix[movie_index] * float(movie.rating)

        def update_vector(user_vector: np.ndarray, movie: MovieRating) -> np.ndarray:
            """
            Update the user vector by adding the vector for a given movie.
            Parameters:
               user_vector (np.ndarray): The user vector to update.
               movie (MovieRating): The movie to calculate the vector for.
            """
            return user_vector + calculate_vector(movie)

        # Get users ratings
        user_ratings = user.get_user_ratings()
        if not user_ratings:
            return np.zeros(self.genre_matrix.shape[1])

        # Create a vector for the current user using the genre matrix
        user_vector = np.zeros(self.genre_matrix.shape[1])
        for movie in user_ratings:
            user_vector = update_vector(user_vector, movie)

        # Normalize by the sum of ratings
        total_ratings = sum(float(movie.rating) for movie in user_ratings)
        if total_ratings == 0:
            return np.zeros(self.genre_matrix.shape[1])
        return user_vector / total_ratings

    def recommend(self, user: User) -> List[Dict[str, Any]]:
        """
        Generate movie recommendations for a user based on content-based filtering.
        Parameters:
            user (User): The user to make recommendations for.
        """
        user_profile = self.create_user_profile(user)
        if len(user_profile) == 0:
            return []

        # Calculate cosine similarity between user profile and all movies
        similarities = cosine_similarity([user_profile], self.genre_matrix).flatten()

        # Get top 10 similar movies
        top_indices = similarities.argsort()[-10:][::-1]

        results = []
        for idx in top_indices:
            results.append({
                "movieId": self.movies.iloc[idx].movieId,
                "similarity": similarities[idx]
            })

        return results

    
class HybridRecommendationSystem:
    
    def __init__(self, movies: pd.DataFrame, ratings: pd.DataFrame, collab_weight: float = 0.6, content_weight: float = 0.4):
        self.collab_weight = collab_weight
        self.content_weight = content_weight

        self.collab = CollaborativeRecommendationSystem(movies, ratings)
        self.collab.initialise()

        self.content = ContentRecommendationSystem(movies, ratings)

        self.movies = movies
        self.ratings = ratings

    def recommend(self, user: User, top_n: int = 10) -> List[Dict[int, float]]:
        """
        Generate hybrid movie recommendations for a user.
        Parameters:
            user (User): The user to make recommendations for.
            top_n (int): The maximum number of recommendations to return.
        """
        # Get collaborative recommendations
        collab_recs = self.collab.recommend(user)
        # Convert to dict for easier scoring
        collab_scores = {rec["movieId"]: rec["similarity"] for rec in collab_recs}

        # Get content recommendations
        content_recs = self.content.recommend(user)
        content_scores = {rec["movieId"]: rec["similarity"] for rec in content_recs}

        # Combine both
        hybrid_scores = {}
        all_movie_ids = set(collab_scores.keys()).union(set(content_scores.keys()))

        for movie_id in all_movie_ids:
            collab_score = collab_scores.get(movie_id, 0)
            content_score = content_scores.get(movie_id, 0)

            hybrid_score = (
                self.collab_weight * collab_score +
                self.content_weight * content_score
            )

            hybrid_scores[movie_id] = hybrid_score

        # Sort by score
        sorted_movies = sorted(
            hybrid_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Return top N movies with titles
        results = []
        for movie_id, score in sorted_movies[:top_n]:
            results.append({
                "movieId": int(movie_id),
                "score": float(score)
            })
        
        user.cache_recommendations(results)

        return results
