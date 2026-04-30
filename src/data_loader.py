import os
import zipfile
import tempfile
import urllib.request
import pandas as pd
import streamlit as st
from src.utils import fix_title_display

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@st.cache_data(show_spinner=False)
def download_movielens_small():
    local_movies = os.path.join(BASE_DIR, "data", "movies.csv")
    local_ratings = os.path.join(BASE_DIR, "data", "ratings.csv")
    if os.path.exists(local_movies) and os.path.exists(local_ratings):
        return local_movies, local_ratings

    dest_path = tempfile.gettempdir()
    movies_path = os.path.join(dest_path, "movies.csv")
    ratings_path = os.path.join(dest_path, "ratings.csv")
    if os.path.exists(movies_path) and os.path.exists(ratings_path):
        return movies_path, ratings_path

    url = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
    zip_path = os.path.join(dest_path, "ml-latest-small.zip")
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extract("ml-latest-small/movies.csv", dest_path)
        z.extract("ml-latest-small/ratings.csv", dest_path)
        os.replace(
            os.path.join(dest_path, "ml-latest-small", "movies.csv"), movies_path
        )
        os.replace(
            os.path.join(dest_path, "ml-latest-small", "ratings.csv"), ratings_path
        )
    if os.path.exists(zip_path):
        try:
            os.remove(zip_path)
        except:
            pass
    return movies_path, ratings_path

@st.cache_data(show_spinner=False)
def load_data():
    movies_path, ratings_path = download_movielens_small()
    movies = pd.read_csv(movies_path)
    ratings = pd.read_csv(ratings_path)
    movies["year"] = movies["title"].str.extract(r"\((\d{4})\)")[0].astype(float)
    movies["title_clean"] = movies["title"].str.replace(
        r"\s*\(\d{4}\)$", "", regex=True
    )
    movies["title_search"] = movies["title_clean"].apply(fix_title_display).str.lower()
    return movies, ratings
