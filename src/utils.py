import base64
import re
import requests
import pandas as pd
import streamlit as st
from difflib import SequenceMatcher
from PIL import Image
from io import BytesIO

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""

def clean_title(title):
    return re.sub(r"\(\d{4}\)", "", title).strip()

def fix_title_display(title):
    if title.endswith(", The"):
        return "The " + title[:-5]
    if title.endswith(", A"):
        return "A " + title[:-3]
    if title.endswith(", An"):
        return "An " + title[:-4]
    return title

def best_match(results, clean_title, year=None):
    if not results:
        return None
    best, best_score = None, 0
    for r in results:
        tmdb_title = r.get("title", "")
        score = SequenceMatcher(None, clean_title.lower(), tmdb_title.lower()).ratio()
        if pd.notna(year) and "release_date" in r and r["release_date"]:
            if str(int(year)) in r["release_date"]:
                score += 0.1
        if score > best_score:
            best, best_score = r, score
    return best

def render_stars(rating: float) -> str:
    full = int(rating)
    half = 1 if rating - full >= 0.5 else 0
    empty = 5 - full - half
    return "★" * full + ("⯨" if half else "") + "☆" * empty

@st.cache_data(show_spinner=False)
def fetch_poster_bytes(title, year, tmdb_api_key):
    try:
        clean = clean_title(title)
        params = {"api_key": tmdb_api_key, "query": clean, "include_adult": False}
        if year and not pd.isna(year):
            params["year"] = int(year)

        resp = requests.get(
            "https://api.themoviedb.org/3/search/movie", params=params, timeout=5
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])

        if not results:
            params.pop("year", None)
            resp = requests.get(
                "https://api.themoviedb.org/3/search/movie", params=params, timeout=5
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])

        match = best_match(results, clean, year)
        if match and match.get("poster_path"):
            url = f"https://image.tmdb.org/t/p/w300{match['poster_path']}"
            return requests.get(url, timeout=5).content

    except Exception:
        pass

    img = Image.new("RGB", (300, 450), color=(73, 109, 137))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def get_image_from_bytes(img_bytes):
    return Image.open(BytesIO(img_bytes))

def get_tmdb_api_key():
    try:
        tmdb = st.secrets.get("tmdb", {})
        return tmdb.get("api_key", "")
    except Exception:
        return ""
