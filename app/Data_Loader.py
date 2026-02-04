import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neighbors import NearestNeighbors


def load_data():
    df = pd.read_csv('ratings.csv')   # userId, movieId, rating, timestamp
    movie_titles = pd.read_csv('movies.csv')  # movieId, title, genres

    data = pd.merge(df, movie_titles, on='movieId')
    return data

data = load_data()

user_movie_matrix = data.pivot_table(
    index='userId',
    columns='title',
    values='rating'
)
user_movie_matrix_filled = user_movie_matrix.fillna(0)
knn = NearestNeighbors(
    metric='cosine',
    algorithm='brute'
)

knn.fit(user_movie_matrix_filled)
#similar users to ID 1
user_id = 1

user_vector = user_movie_matrix_filled.loc[user_id].values.reshape(1, -1)

distances, indices = knn.kneighbors(
    user_vector,
    n_neighbors=6  # user + 5 nearest neighbors
)
similar_users = user_movie_matrix_filled.index[indices.flatten()]
similar_users
def recommend_movies(user_id, n_recommendations=5):
    user_vector = user_movie_matrix_filled.loc[user_id].values.reshape(1, -1)
    distances, indices = knn.kneighbors(user_vector, n_neighbors=6)

    similar_users = user_movie_matrix_filled.index[indices.flatten()[1:]]  # skip self

    # Average ratings from similar users
    similar_users_ratings = user_movie_matrix.loc[similar_users]
    mean_ratings = similar_users_ratings.mean()

    # Movies the user hasn’t rated
    user_rated_movies = user_movie_matrix.loc[user_id]
    unrated_movies = user_rated_movies[user_rated_movies.isna()]

    recommendations = mean_ratings[unrated_movies.index]
    recommendations = recommendations.sort_values(ascending=False)

    return recommendations.head(n_recommendations)

recommend_movies(user_id=1)
