import folium
from folium.plugins import MarkerCluster
import streamlit as st
from .timing import timing_decorator


@st.cache_resource()
@timing_decorator
def create_base_map(df, default_location=None, zoom_level=13):
    """Create a base map centered on the data points"""
    if default_location:
        center_lat, center_lng = default_location
    else:
        center_lat = df["lat"].mean()
        center_lng = df["lng"].mean()

    my_map = folium.Map(location=[center_lat, center_lng], zoom_start=zoom_level)
    return my_map


@timing_decorator
def add_invaders_to_map(my_map, df, use_clusters=True):
    """Add Space Invaders to the map"""
    if use_clusters:
        marker_cluster = MarkerCluster().add_to(my_map)

    # Create all markers first
    markers = []
    for _, row in df.iterrows():
        popup_text = f"""
        <b>ID:</b> {row['id']}<br>
        <b>Status:</b> {row['status']}<br>
        <b>Points:</b> {row['points']}<br>
        """
        if row["hint"]:
            popup_text += f"<b>Hint:</b> {row['hint']}"

        popup = folium.Popup(popup_text, max_width=300)

        # Choose color based on status
        color = "green" if row["status"] == "OK" else "red"

        marker = folium.Marker(
            location=[row["lat"], row["lng"]],
            popup=popup,
            tooltip=row["id"],
            icon=folium.Icon(color=color, icon="gamepad", prefix="fa"),
        )
        markers.append(marker)

    # Add all markers to the map after iteration
    for marker in markers:
        if use_clusters:
            marker.add_to(marker_cluster)
        else:
            marker.add_to(my_map)

    return my_map
