import re
import numpy as np
from difflib import SequenceMatcher
from sklearn.metrics.pairwise import cosine_similarity

try:
    from rapidfuzz import process, fuzz

    USE_RAPIDFUZZ = True
except:
    USE_RAPIDFUZZ = False

from sklearn.feature_extraction.text import TfidfVectorizer


def compute_content_features(movies_df):
    # Initialize TF-IDF, removing common English stop words (the, and, is)
    tfidf = TfidfVectorizer(stop_words="english")

    # Fit the vectorizer on our new metadata soup
    tfidf_matrix = tfidf.fit_transform(movies_df["metadata"])

    # Return as an array for the cosine_similarity function
    return tfidf_matrix.toarray().astype(np.float32)


def compute_collaborative_features(movies_df, ratings_df):
    item_user_matrix = ratings_df.pivot(
        index="movieId", columns="userId", values="rating"
    )
    aligned_matrix = item_user_matrix.reindex(movies_df["movieId"])
    normalized = aligned_matrix.sub(aligned_matrix.mean(axis=1), axis=0)
    normalized = normalized.fillna(0)
    return normalized.astype(np.float32).values


def aggregate_ratings(ratings_df):
    agg = ratings_df.groupby("movieId").rating.agg(["mean", "count"]).reset_index()
    agg.rename(columns={"mean": "avg_rating", "count": "num_ratings"}, inplace=True)

    C = agg["avg_rating"].mean()
    m = agg["num_ratings"].quantile(0.6)

    agg["weighted_rating"] = (agg["num_ratings"] / (agg["num_ratings"] + m)) * agg[
        "avg_rating"
    ] + (m / (agg["num_ratings"] + m)) * C

    return agg


def find_movie_index(movie_title, movies_df):
    titles = movies_df["title_clean"]
    search_query = movie_title.strip().lower()

    exact = movies_df[movies_df["title_search"] == search_query]
    if not exact.empty:
        return exact.index[0]

    normalized_query = re.sub(r"[^a-z0-9]", "", search_query)
    normalized_titles = movies_df["title_search"].apply(
        lambda x: re.sub(r"[^a-z0-9]", "", str(x))
    )
    exact_norm = movies_df[normalized_titles == normalized_query]
    if not exact_norm.empty:
        return exact_norm.index[0]

    if USE_RAPIDFUZZ:
        match = process.extractOne(movie_title, titles.tolist(), scorer=fuzz.WRatio)
        if match and match[1] > 70:
            return titles[titles == match[0]].index[0]

    contains = movies_df[
        titles.str.lower().str.contains(movie_title.strip().lower(), na=False)
    ].copy()
    if contains.empty:
        return None

    contains["match_score"] = contains["title_clean"].apply(
        lambda x: SequenceMatcher(None, movie_title.lower(), x.lower()).ratio()
    )

    return contains.sort_values("match_score", ascending=False).index[0]


def recommend_hybrid(
    movie_title,
    movies_df,
    content_features,
    cf_features,
    content_weight=0.5,
    top_n=5,
    min_avg_rating=None,
    rating_agg=None,
):

    idx = find_movie_index(movie_title, movies_df)
    if idx is None:
        return []

    content_scores = cosine_similarity(
        content_features[idx : idx + 1], content_features
    ).ravel()
    cf_scores = cosine_similarity(cf_features[idx : idx + 1], cf_features).ravel()

    hybrid_scores = (content_weight * content_scores) + (
        (1 - content_weight) * cf_scores
    )

    sim_scores = list(enumerate(hybrid_scores))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    recommendations = []
    for i, score in sim_scores:
        if i == idx:
            continue

        movieid = movies_df.iloc[i]["movieId"]

        if min_avg_rating is not None and rating_agg is not None:
            row = rating_agg[rating_agg.movieId == movieid]
            if row.empty or row.iloc[0].weighted_rating < min_avg_rating:
                continue

        recommendations.append(
            (
                movies_df.iloc[i]["title"],
                movies_df.iloc[i]["genres"],
                float(score),
                movies_df.iloc[i]["year"],
            )
        )

        if len(recommendations) >= top_n:
            break

    return recommendations
