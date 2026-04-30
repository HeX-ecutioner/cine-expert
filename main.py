import os
import pandas as pd
import streamlit as st

from src.utils import (
    get_base64_of_bin_file,
    fix_title_display,
    render_stars,
    get_tmdb_api_key,
    fetch_poster_bytes,
    get_image_from_bytes,
)
from src.data_loader import load_data
from src.engine import (
    compute_content_features,
    compute_collaborative_features,
    aggregate_ratings,
    recommend_hybrid,
)

st.set_page_config(page_title="Movie Recommender System", page_icon="🎬", layout="wide")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------- UI ----------------

st.markdown(
    f"""
    <div style="display:flex; align-items:center; justify-content:space-between;">
        <h1 style="margin:0;">🎬 Movie Recommender System</h1>
        <img src="data:image/png;base64,{get_base64_of_bin_file(os.path.join(BASE_DIR, 'assets', 'icon.jpg'))}" 
             width="160" style="margin-left:20px;border-radius:10px;">
    </div>
    <br>
    """,
    unsafe_allow_html=True,
)

with st.spinner("Loading Recommendation Engine..."):
    movies, ratings = load_data()
    rating_agg = aggregate_ratings(ratings)
    content_features = compute_content_features(movies)
    cf_features = compute_collaborative_features(movies, ratings)

st.header("📊 Data Exploration")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        f"<p style='font-size:18px;'>Total Movies</p><p style='font-size:28px; font-weight:bold;'>{movies.shape[0]}</p>",
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"<p style='font-size:18px;'>Total Ratings</p><p style='font-size:28px; font-weight:bold;'>{ratings.shape[0]}</p>",
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"<p style='font-size:18px;'>Unique Users</p><p style='font-size:28px; font-weight:bold;'>{ratings['userId'].nunique()}</p>",
        unsafe_allow_html=True,
    )

st.subheader("🔝 Top 5 Most-Rated Movies")
top5 = rating_agg.merge(movies[["movieId", "title"]], on="movieId")
top5 = top5.sort_values("num_ratings", ascending=False).head(5)
top5["Average Rating"] = top5["avg_rating"].apply(render_stars)

table_html = "<table style='border-collapse: collapse; width: 100%;'>"
table_html += "<tr style='background-color:#1e1e1e; text-align:left;'><th>Title of Movie</th><th>Number of Ratings</th><th>Average Rating</th></tr>"
for _, row in top5.iterrows():
    table_html += f"<tr><td>{fix_title_display(row['title'])}</td><td>{row['num_ratings']}</td><td>{row['Average Rating']}</td></tr>"
table_html += "</table>"
st.markdown(
    f"<div style='overflow-x:auto;'>{table_html}</div><br>", unsafe_allow_html=True
)

st.markdown("---")

@st.fragment
def display_recommendations(recs, movie_name, movies, rating_agg):
    if not recs:
        st.warning("No suggestions found for this search and filter combination.")
        return

    st.subheader(f"Top 5 recommendations for **{movie_name}**")

    cols = st.columns(5)
    for i, rec in enumerate(recs[:5]):
        title, genres, score, year = rec
        with cols[i]:
            api_key = get_tmdb_api_key()
            poster_bytes = fetch_poster_bytes(title, year, api_key)
            st.image(get_image_from_bytes(poster_bytes), use_container_width=True)

            st.markdown(f"**{fix_title_display(title)}**")
            st.caption(f"{' | '.join(genres.split('|'))}")
            movieid = movies.loc[movies["title"] == title, "movieId"].values[0]
            row = rating_agg[rating_agg.movieId == movieid]
            actual_rating = row.iloc[0].avg_rating if not row.empty else 0

            st.markdown(
                f"<small>{render_stars(actual_rating)}<br><b>Match: {score*100:.1f}%</b></small>",
                unsafe_allow_html=True,
            )

    st.markdown("<br><b>Detailed View of Top 10 Recommendations</b>", unsafe_allow_html=True)
    df_out = pd.DataFrame(
        [
            {
                "Rank": i + 1,
                "Title": fix_title_display(r[0]),
                "Genres": " | ".join(r[1].split("|")),
                "Match (%)": f"{r[2]*100:.2f}%",
            }
            for i, r in enumerate(recs)
        ]
    )
    st.dataframe(df_out.set_index("Rank"), use_container_width=True)

st.header("🔍 Find Similar Movies")

if "recs" not in st.session_state:
    st.session_state.recs = []
if "movie_name" not in st.session_state:
    st.session_state.movie_name = ""

with st.form("search_form"):
    col_input, col_filters = st.columns([2, 1])

    with col_input:
        movie_name = st.text_input(
            "Enter a movie you like:", placeholder="e.g. The Dark Knight"
        )

    with col_filters:
        min_rating = st.slider("Minimum Rating", 0.0, 5.0, 3.5, 0.1)
        content_weight = st.slider("Content vs Collaborative", 0.0, 1.0, 0.5, 0.05)

    submitted = st.form_submit_button("Search")

if submitted and movie_name:
    st.session_state.movie_name = movie_name
    st.session_state.recs = recommend_hybrid(
        movie_name,
        movies,
        content_features,
        cf_features,
        content_weight,
        10,
        min_rating,
        rating_agg,
    )

if st.session_state.movie_name:
    display_recommendations(st.session_state.recs, st.session_state.movie_name, movies, rating_agg)

# ------------- FOOTER ----------------

st.markdown(
    """<hr style="margin-top:50px; margin-bottom:10px;">
<div style="text-align:right; color:gray; font-size:14px;">🎬 Movie Recommender System • Built with Python & Streamlit</div>""",
    unsafe_allow_html=True,
)
