from Data_Loader import CollaborativeRecommendationSystem, extract_year
import pandas as pd
from line_profiler import LineProfiler

def standard_recommendation_test():
    ratings = pd.read_csv("app/datasets/ratings.csv")
    movies = pd.read_csv("app/datasets/movies.csv")

    crs = CollaborativeRecommendationSystem(movies, ratings)
    crs.initialise()
    results = crs.recommend(1, 3)
    print( len( results ) )


def extraction_test():
    movies = pd.read_csv("app/datasets/movies.csv")
    extract_year(movies, "app/datasets/extracted_year.csv")

extraction_test()
    
#standard_recommendation_test()