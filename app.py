import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
from streamlit_geolocation import streamlit_geolocation

from utils.data_loader import load_invaders_data, get_cities
from utils.map_utils import create_base_map, add_invaders_to_map

# Set page config
st.set_page_config(page_title="Space Invaders Map", page_icon="👾", layout="wide")

# Initialize session state for persistence
if "user_location" not in st.session_state:
    st.session_state.user_location = None
if "get_location" not in st.session_state:
    st.session_state.get_location = True
if "selected_invader" not in st.session_state:
    st.session_state.selected_invader = None


# Load data with caching
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    data = load_invaders_data()
    # Ensure data types are correct
    if "points" in data.columns:
        data["points"] = pd.to_numeric(data["points"], errors="coerce")
    return data


def filter_data(df, city, status, min_points):
    """Filter dataframe based on selected criteria"""
    filtered = df.copy()
    if city != "All":
        filtered = filtered[filtered["city"] == city]
    if status != "All":
        filtered = filtered[filtered["status"] == status]
    filtered = filtered[filtered["points"] >= min_points]
    return filtered


def get_user_location():
    """Get user location with error handling"""
    location = streamlit_geolocation()
    if (
        location
        and isinstance(location, dict)
        and "latitude" in location
        and "longitude" in location
    ):
        try:
            lat = float(location["latitude"])
            lng = float(location["longitude"])
            return (lat, lng)
        except (ValueError, TypeError):
            pass
    return None


def display_stats(df):
    """Display statistics in the sidebar"""
    st.sidebar.header("Statistics")
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Total Invaders", f"{len(df)}")
    col2.metric("Total Points", f"{int(df['points'].sum())}")

    # Add more insightful stats
    if not df.empty:
        st.sidebar.markdown("---")
        avg_points = round(df["points"].mean(), 1)
        max_points = int(df["points"].max())
        st.sidebar.metric("Average Points", f"{avg_points}")
        st.sidebar.metric("Highest Points", f"{max_points}")


def create_visualizations(df, filtered_df):
    """Create visualization tabs with more context"""
    st.header("Visualizations")
    tabs = st.tabs(["City Distribution", "Points Distribution", "Status Distribution"])

    with tabs[0]:
        col1, col2 = st.columns([3, 1])
        with col1:
            city_counts = df["city"].value_counts().sort_values(ascending=False)
            st.bar_chart(city_counts)
        with col2:
            st.metric("Total Cities", len(city_counts))
            st.metric("Most Popular", city_counts.index[0])
            st.metric(
                "Selected City Count",
                (
                    len(filtered_df)
                    if st.session_state.get("selected_city") != "All"
                    else "All cities"
                ),
            )

    with tabs[1]:
        points_dist = pd.DataFrame(df["points"].describe()).T
        st.dataframe(points_dist)
        st.bar_chart(df["points"].value_counts().sort_index())

    with tabs[2]:
        status_counts = df["status"].value_counts().sort_values(ascending=False)
        col1, col2 = st.columns([3, 1])
        with col1:
            st.bar_chart(status_counts)
        with col2:
            for status, count in status_counts.items():
                st.metric(f"{status}", f"{count}")


def main():
    # Load data
    df = load_data()
    cities = get_cities(df)

    # App title and description
    st.title("Space Invaders Location Map 👾")
    st.markdown(
        """
    This application displays the locations of Space Invader street art around the world.
    Use the filters to explore different cities and view details about each invader.
    """
    )

    # Sidebar filters with more intuitive layout
    st.sidebar.header("Filters")

    # City filter
    selected_city = st.sidebar.selectbox(
        "Select City", ["All"] + cities, key="selected_city"
    )

    # Status filter with color indicators
    status_options = ["All"] + sorted(df["status"].unique().tolist())
    selected_status = st.sidebar.selectbox("Status", status_options)

    # Points filter with histogram
    min_points = int(df["points"].min())
    max_points = int(df["points"].max())

    # Show points distribution miniature
    points_counts = df["points"].value_counts().sort_index()
    st.sidebar.area_chart(points_counts)

    selected_points = st.sidebar.slider(
        "Minimum Points", min_points, max_points, min_points
    )

    # Filter data
    filtered_df = filter_data(df, selected_city, selected_status, selected_points)

    # Display stats
    display_stats(filtered_df)

    # Display options
    st.sidebar.header("Display Options")
    use_clusters = st.sidebar.checkbox("Use Clusters", value=True)
    show_heatmap = st.sidebar.checkbox("Show Heatmap", value=False)

    # Create map
    col1, col2 = st.columns([3, 1])

    with col1:
        if not filtered_df.empty:
            # Handle location
            if st.session_state.get_location:
                user_location = get_user_location()
                if user_location:
                    st.session_state.user_location = user_location
                    st.success("Located you successfully!")

            # Get location for map
            default_location = (
                st.session_state.user_location
                if st.session_state.user_location
                else (48.8566, 2.3522)  # Paris coordinates
            )

            # Map creation with existing parameters only
            m = create_base_map(filtered_df, default_location)
            m = add_invaders_to_map(m, filtered_df, use_clusters)

            # Add heatmap layer if requested (without modifying the existing function)
            if show_heatmap and len(filtered_df) > 0:
                try:
                    from folium.plugins import HeatMap

                    # Add heatmap directly to the map
                    heat_data = [
                        [row["lat"], row["lng"]]
                        for _, row in filtered_df.iterrows()
                        if pd.notnull(row.get("lat")) and pd.notnull(row.get("lng"))
                    ]
                    if heat_data:
                        HeatMap(heat_data).add_to(m)
                except (ImportError, AttributeError) as e:
                    st.sidebar.warning(
                        "Heatmap could not be displayed: missing coordinates or plugin."
                    )

            # Display map with error handling
            try:
                folium_static(m, width=800, height=600)
            except Exception as e:
                st.error(f"Error displaying map: {str(e)}")
                st.info("Try adjusting your filters or refreshing the page.")
        else:
            st.warning(
                "No data to display with current filters. Try changing your selection."
            )

    # Display data table with interactivity
    with col2:
        st.subheader("Invaders List")

        # Add search functionality
        search_term = st.text_input("Search by ID", "")

        display_df = filtered_df.copy()
        if search_term:
            display_df = display_df[
                display_df["id"].str.contains(search_term, case=False, na=False)
            ]

        # Interactive dataframe
        st.dataframe(
            display_df[["id", "city", "status", "points"]].sort_values(
                "points", ascending=False
            ),
            height=600,
            use_container_width=True,
            column_config={
                "points": st.column_config.ProgressColumn(
                    "Points",
                    help="Invader point value",
                    format="%d",
                    min_value=min_points,
                    max_value=max_points,
                ),
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    help="Current status of the invader",
                    options=df["status"].unique().tolist(),
                    required=True,
                ),
            },
        )

    # Create visualizations
    create_visualizations(df, filtered_df)

    # Add footer with information
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center">
            <p>Data last updated: [Update Date Here] | Created with Streamlit</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
