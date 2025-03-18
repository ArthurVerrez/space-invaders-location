import json
import pandas as pd
import streamlit as st


@st.cache_data()
def load_invaders_data(file_path="data/space_invaders_database.json"):
    """Load Space Invaders data from JSON file and convert to DataFrame"""
    with open(file_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Convert coordinates to float (replace comma with period if needed)
    # Handle empty strings and invalid values
    df["lat"] = pd.to_numeric(df["lat"].str.replace(",", "."), errors="coerce")
    df["lng"] = pd.to_numeric(df["lng"].str.replace(",", "."), errors="coerce")

    # Convert points to numeric
    df["points"] = pd.to_numeric(df["points"], errors="coerce")

    # Drop rows with missing coordinates
    df = df.dropna(subset=["lat", "lng"])

    return df


@st.cache_data()
def get_cities(df):
    """Get unique cities from the dataset"""
    return sorted(df["city"].unique())
