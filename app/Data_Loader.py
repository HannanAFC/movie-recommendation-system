import pandas as pd
from sklearn.neighbors import NearestNeighbors
import warnings


class CollaborativeRecommendationSystem():

    def __init__(self, movies: pd.DataFrame, ratings: pd.DataFrame):
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

        if (type(self.movie_user_matrix) == pd.DataFrame):
            movie_idx = self.movie_user_matrix.index.get_loc(movie_id)

            distances, indices = self.knn.kneighbors(
                self.movie_user_matrix.iloc[movie_idx].to_numpy().reshape(1, -1),
                n_neighbors=n + 1
            )

            similar_movies = []

            for i in range(1, len(indices[0])):
                similar_movie_id = self.movie_user_matrix.index[indices[0][i]]
                similarity = 1 - distances[0][i]
                similar_movies.append((similar_movie_id, similarity))

            return similar_movies
        else:
            warnings.warn( "Warning - movie matrix was not a dataframe, no similar movies found." )
            return []

    def initialise(self):
        self.__prepare()
        if (type( self.movie_user_matrix ) == pd.DataFrame):
            self.knn.fit( self.movie_user_matrix )
        else:
            warnings.warn( "Warning - movie matrix was not a dataframe, initialisation failed." )
        
    def recommend(self, user_id:int, recs_per_rating=3):
        current_user_ratings = self.ratings[self.ratings.userId == user_id]
        recommendations = []

        for index, row in current_user_ratings.iterrows():
            if row.rating >= 4.0:
                similar_movies = self.get_similar_movies(row.movieId, n=recs_per_rating)

                for movie in similar_movies:
                    if movie[0] not in current_user_ratings.movieId.values:
                        recommendations.append( { "movieId": movie[0], "similarity": movie[1] } )

        recommendations.sort( key=lambda x: x["similarity"], reverse=True )

        return recommendations