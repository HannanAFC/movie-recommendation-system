import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer
import warnings
import numpy as np
from app.models import User, MovieRating
from app import db

class CollaborativeRecommendationSystem():

    def __init__(self, movies: pd.DataFrame, ratings: pd.DataFrame):
        if movies.empty or ratings.empty:
            raise ValueError("Movies and ratings dataframes must contain data.")
        self.movies = movies
        self.ratings = ratings
        self.df = None
        self.movie_user_matrix = None
        self.knn = NearestNeighbors(
            metric="cosine",
            algorithm="brute"
        )

    def __prepare(self):
        self.movie_user_matrix = self.ratings.pivot_table(
            index="movieId",
            columns="userId",
            values="rating",
            fill_value=0
        )

        self.movie_user_matrix = self.movie_user_matrix.fillna(0)
    
    def get_similar_movies(self, movie_id, n=10):

        # Check if the movie user matrix is already prepared
        if (type(self.movie_user_matrix) == pd.DataFrame):
            # Find the given movie in the matrix
            try:
                movie_index = self.movie_user_matrix.index.get_loc(movie_id)
            except KeyError:
                warnings.warn(f"Warning - movie with id {movie_id} not found in the matrix.")
                return []

            # Get the indices of the n nearest neighbors
            distances, indices = self.knn.kneighbors(
                self.movie_user_matrix.iloc[movie_index].to_numpy().reshape(1, -1),
                n_neighbors=n + 1
            )

            similar_movies = []

            # Get the similarity scores for each neighbor
            for i in range(1, len(indices[0])):
                similar_movie_id = self.movie_user_matrix.index[indices[0][i]]
                similarity = 1 - distances[0][i]
                similar_movies.append((similar_movie_id, similarity))

            return similar_movies
        else:
            warnings.warn( "Warning - movie matrix was not a dataframe, no similar movies found." )
            return []

    def initialise(self):
        # Attempt to create the matrix and fit to the data
        self.__prepare()
        if (type( self.movie_user_matrix ) == pd.DataFrame):
            self.knn.fit( self.movie_user_matrix )
        else:
            warnings.warn( "Warning - movie matrix was not a dataframe, initialisation failed." )
        
    def recommend(self, user: User, recs_per_rating=3):
        # Get the users ratings
        current_user_ratings = user.get_user_ratings()
        recommendations = []

        if len( current_user_ratings ) > 0:
            # Loop through each rating, if it is more than 4.0, find similar movies and add them to the list
            for rating in current_user_ratings:
                if float( rating.rating ) >= 4.0:
                    similar_movies = self.get_similar_movies(int( rating.movie_id ), n=recs_per_rating)

                    for movie in similar_movies:
                        if int( movie[0] ) not in [int( movie.movie_id ) for movie in current_user_ratings]:
                            recommendations.append( { "movieId": movie[0], "similarity": movie[1] } )

            # Finally, sort by the similarity score in descending order
            recommendations.sort( key=lambda x: x["similarity"], reverse=True )
        else:
            warnings.warn("No user ratings found for this user")

        return recommendations
    
class ContentRecommendationSystem():
    
    def __init__(self, movies: pd.DataFrame, ratings: pd.DataFrame):
        if movies.empty or ratings.empty:
            raise ValueError("Movies and ratings dataframes must contain data.")
        self.movies = movies
        self.ratings = ratings
        # Split genres into a list
        try:
            self.movies["genres"] = movies["genres"].apply(lambda x: x.split("|"))
        except Exception as e:
            raise ValueError("Error splitting genres.")
        self.mlb = MultiLabelBinarizer()
        self.genre_matrix = self.mlb.fit_transform(self.movies["genres"])
        self.genre_matrix = self.genre_matrix / self.genre_matrix.sum(axis=0)

    def create_user_profile(self, user: User):
        def calculate_vector(movie: MovieRating):
            try:
                movie_index = np.where(self.movies["movieId"] == movie.movie_id)[0][0]
            except IndexError:
                return 0
            return self.genre_matrix[movie_index] * float(movie.rating)

        def update_vector(user_vector, movie):
            return user_vector + calculate_vector(movie)

        # Get users ratings
        current_user_ratings = user.get_user_ratings()
    
        # Create a vector for the current user using the genre matrix
        user_vector = np.zeros(self.genre_matrix.shape[1])
    
        for movie in current_user_ratings:
            user_vector = update_vector(user_vector, movie)
            
        return user_vector / sum([float(movie.rating) for movie in current_user_ratings])
    
    def recommend(self, user: User):
        user_profile = self.create_user_profile(user)
        if len(user_profile) == 0:
            return []
        similarities = cosine_similarity([user_profile], self.genre_matrix).flatten()

        top_indices = similarities.argsort()[-10:][::-1]

        results = []
        for idx in top_indices:
            results.append({
                "movieId": self.movies.iloc[idx].movieId,
                "similarity": similarities[idx]
            })

        return results

# Helper function - extracts the years in the movie title into a new column, only run once
def extract_year(movies: pd.DataFrame, file_path: str):
    
    # Extract year from title string and place into new column
    movies['year'] = movies['title'].str.extract(r'\((\d{4})\)')
    movies['title'] = movies['title'].str.replace(r'\(\d{4}\)', '', regex=True)
    
    movies.to_csv(file_path, index=False)
    
class HybridRecommendationSystem:
    def __init__(self, movies: pd.DataFrame, ratings: pd.DataFrame, collab_weight=0.6, content_weight=0.4):
        self.collab_weight = collab_weight
        self.content_weight = content_weight

        self.collab = CollaborativeRecommendationSystem(movies, ratings)
        self.collab.initialise()

        self.content = ContentRecommendationSystem(movies, ratings)

        self.movies = movies
        self.ratings = ratings
    def recommend(self, user: User, top_n=10):
        # Get collaborative recommendations
        collab_recs = self.collab.recommend(user)

        # Convert to dict for easier scoring
        collab_scores = {}
        for rec in collab_recs:
            collab_scores[rec["movieId"]] = rec["similarity"]

        # Get content recommendations
        content_recs = self.content.recommend(user)

        content_scores = {
            rec["movieId"]: rec["similarity"]
            for rec in content_recs
        }
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
            movie_title = self.movies[self.movies.movieId == movie_id].title.values[0]
            results.append({
                "movieId": int(movie_id),
                "title": str(movie_title),
                "score": float(score)
            })

        return results
