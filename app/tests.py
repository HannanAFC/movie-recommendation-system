from Data_Loader import CollaborativeRecommendationSystem
import pandas as pd
from line_profiler import LineProfiler

def standard_recommendation_test():
    ratings = pd.read_csv("app/datasets/ratings.csv")
    movies = pd.read_csv("app/datasets/movies.csv")

    crs = CollaborativeRecommendationSystem(movies, ratings)
    crs.initialise()
    results = crs.recommend(1, 3)
    print( len( results ) )

standard_recommendation_test()