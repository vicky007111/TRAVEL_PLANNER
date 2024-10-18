import streamlit as st
import requests
import openrouteservice
import networkx as nx
import matplotlib.pyplot as plt

# API Keys
ORS_API_KEY = "5b3ce3597851110001cf6248dbc0d825bf6d4b69b125fac5de442cbf"
WEATHER_API_KEY = "32b81c71eced042b3edd4ffd4835d21d"

# Initialize OpenRouteService client
client = openrouteservice.Client(key=ORS_API_KEY)

# Add a custom background image and style the UI
st.markdown("""
    <style>
    body {
        background-image: url('https://www.yourimageurl.com/travel_bg.jpg');
        background-size: cover;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 12px;
        padding: 10px;
        font-size: 16px;
    }
    .stTextInput > div > input {
        background-color: #f1f1f1;
        border: 2px solid #ccc;
        padding: 10px;
    }
    h1, h2, h3 {
        color: #4CAF50;
    }
    .info {
        background-color: #e7f3fe;
        border-left: 6px solid #2196F3;
        color: #2196F3;
    }
    </style>
""", unsafe_allow_html=True)

# Function to get real-time weather data
def get_weather(city):
    try:
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(weather_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error getting weather: {e}")
        return None

# Function to get directions between two points
def get_directions(start_point, end_point):
    try:
        # Geocoding the city names to coordinates
        start_coords = client.pelias_search(start_point)['features'][0]['geometry']['coordinates']
        end_coords = client.pelias_search(end_point)['features'][0]['geometry']['coordinates']
        
        # Fetching directions
        coords = client.directions(coordinates=[start_coords, end_coords], profile='driving-car', format='geojson')
        return coords
    except Exception as e:
        st.error(f"Error getting directions: {e}")
        return None

# Streamlit UI
st.title("🌍 Advanced Travel Planner with Real-Time Maps")

# User inputs: Start and End points
start_point = st.text_input("📍 Enter your starting location:")
end_point = st.text_input("📍 Enter your destination:")

# Button to confirm
if st.button("🔍 Get Directions"):
    if start_point and end_point:
        st.write(f"Fetching directions from **{start_point}** to **{end_point}**...")

        # Get directions
        directions = get_directions(start_point, end_point)

        if directions:
            route = directions['features'][0]['geometry']['coordinates']
            st.success("Route fetched successfully!")

            # Plot the graph representing the route
            G = nx.Graph()

            # Create edges from the route data
            for i in range(len(route) - 1):
                G.add_edge((route[i][1], route[i][0]), (route[i + 1][1], route[i + 1][0]))

            # Define positions for nodes using a layout (spring layout)
            pos = nx.spring_layout(G)

            # Plotting the graph
            plt.figure(figsize=(12, 8))
            nx.draw_networkx_nodes(G, pos, node_size=50, node_color='lightcoral', alpha=0.8, edgecolors='black')
            nx.draw_networkx_edges(G, pos, width=2, alpha=0.6, edge_color='darkblue')
            nx.draw_networkx_labels(G, pos, font_size=8, font_color='white')

            # Set the title and display settings
            plt.title("Route Graph", fontsize=18, fontweight='bold')
            plt.axis('off')  # Hide the axes for a cleaner look
            st.pyplot(plt)

            # Display real-time weather for start and destination
            start_weather = get_weather(start_point)
            end_weather = get_weather(end_point)

            if start_weather:
                temp = start_weather['main']['temp']
                description = start_weather['weather'][0]['description']
                st.info(f"🌡️ Weather in {start_point}: {temp}°C, {description}")

            if end_weather:
                temp = end_weather['main']['temp']
                description = end_weather['weather'][0]['description']
                st.info(f"🌡️ Weather in {end_point}: {temp}°C, {description}")
        else:
            st.error("No directions found. Please check the locations.")
    else:
        st.error("Please enter both starting and destination locations.")
