from Data_Loader import CollaborativeRecommendationSystem, ContentRecommendationSystem, extract_year
import pandas as pd
from line_profiler import LineProfiler

ratings = pd.read_csv("app/datasets/ratings.csv")
movies = pd.read_csv("app/datasets/movies.csv")

def standard_collaborative_recommendation_test():
    crs = CollaborativeRecommendationSystem(movies, ratings)
    crs.initialise()
    results = crs.recommend(1, 3)
    print( results )

def standard_content_recommendation_test():
    content = ContentRecommendationSystem( movies, ratings )
    print( content.recommend( 1 ) )

def extraction_test():
    extract_year(movies, "app/datasets/extracted_year.csv")

standard_content_recommendation_test()
#standard_collaborative_recommendation_test()