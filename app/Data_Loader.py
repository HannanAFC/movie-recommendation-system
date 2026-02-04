import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neighbors import NearestNeighbors
#read csv
column_names = ['userId', 'movieId', 'rating', 'timestamp']
path = 'ratings.csv'
df = pd.read_csv(path, sep='\t', names=column_names)

df.head()

movie_titles = pd.read_csv('movies.csv')
movie_titles.head()
#merge datasets
data = pd.merge(df, movie_titles, on='movieId')
data.head()
