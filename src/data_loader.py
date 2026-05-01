import os
import zipfile
import tempfile
import urllib.request
import pandas as pd
from functools import lru_cache
from src.utils import fix_title_display

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@lru_cache(maxsize=1)
def download_movielens_small():
    local_movies = os.path.join(BASE_DIR, "data", "movies.csv")
    local_ratings = os.path.join(BASE_DIR, "data", "ratings.csv")
    local_tags = os.path.join(BASE_DIR, "data", "tags.csv")
    if os.path.exists(local_movies) and os.path.exists(local_ratings) and os.path.exists(local_tags):
        return local_movies, local_ratings, local_tags

    dest_path = tempfile.gettempdir()
    movies_path = os.path.join(dest_path, "movies.csv")
    ratings_path = os.path.join(dest_path, "ratings.csv")
    tags_path = os.path.join(dest_path, "tags.csv")
    if os.path.exists(movies_path) and os.path.exists(ratings_path) and os.path.exists(tags_path):
        return movies_path, ratings_path, tags_path

    url = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
    zip_path = os.path.join(dest_path, "ml-latest-small.zip")
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extract("ml-latest-small/movies.csv", dest_path)
        z.extract("ml-latest-small/ratings.csv", dest_path)
        z.extract("ml-latest-small/tags.csv", dest_path)
        os.replace(
            os.path.join(dest_path, "ml-latest-small", "movies.csv"), movies_path
        )
        os.replace(
            os.path.join(dest_path, "ml-latest-small", "ratings.csv"), ratings_path
        )
        os.replace(
            os.path.join(dest_path, "ml-latest-small", "tags.csv"), tags_path
        )
    if os.path.exists(zip_path):
        try:
            os.remove(zip_path)
        except:
            pass
    return movies_path, ratings_path, tags_path

@lru_cache(maxsize=1)
def load_data():
    movies_path, ratings_path, tags_path = download_movielens_small()
    movies = pd.read_csv(movies_path)
    ratings = pd.read_csv(ratings_path)
    tags = pd.read_csv(tags_path)
    
    # Clean the titles
    movies["year"] = movies["title"].str.extract(r"\((\d{4})\)")[0].astype(float)
    movies["title_clean"] = movies["title"].str.replace(
        r"\s*\(\d{4}\)$", "", regex=True
    )
    movies["title_search"] = movies["title_clean"].apply(fix_title_display).str.lower()
    
    # Combine all tags for a single movie into one string
    tags_grouped = tags.groupby('movieId')['tag'].apply(lambda x: ' '.join(x.astype(str).str.lower())).reset_index()
    
    # Merge tags into movies
    movies = movies.merge(tags_grouped, on='movieId', how='left')
    movies['tag'] = movies['tag'].fillna('')
    
    # Create a "metadata" soup: genres (replace | with space) + user tags
    movies['metadata'] = movies['genres'].str.replace('|', ' ', regex=False).str.lower() + " " + movies['tag']
    
    return movies, ratings
