import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd

from utils.data_loader import load_invaders_data, get_cities
from utils.map_utils import create_base_map, add_invaders_to_map

# Set page config
st.set_page_config(
    page_title="Space Invaders Map",
    page_icon="👾",
    layout="wide"
)

# Load data
@st.cache_data
def load_data():
    return load_invaders_data()

df = load_data()
cities = get_cities(df)

# App title and description
st.title("Space Invaders Location Map")
st.markdown("""
This application displays the locations of Space Invader street art around the world.
Use the filters to explore different cities and view details about each invader.
""")

# Sidebar filters
st.sidebar.header("Filters")

# City filter
selected_city = st.sidebar.selectbox("Select City", ["All"] + cities)

# Status filter
status_options = ["All"] + sorted(df['status'].unique().tolist())
selected_status = st.sidebar.selectbox("Status", status_options)

# Points filter
min_points = int(df['points'].min())
max_points = int(df['points'].max())
selected_points = st.sidebar.slider("Minimum Points", min_points, max_points, min_points)

# Filter data
filtered_df = df.copy()
if selected_city != "All":
    filtered_df = filtered_df[filtered_df['city'] == selected_city]
if selected_status != "All":
    filtered_df = filtered_df[filtered_df['status'] == selected_status]
filtered_df = filtered_df[filtered_df['points'] >= selected_points]

# Display stats
st.sidebar.header("Statistics")
st.sidebar.write(f"Total Invaders: {len(filtered_df)}")
st.sidebar.write(f"Total Points: {filtered_df['points'].sum()}")

# Display options
st.sidebar.header("Display Options")
use_clusters = st.sidebar.checkbox("Use Clusters", value=True)

# Create map
col1, col2 = st.columns([3, 1])

with col1:
    if not filtered_df.empty:
        m = create_base_map(filtered_df)
        m = add_invaders_to_map(m, filtered_df, use_clusters)
        folium_static(m, width=800, height=600)
    else:
        st.warning("No data to display with current filters.")

# Display data table
with col2:
    st.subheader("Invaders List")
    st.dataframe(
        filtered_df[['id', 'city', 'status', 'points']],
        height=600,
        use_container_width=True
    )

# Additional visualizations
st.header("Visualizations")
tabs = st.tabs(["City Distribution", "Points Distribution", "Status Distribution"])

with tabs[0]:
    city_counts = df['city'].value_counts()
    st.bar_chart(city_counts)

with tabs[1]:
    points_counts = df['points'].value_counts().sort_index()
    st.bar_chart(points_counts)

with tabs[2]:
    status_counts = df['status'].value_counts()
    st.bar_chart(status_counts)