import streamlit as st
import folium
from streamlit_folium import st_folium

# Create a Folium map centered on a specific location
map = folium.Map(location=[45.5236, -122.6750], zoom_start=12)

# Display the map in Streamlit with a specified height
st_folium(map, height=500)  # Adjust height as needed

# Additional content can be added here
st.write("This is a Folium map displayed in Streamlit.")