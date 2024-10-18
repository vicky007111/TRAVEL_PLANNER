import streamlit as st
import requests
import openrouteservice
import networkx as nx
import matplotlib.pyplot as plt
import random

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

# Function to get the city name from coordinates
def get_city_name(coords):
    try:
        result = client.pelias_search(f"{coords[1]}, {coords[0]}")  # Note the order of latitude and longitude
        if result['features']:  # Check if there are features returned
            return result['features'][0]['properties']['label']
        else:
            st.error("No features found for the coordinates.")
            return None
    except Exception as e:
        st.error(f"Error getting city name: {e}")
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
            for i in range(len(route) - 1):
                G.add_edge((route[i][1], route[i][0]), (route[i + 1][1], route[i + 1][0]))

            # Highlight the route
            plt.figure(figsize=(10, 8))
            pos = {node: (node[0], node[1]) for node in G.nodes()}  # Set positions based on coordinates
            nx.draw_networkx_nodes(G, pos, node_size=10, node_color='red')
            nx.draw_networkx_edges(G, pos, edge_color='blue', alpha=0.5)

            # Draw the route specifically
            route_edges = [((route[i][1], route[i][0]), (route[i + 1][1], route[i + 1][0])) for i in range(len(route) - 1)]
            nx.draw_networkx_edges(G, pos, edgelist=route_edges, edge_color='green', width=4)  # Shortest route in green
            
            # Select 5 random waypoints to display
            waypoint_indices = random.sample(range(1, len(route) - 1), min(5, len(route) - 2))  # Avoid first and last point
            for i in waypoint_indices:
                city_name = get_city_name((route[i][1], route[i][0]))  # Get the city name for the waypoint
                if city_name:
                    plt.text(route[i][1], route[i][0], city_name, fontsize=9, ha='right', color='black')

            plt.title("Route to Destination")
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
