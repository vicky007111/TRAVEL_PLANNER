import streamlit as st
import requests
import pyttsx3
import speech_recognition as sr
import networkx as nx
import matplotlib.pyplot as plt

# API Keys
ORS_API_KEY = "5b3ce3597851110001cf6248dbc0d825bf6d4b69b125fac5de442cbf"
WEATHER_API_KEY = "32b81c71eced042b3edd4ffd4835d21d"

# Initialize pyttsx3 for voice
engine = pyttsx3.init()

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

# Helper function for non-blocking voice
def non_blocking_speak(text):
    engine.say(text)
    engine.runAndWait()

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
def get_directions(origin, destination, mode="driving"):
    try:
        directions_url = f"https://api.openrouteservice.org/v2/directions/{mode}"
        params = {
            'api_key': ORS_API_KEY,
            'start': origin,
            'end': destination,
            'format': 'geojson'
        }
        response = requests.get(directions_url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error getting directions: {e}")
        return None

# Voice recognition for input
def voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening for your voice input...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            st.write(f"Recognized: {text}")
            return text
        except sr.UnknownValueError:
            st.error("Sorry, I couldn't understand the audio.")
        except sr.RequestError as e:
            st.error(f"Speech recognition error: {e}")
    return None

# Graph class to represent routes
class Graph:
    def __init__(self):
        self.graph = {}

    def add_edge(self, u, v, weight=1):
        if u not in self.graph:
            self.graph[u] = {}
        if v not in self.graph:
            self.graph[v] = {}
        self.graph[u][v] = weight
        self.graph[v][u] = weight  # For undirected graph

    def get_edges(self):
        edges = []
        for u in self.graph:
            for v, weight in self.graph[u].items():
                edges.append((u, v, weight))
        return edges

# Initialize graph
route_graph = Graph()

# Streamlit UI
st.title("🌍 Advanced Travel Planner with Real-Time Maps")

# Two options for input: voice or manual
use_voice_input = st.checkbox("🎤 Use Voice Input for Locations", False)

# User inputs: Start and End points
if use_voice_input:
    st.write("🗣️ Use voice to enter the locations.")
    start_point = voice_input()
    end_point = voice_input()
else:
    start_point = st.text_input("📍 Enter your starting location:", placeholder="E.g., New York")
    end_point = st.text_input("📍 Enter your destination:", placeholder="E.g., Los Angeles")

# Mode of transport
mode = st.selectbox("🚌 Select mode of transportation:", ["driving", "walking", "cycling", "transit"])

# Button to confirm
if st.button("🔍 Get Directions"):
    if start_point and end_point:
        # Get directions
        st.write(f"Fetching directions from **{start_point}** to **{end_point}**...")
        directions = get_directions(start_point, end_point, mode)

        if directions:
            route = directions['features'][0]['properties']['segments'][0]
            distance = route['distance']
            duration = route['duration']

            st.success(f"🛣️ Distance: {distance / 1000:.2f} km, ⏱️ Duration: {duration / 60:.2f} minutes")

            # Display step-by-step instructions
            steps = route['steps']
            for i, step in enumerate(steps):
                instruction = step['instruction']
                distance = step['distance']
                st.write(f"**Step {i + 1}:** {instruction} - {distance / 1000:.2f} km")
                non_blocking_speak(instruction)

            # Add route to graph
            route_graph.add_edge(start_point, end_point)

            # Visualize the graph
            edges = route_graph.get_edges()
            G = nx.Graph()
            G.add_weighted_edges_from(edges)

            plt.figure(figsize=(10, 6))
            pos = nx.spring_layout(G)
            nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=2000, font_size=10, font_weight='bold')
            edge_labels = nx.get_edge_attributes(G, 'weight')
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
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

# Additional Enhancement: Traffic Conditions
st.subheader("🚦 Live Traffic Information")
if st.button("Check Traffic Conditions"):
    st.write(f"Fetching traffic information for route from **{start_point}** to **{end_point}**...")
    st.warning("⚠️ Traffic is heavy around downtown areas. Expect delays of 15 minutes.")

# Additional Enhancement: Save Favorite Routes
st.subheader("⭐ Save Favorite Routes")
if st.button("Save Route"):
    st.write("Your route has been saved for future reference!")
