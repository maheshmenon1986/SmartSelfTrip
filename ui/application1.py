from pathlib import Path

from streamlit_folium import st_folium
import pandas as pd
import streamlit as st
import base64
import json
import sys
import os
import datetime

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Assuming utility.nlp_processing exists and works
from utility.nlp_processing import interpret_intent

# --- Configuration ---
image_path = os.path.join(project_root, "utility", "images", "technology.png")
st.set_page_config(
    layout="wide",
    page_title="Smart2SelfTrip",
    page_icon=image_path # Set the page icon to the path of your image
)

# --- Session State Initialization ---
if "history" not in st.session_state:
    st.session_state.history = [
        {
            "role": "assistant",
            "content": "Can’t figure out where to go? \n\n Let me help you plan a smooth and fun trip — powered by Google Maps"
        },
        {
            "role": "assistant",
            "content": "Just Share your travel ideas"
        },
    ]
if "show_results" not in st.session_state:
    st.session_state.show_results = False

if "intent_context" not in st.session_state:
    st.session_state.intent_context = {
        "active_intent": None,
        "slots_filled": {},
        "pending_slot": None
    }
# Session state variables for checkboxes
if "checkbox_options" not in st.session_state:
    st.session_state.checkbox_options = []
if "selected_place_types" not in st.session_state:
    st.session_state.selected_place_types = []

# Dedicated state variable for controlling chat input's enabled/disabled state
if "chat_input_enabled" not in st.session_state:
    st.session_state.chat_input_enabled = True # Start enabled

# Key for the chat input that changes to force re-render
if "chat_input_key" not in st.session_state:
    st.session_state.chat_input_key = "chat_input_initial"
if "rerun_count" not in st.session_state:
    st.session_state.rerun_count = 0

# Dedicated state variables for storing distance matrices
if "walking_matrix" not in st.session_state:
    st.session_state.walking_matrix = None
if "transit_matrix" not in st.session_state:
    st.session_state.transit_matrix = None

# New session state for route mode map
if "route_mode_map" not in st.session_state:
    st.session_state.route_mode_map = None

if "direction_details" not in st.session_state: # This initializes it
    st.session_state.direction_details = {} # Initialize as an empty dict, not None


# Toggle to use live Google API or mock data
use_live_api = True

# --- Function to get Base64 encoded image ---
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
            return encoded_string
    except FileNotFoundError:
        st.error(f"Image not found: {image_path}")
        return None
    except Exception as e:
        st.error(f"Error loading image {image_path}: {e}")
        return None

# Paths to your images
welcomescreen_path = Path(project_root) / "utility" / "images" / "welcomescreen.jpg"
result_path = Path(project_root) / "utility" / "images" / "result.jpg"

# --- NEW: Define paths for your mock Distance Matrix files ---
MOCK_PLACES_PATH =  Path(project_root) / "ui" / "apidata" / "mock_places.json"
MOCK_WALKING_MATRIX_PATH = Path(project_root) / "ui" / "apidata" / "mock_walking_matrix.json"
MOCK_TRANSIT_MATRIX_PATH = Path(project_root) / "ui" / "apidata" / "mock_transit_matrix.json"
MOCK_DIRECTIONS_DETAILS_PATH =  Path(project_root) / "ui" / "apidata" / "mock_directions_details.json"

welcome_b64 = get_base64_image(welcomescreen_path)
result_b64 = get_base64_image(result_path)

# Prepare base64 URLs
BACKGROUND_IMAGE_URL = f"data:image/jpeg;base64,{welcome_b64}" if welcome_b64 else ""
RESULT_BACKGROUND_IMAGE_URL = f"data:image/jpeg;base64,{result_b64}" if result_b64 else ""

# --- Dynamic Custom CSS based on state ---
active_background_url = RESULT_BACKGROUND_IMAGE_URL if st.session_state.show_results else BACKGROUND_IMAGE_URL
main_block_bg_color = "#FFFFFF" if st.session_state.show_results else "transparent"
sidebar_bg_color = "#f0f2f6" if st.session_state.show_results else "transparent"

ITINERARY_BUTTON_KEY = "your_personalized_itinerary_button"

custom_css = f"""
<style>
/* Base Streamlit App Background - Dynamically set */
.stApp {{
    background-image: url("{active_background_url}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
    transition: background-image 0.5s ease-in-out, background-color 0.5s ease-in-out;
    background-color: transparent; /* Ensure this doesn't hide the image */
}}

/* Your existing CSS styling below, adjusted for dynamic backgrounds */

/* Existing rule for generic 1g6x8q - keep if it applies to other elements too */
.st-emotion-cache-1g6x8q {{
    background-color: transparent;
    border-radius: 15px;
    box-shadow: none;
    padding: 15px;
    overflow-y: auto;
    margin-bottom: 15px;
    display: flex;
    flex-direction: column;
    # justify-content: flex-end !important;
    # height: 100% !important;
    # min-height: 0 !important;
}}

/* NEW RULE: Add this block for the specific container you identified */
.st-emotion-cache-mc20ew {{
    display: block;
    border-radius: 15px;
    padding: calc(-1px + 1rem);
    height: 460px;
    overflow: auto;
    border: 1px solid rgba(0, 0, 0, 0.8);
}}

#text
div[data-testid="stVerticalBlock"] > div > div.st-emotion-cache-1g6x8q {{
    # justify-content: flex-end !important;
    # height: 100% !important;
    # min-height: 0 !important;
    
}}

div[data-testid="stChatMessage"] {{
    background-color: #FFFFFF;
    border-radius: 10px;
    padding: 25px;
    margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    max-width: 99%;
    word-wrap: break-word;
    margin-top: 40px;
    color: #333;
    font-family: 'Inter', sans-serif;
}}

div[data-testid="stChatMessage"].stChatMessage-user {{
    background-color: #E6F7FF;
    margin-left: auto;
    margin-right: 0;
}}

div[data-testid="stChatMessage"].stChatMessage-assistant {{
    background-color: #FFFFFF;
    margin-right: auto;
    margin-left: 0;
    align-self: flex-start;
}}

div[data-testid="stChatInput"] {{
    background-color: #FFFFFF;
    border-radius: 10px;
    padding: 10px;
    box-shadow: 0 -2px 5px rgba(0,0,0,0.05);
}}

/* Main content block background */
.main .block-container {{
    padding-top: 2rem;
    padding-bottom: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    transition: background-color 0.5s ease-in-out;
    background-color: {main_block_bg_color}; /* Dynamic background */
}}
.main .block-container * {{ /* This will make ALL text inside the main content block white */
    color: white !important;
}}

/* Side/Chat panel background (often st-emotion-cache-vk3304 or similar) */
.st-emotion-cache-vk3304 {{
    background-color: {sidebar_bg_color}; /* Dynamic background */
    transition: background-color 0.5s ease-in-out;
}}



.space-adding {{
    margin-left: auto;
    margin-top: 50px;
}}

.title-tagline-box {{
    background-color: #FFFFFF;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    text-align: center;
    max-width: 450px;
    margin-left: auto;
    margin-top: 450px;
}}

.title-tagline-box h1 {{
    font-size: 2.5em;
    color: #333;
    margin-bottom: 10px;
    font-family: 'Inter', sans-serif;
    text-align: center;
}}
.title-tagline-box p {{
    font-size: 1.5em;
    color: #555;
    line-height: 1.5;
    font-family: 'Inter', sans-serif;
    text-align: center;
}}

body {{
    font-family: 'Inter', sans-serif;
}}

.st-emotion-cache-1fm0v0 {{
    padding-left: 1rem;
    padding-right: 1rem;
}}


.title-result-1 {{
   background-color: #FFFFFF;
    padding: 1px;
    border-radius: 15px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    text-align: center;
    max-width: 1450px;
    margin-bottom: 90px;
}}

.title-result-1 h1 {{
    font-size: 2.0em;
    color: #333;
    margin-bottom: 10px;
    font-family: 'Inter', sans-serif;
    text-align: center;
}}


div[data-testid="stSpinner"] span {{
    font-size: 2.0em !important;
    color: white !important;
    font-family: 'Inter', sans-serif !important;
    text-align: center !important;
    display: block !important;
    width: 100% !important;
}}



.summary-top {{
    background-color: #FFFFFF;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    max-width: 1450px;
    display: flex;
    flex-direction: column;
    margin-bottom: 200px;
    height: 280px;
    margin-top: 50px;
}}

.summary-top h1 {{
   font-size: 1.4em; /* Adjusted to be a bit larger for a main summary title */
    color: #333;
    margin-bottom: 10px; /* Increased margin for better separation */
    font-family: 'Inter', sans-serif;
    word-wrap: break-word;
}}

.summary-top p {{
    font-size: 1.1em;
    color: #555;
    margin-bottom: 5px;
    font-family: 'Inter', sans-serif;
    word-wrap: break-word;
}}
  
        
.summary-top .summary-value {{
    font-size: 0.9em; /* Make it slightly smaller than the 1.2em of the bold label */
    color: #333; /* Make the value text a bit darker/more prominent */
    font-weight: normal; /* Ensure it's not bold by default unless specified */
}}

.summary-top strong {{
    font-weight: bold !important; /* Use !important to override potential conflicts */
    color: #333; /* Ensure bold text is clearly visible */
}}


.location_image {{
    background-color: #FFFFFF;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    max-width: 1450px;
    display: flex;
    flex-direction: column;
}}

.location_image h1 {{
   font-size: 1.4em; /* Adjusted to be a bit larger for a main summary title */
    color: #333;
    margin-bottom: 10px; /* Increased margin for better separation */
    font-family: 'Inter', sans-serif;
    word-wrap: break-word;
    text-align: center !important;
}}

.location_image img {{
   max-width: 100%; /* Image will scale down if larger than container */
   height: auto; /* Maintain aspect ratio */
   border-radius: 8px;
   margin-top: 10px;
   display: block; /* Remove extra space below image */
   margin-left: auto; /* Center image */
   margin-right: auto; /* Center image */
}}




.budget_splitin {{
    background-color: #FFFFFF;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    max-width: 1450px;
    display: flex;
    flex-direction: column;
    height: 100%;
    margin-top:100px;
    margin-bottom: 70px;
}}

.budget_splitin h1{{
    font-size: 1.2em; /* Adjusted to be a bit larger for a main summary title */
    color: #333;
    margin-bottom: 10px; /* Increased margin for better separation */
    font-family: 'Inter', sans-serif;
    word-wrap: break-word;
}}

.budget_splitin p{{
    font-size: 1.1em;
    color: #555;
    margin-bottom: 5px;
    font-family: 'Inter', sans-serif;
    word-wrap: break-word;
}}



.stop-details {{
  background-color: #FFFFFF;
    padding: 30px; /* Increased padding for better visual appeal */
    border-radius: 15px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    max-width: 1350px; /* This max-width might be too wide for columns, consider adjusting */
    display: flex;
    flex-direction: column; /* Stack children vertically */
    height: 100%; /* Ensure cards in columns have consistent height */  
    justify-content: space-between; 
    min-height: 500px;
    max-height: 1500px;
    margin-bottom: 70px;
}}

.stop-details h1  {{
   font-size: 1.1em; /* Adjusted font size for better readability within cards */
    color: #333;
    margin-bottom: 5px;
    font-family: 'Inter', sans-serif;
    word-wrap: break-word; /* Ensure long names wrap */
}}

.stop-details p {{
   font-size: 1.1em; /* Adjusted font size for better readability within cards */
    color: #555; /* Slightly darker color for body text */
    margin-bottom: 5px;
    font-family: 'Inter', sans-serif;
    word-wrap: break-word; /* Ensure long text wraps */
}}


iframe[title="streamlit_folium.st_folium"] {{
    width: 100% !important;  /* Make the iframe fill the width of its Streamlit container */
    height: 600px !important; /* Force the iframe's height to 600px, matching your st_folium call */
    display: block !important; /* Ensure it behaves like a block element */
    margin: 0 !important;     /* Remove any default margins */
    padding: 0 !important;    /* Remove any default padding */
}}


.nocity_response {{
    background-color: #FFFFFF;
    padding: 10px;
    border-radius: 15px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    height: 100%;
    margin-bottom: 70px;
    max-width: 740px;
    text-align: center; /* Centers the text inside the bubble */
    margin-left: auto;   /* Centers the bubble horizontally */
    margin-right: auto;  /* Centers the bubble horizontally */
}}

.nocity_response p{{
    font-size: 1.1em;
    color: #555;
    margin-bottom: 5px;
    font-family: 'Inter', sans-serif;
    word-wrap: break-word;
}}

</style>
"""

# Apply custom CSS
st.markdown(custom_css, unsafe_allow_html=True)


import requests

GOOGLE_API_KEY = st.secrets.get("Maps_api_key", None)

# --- Google API Helper Functions (Keep these) ---


def format_duration(seconds):
    """Formats duration from seconds to a human-readable string (e.g., '1 hour 30 mins')."""
    if seconds is None:
        return "N/A"
    minutes = seconds // 60
    hours = minutes // 60
    minutes = minutes % 60
    if hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''} {minutes} min{'s' if minutes > 1 else ''}"
    return f"{minutes} min{'s' if minutes > 1 else ''}"

def get_data_from_json(file_path):
    """Loads data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Mock data file not found: {file_path}")
        return None
    except json.JSONDecodeError:
        st.error(f"Error decoding JSON from file: {file_path}")
        return None


def geocode_city(city_name):
    """
    Geocodes a city name to its latitude, longitude, and **country code**.
    MODIFIED: Now returns (lat, lng, country_code).
    """
    if not GOOGLE_API_KEY:
        st.error("Google API key is not set for geocoding!")
        return None, None, None # MODIFIED: Return 3 values

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": city_name, "key": GOOGLE_API_KEY}

    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = resp.json()

        if data.get("status") == "OK" and data.get("results"):
            result = data["results"][0]
            loc = result["geometry"]["location"]

            # NEW: Extract country code from address components
            country_code = None
            for component in result.get("address_components", []):
                if "country" in component.get("types", []):
                    country_code = component.get("short_name") # This is the 2-letter ISO code (e.g., CA, US)
                    break

            if country_code:
                print(f"DEBUG: Geocoded '{city_name}': Lat={loc['lat']}, Lng={loc['lng']}, Country Code={country_code}")
                return loc["lat"], loc["lng"], country_code
            else:
                st.warning(f"Could not determine country code for '{city_name}'. Returning lat/lng but no country code.")
                return loc["lat"], loc["lng"], None # Return lat/lng even if country code is missing
        else:
            #st.error(f"Geocode API returned non-OK status: {data.get('status')}. Message: {data.get('error_message', 'No message.')}")
            return None, None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Network or HTTP error during Geocoding API call: {e}")
        return None, None, None
    except json.JSONDecodeError as e: # MODIFIED: Catch specific JSONDecodeError
        st.error(f"Error decoding JSON from Geocoding API response: {e}. Response text: {resp.text}")
        return None, None, None
    except Exception as e:
        st.error(f"An unexpected error occurred during Geocoding API call: {e}")
        return None, None, None


def get_places(lat, lng, place_type): # MODIFIED: Removed 'country_code=None' parameter
    """
    Fetches places using Google Places API's Nearby Search.
    This function returns all raw results within the specified radius;
    country-specific filtering is handled by the calling function (get_initial_places).
    """
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY is not set or empty for Places API!")
        return []

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": 10000,  # 10 km radius
        "type": place_type,
        "key": GOOGLE_API_KEY
    }

    try:
        resp = requests.get(url, params=params)

        # --- KEEP THESE DEBUGGING PRINTS! They are essential for diagnosis if problems persist ---
        print(f"\n--- Raw API Response Text for type '{place_type}' ---")
        print(f"HTTP Status Code: {resp.status_code}")
        print(f"Response URL: {resp.url}") # Show the actual URL sent
        print(resp.text)
        print("-----------------------------------")
        # --- END OF RAW DEBUGGING ---

        resp.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        data = resp.json()

        # --- KEEP THESE DEBUGGING PRINTS! ---
        print(f"\n--- Parsed API Response JSON for type '{place_type}' ---")
        print(json.dumps(data, indent=2))
        print("-----------------------------------")
        # --- END OF PARSED DEBUGGING ---

        if data.get("status") == "OK":
            raw_results = data.get("results", [])
            print(f"DEBUG: get_places RAW results for type '{place_type}' ({len(raw_results)} found).")
            return raw_results # This function returns all raw results; filtering is done in get_initial_places
        else:
            print(f"Places API returned non-OK status: {data.get('status')}")
            if data.get('error_message'):
                print(f"API Error Message: {data.get('error_message')}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Network or HTTP error during Places API call: {e}")
        return []
    except json.JSONDecodeError as e: # MODIFIED: Catch specific JSONDecodeError
        print(f"Error decoding JSON from Places API response: {e}. Response text: {resp.text}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred during Places API call: {e}")
        return []

def get_specific_place_by_name(query, city_lat, city_lng, city_name):

    if not GOOGLE_API_KEY:
        st.error("Google API key is not set!")
        return None

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    search_query = f"{query} {city_name}" # Bias the search

    params = {
        "query": search_query,
        "location": f"{city_lat},{city_lng}", # Bias results to the city's location
        "radius": 10000, # Use same radius as nearby search for consistency
        "key": GOOGLE_API_KEY
    }

    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") == "OK" and data.get("results"):
            return data["results"][0]
        else:
            st.warning(f"Could not find specific place '{query}': {data.get('status')}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network or API error when searching for '{query}': {e}")
        return None

# 1. Keep this helper function as is (or with minor adjustments if needed)


def get_place_photo_url(photo_reference, max_width=400):
    """
    Fetches the direct URL for a Google Places photo using its photo_reference.
    """
    print(f"\nDEBUG: Entering get_place_photo_url for photo_reference: {photo_reference[:30]}...") # Print first 30 chars
    if not photo_reference:
        print("DEBUG: photo_reference is None or empty. Returning None.")
        return None
    if not GOOGLE_API_KEY:
        print("DEBUG: GOOGLE_API_KEY is not set or empty for Photos API! Returning None.")
        return None

    url = "https://maps.googleapis.com/maps/api/place/photo"
    params = {
        "photo_reference": photo_reference,
        "maxwidth": max_width,
        "key": GOOGLE_API_KEY
    }
    print(f"DEBUG: Photos API request URL (params): {url}?{requests.compat.urlencode(params)}")

    try:
        resp = requests.get(url, params=params, allow_redirects=True)
        resp.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        final_image_url = resp.url
        print(f"DEBUG: Photos API successful. Final image URL: {final_image_url}")
        return final_image_url

    except requests.exceptions.RequestException as e:
        print(f"DEBUG ERROR: Network or HTTP error during Places Photos API call: {e}")
        print(f"DEBUG ERROR: Response status code: {resp.status_code if 'resp' in locals() else 'N/A'}")
        print(f"DEBUG ERROR: Response text: {resp.text if 'resp' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"DEBUG ERROR: An unexpected error occurred during Places Photos API call: {e}")
        return None



import requests # Ensure requests is imported at the top of your script
import json     # Ensure json is imported at the top of your script
import streamlit as st # Ensure streamlit is imported

# Assume GOOGLE_API_KEY is defined globally or passed securely
# For example:
# GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"] # Recommended for Streamlit Cloud
# Or if it's a global variable:
# GOOGLE_API_KEY = "YOUR_ACTUAL_GOOGLE_API_KEY" # Replace with your key

def get_place_id_from_name(place_name, api_key):
    """
    Fetches the Place ID for a given place name using Google Places Find Place API.
    """
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": place_name,
        "inputtype": "textquery",
        "fields": "place_id", # Only request place_id to save on API costs
        "key": api_key
    }
    print(f"DEBUG: Calling Find Place API for '{place_name}'...")
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = resp.json()

        print(f"DEBUG: Find Place API response for '{place_name}':\n{json.dumps(data, indent=2)}")

        if data.get("status") == "OK" and data.get("candidates"):
            place_id = data["candidates"][0]["place_id"]
            print(f"DEBUG: Found Place ID for '{place_name}': {place_id}")
            return place_id
        else:
            print(f"DEBUG: Could not find Place ID for '{place_name}'. Status: {data.get('status')}, Error: {data.get('error_message', 'N/A')}")
            # Optionally, you can add a Streamlit warning here if you want the user to know
            # st.warning(f"Could not find exact Google Place ID for {place_name}.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"DEBUG ERROR: Network or API error finding Place ID for '{place_name}': {e}")
        # st.error(f"Error connecting to Google Places API to find {place_name}.") # Optional user error
        return None
    except json.JSONDecodeError as e:
        print(f"DEBUG ERROR: Error decoding JSON from Find Place API response for '{place_name}': {e}. Response text: {resp.text}")
        return None
    except Exception as e:
        print(f"DEBUG ERROR: An unexpected error occurred while finding Place ID for '{place_name}': {e}")
        return None

# Add the get_place_details_with_photos function as well if you haven't already:
def get_place_details_with_photos(place_id):
    """
    Fetches details for a specific place, specifically requesting 'photos'.
    """
    url = "https://maps.googleapis.com/maps/api/place/details/json"

    if not GOOGLE_API_KEY:
        print("ERROR: Google API key not found for Place Details API (photos).")
        return None

    params = {
        "place_id": place_id,
        "fields": "photos", # ONLY request the 'photos' field to save on costs if you only need photos
        "key": GOOGLE_API_KEY
    }

    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        print(f"DEBUG: Place Details API (photos) response for {place_id}:\n{json.dumps(data, indent=2)}")

        if data.get("status") == "OK" and "result" in data:
            return data["result"] # Return the 'result' dictionary, which will contain 'photos' if available
        else:
            print(f"DEBUG: Place Details API (photos) call for place_id {place_id}: Status '{data.get('status')}'. Error message: {data.get('error_message', 'No message.')}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"DEBUG ERROR: Network or API error when fetching photos for {place_id}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"DEBUG ERROR: Error decoding JSON from Place Details API response (photos): {e}. Response text: {resp.text}")
        return None
    except Exception as e:
        print(f"DEBUG ERROR: An unexpected error occurred when fetching photos for {place_id}: {e}")
        return None

def get_place_details_with_price_level(place_id):
    """
    Fetches the price_level for a specific place using Place Details API.
    Note: 'price_level' is typically an 'Enterprise' SKU field.
    """
    url = "https://maps.googleapis.com/maps/api/place/details/json"

    if not GOOGLE_API_KEY:
        st.error("Google API key not found. Please set it in your Streamlit secrets or environment variables.")
        return None

    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,geometry,website,international_phone_number,price_level",
        "key": GOOGLE_API_KEY
    }

    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        # Debug print to see the *entire* response from Place Details API for this place_id
        # This will confirm if 'result' is missing or if 'price_level' is simply not there
        import json
        print(f"DEBUG: Full Place Details API response for {place_id}:\n{json.dumps(data, indent=2)}")

        # Condition 1: Check if the API call status is 'OK' AND a 'result' object exists
        if data.get("status") == "OK" and "result" in data:
            result_data = data["result"] # Get the result dictionary
            price_level = result_data.get("price_level") # Safely get price_level from result

            if price_level is None:
                # This is the expected case for places without a defined price_level
                # Log this to console for debugging, but do NOT show a Streamlit warning
                print(f"DEBUG: price_level is NULL for place_id {place_id}. This is expected for many museums/attractions that don't have a price_level in Google Places.")

            return price_level # Returns the actual price_level (0-4) or None

        else:
            # This 'else' block now specifically catches cases where status is NOT 'OK'
            # OR where the 'result' key is completely missing from the API response (though status 'OK' usually implies 'result' exists).
            st.warning(f"Place Details API call for place_id {place_id}: Status '{data.get('status')}'. No 'result' object found or API error preventing details.")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"Network or API error when fetching price_level for {place_id}: {e}")
        return None
def get_distance_matrix(origins, destinations, mode, api_key, use_live_api, mock_walking_path, mock_transit_path):

    print(f"DEBUG: DM API CALL - Mode: {mode}")
    print(f"DEBUG: DM API CALL - Origins being sent: {origins}")
    print(f"DEBUG: DM API CALL - Destinations being sent: {destinations}")
    print(f"DEBUG: DM API CALL - API Key used (first 5 chars): {api_key[:5]}...") # Good to check key is being passed

    if use_live_api:
        base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": "|".join(origins),
            "destinations": "|".join(destinations),
            "mode": mode,
            "key": api_key
        }

        if mode == "transit":
            params["departure_time"] = int(datetime.datetime.now().timestamp())

        # --- ADD THESE DEBUG PRINTS HERE (Before the requests.get call) ---
        print(f"DEBUG: DM API Request URL: {base_url}")
        print(f"DEBUG: DM API Request Params: {params}")

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json() # Capture the JSON response here

            # --- ADD THIS DEBUG PRINT HERE (After getting the JSON response) ---
            print(f"DEBUG: Raw Distance Matrix API Response: {json.dumps(data, indent=2)}")

            # Check the status from the API response
            if data.get("status") != "OK":
                error_message = data.get("error_message", "No specific error message provided by API.")
                print(f"ERROR: Distance Matrix API returned status '{data.get('status')}'. Error message: {error_message}")
                st.error(f"Distance Matrix API Error: {error_message} (Status: {data.get('status')})")
                return None

            return data # Return the data if status is OK

        except requests.exceptions.RequestException as e:
            st.error(f"Error calling live Distance Matrix API for mode '{mode}': {e}")
            print(f"ERROR: Requests exception during DM API call for mode '{mode}': {e}") # Add to console
            return None
    else: # Load from mock files
        print("DEBUG: use_live_api is False. Attempting to load mock data.") # Indicate mock data path taken
        mock_file_path = None
        if mode == "walking":
            mock_file_path = mock_walking_path
        elif mode == "transit":
            mock_file_path = mock_transit_path
        else:
            st.error(f"Unsupported mode '{mode}' for mock data.")
            print(f"ERROR: Unsupported mode '{mode}' for mock data path.") # Add to console
            return None

        if mock_file_path and os.path.exists(mock_file_path):
            try:
                with open(mock_file_path, 'r') as f:
                    mock_data = json.load(f)
                    print(f"DEBUG: Successfully loaded mock data from: {mock_file_path}") # Confirm mock load
                    return mock_data
            except json.JSONDecodeError:
                st.error(f"Error decoding JSON from mock file: {mock_file_path}. Check file format.")
                print(f"ERROR: JSONDecodeError for mock file: {mock_file_path}.") # Add to console
                return None
            except Exception as e:
                st.error(f"Error reading mock file {mock_file_path}: {e}")
                print(f"ERROR: Exception reading mock file {mock_file_path}: {e}") # Add to console
                return None
        else:
            st.error(f"Mock file not found for mode '{mode}': {mock_file_path}")
            print(f"ERROR: Mock file not found for mode '{mode}': {mock_file_path}") # Add to console
            return None


# your_app.py (Add this block)

# --- NEW FUNCTION: Get Detailed Directions ---
def get_directions_details(origin_place_id, destination_place_id, travel_mode, api_key, use_live, mock_directions_path, origin_name="", destination_name=""):
    """
    Fetches detailed directions (steps) from Google Directions API or mock data.
    Returns a list of step dictionaries.
    """
    if use_live:
        base_url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": f"place_id:{origin_place_id}",
            "destination": f"place_id:{destination_place_id}",
            "mode": travel_mode,
            "key": api_key
        }
        if travel_mode == "transit":
            params["departure_time"] = "now" # Required for transit directions

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            directions_data = response.json()
            if directions_data and directions_data['status'] == 'OK' and directions_data['routes']:
                # Return the steps from the first leg of the first route
                return directions_data['routes'][0]['legs'][0]['steps']
            else:
                st.warning(f"No directions found for {origin_name} to {destination_name} via {travel_mode} (Live API). Status: {directions_data.get('status')}")
                return []
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching directions from live API for {origin_name} to {destination_name} ({travel_mode}): {e}")
            return []
    else:
        # Use mock data
        mock_data = get_data_from_json(mock_directions_path)
        if mock_data:
            # Create a key for lookup in the mock JSON
            mock_key = f"{origin_name}-{destination_name}-{travel_mode}"
            if mock_key in mock_data and mock_data[mock_key] and mock_data[mock_key][0]['legs']:
                return mock_data[mock_key][0]['legs'][0]['steps']
            else:
                #st.warning(f"No mock directions found for key: {mock_key}")
                return []
        return []

# --- NEW FUNCTION: Format Detailed Instructions ---
def format_instructions(steps):
    """
    Formats a list of steps from Directions API into a human-readable instruction string.
    Handles both walking and transit steps.
    """
    if not steps:
        return "No detailed instructions available."

    instructions_list = []
    for i, step in enumerate(steps):
        # Clean up HTML tags for display in Streamlit
        html_instructions = step.get('html_instructions', '').replace('<b>', '**').replace('</b>', '**').replace('<div style="font-size:0.9em">', ' (').replace('</div>', ')')

        if step['travel_mode'] == 'WALKING':
            instructions_list.append(f"{i+1}. Walk: {html_instructions}")
        elif step['travel_mode'] == 'TRANSIT':
            transit_details = step.get('transit_details')
            if transit_details:
                line_name = transit_details['line'].get('name', 'Unknown Line')
                departure_stop = transit_details['departure_stop'].get('name', 'Unknown Stop')
                arrival_stop = transit_details['arrival_stop'].get('name', 'Unknown Stop')
                headsign = transit_details.get('headsign', '')
                num_stops = transit_details.get('num_stops')

                stops_info = f"({num_stops} stop{'s' if num_stops != 1 else ''})" if num_stops is not None else ""

                if line_name and departure_stop and arrival_stop:
                    if headsign:
                        instructions_list.append(
                            f"{i+1}. Take {line_name} towards {headsign} from {departure_stop} to {arrival_stop} {stops_info}"
                        )
                    else:
                        instructions_list.append(
                            f"{i+1}. Take {line_name} from {departure_stop} to {arrival_stop} {stops_info}"
                        )
                else:
                    instructions_list.append(f"{i+1}. Transit: {html_instructions}")
            else:
                instructions_list.append(f"{i+1}. Transit: {html_instructions}")
        else: # For other modes like DRIVING, BICYCLING if you ever add them
            instructions_list.append(f"{i+1}. {step['travel_mode'].capitalize()}: {html_instructions}")
    return "\n\n".join(instructions_list)


def create_time_map(places_results, walking_matrix, transit_matrix): # REMOVED driving_matrix from parameters
    """
    Creates a time map (adjacency matrix) for locations, choosing travel mode
    based on the following preference:
    1. Walking if duration is <= 20 minutes (1200 seconds) AND status is OK.
    2. Transit if available (status is OK).
    3. Driving (cab) if walking is too long/unavailable AND transit is unavailable.
       For mock testing with only 2 files, driving duration will be estimated.

    Returns both the time map and a mode map indicating the chosen transport for each segment.
    """
    # Updated check for missing matrices - now only walking and transit
    if not all([places_results, walking_matrix, transit_matrix]):
        st.error("Missing one or more required matrices (places_results, walking, or transit) to create time map.")
        return None, None

    num_places = len(places_results)
    time_map = [[0] * num_places for _ in range(num_places)]
    mode_map = [[''] * num_places for _ in range(num_places)]

    WALKING_PREFERENCE_THRESHOLD = 20 * 60 # 1200 seconds (20 minutes)
    # Define a factor for estimating driving time from walking time
    # e.g., driving is 4x faster than walking, so duration is 1/4th.
    DRIVING_WALKING_TIME_FACTOR = 0.25
    MIN_DRIVING_TIME_SECONDS = 5 * 60 # Minimum estimated driving time (5 minutes)

    for i in range(num_places):
        for j in range(num_places):
            if i == j: # Travel time from a place to itself is 0
                time_map[i][j] = 0
                mode_map[i][j] = 'start/end'
                continue

            origin_name = places_results[i]['name']
            destination_name = places_results[j]['name']

            # --- Extract data from matrices safely ---
            walking_element = walking_matrix["rows"][i]["elements"][j]
            transit_element = transit_matrix["rows"][i]["elements"][j]
            # REMOVED: driving_element = driving_matrix["rows"][i]["elements"][j]

            # Initialize durations to infinity
            walk_duration = float('inf')
            transit_duration = float('inf')
            # drive_duration is not directly from a matrix anymore, will be estimated

            # Get walking duration if status is OK
            if walking_element["status"] == "OK" and "duration" in walking_element:
                walk_duration = walking_element["duration"]["value"]
            # Optional debug print for walking status (keep commented unless actively debugging)
            # else:
            #     print(f"DEBUG: Walking status not OK for {origin_name} to {destination_name}: {walking_element.get('status', 'N/A')}")

            # Get transit duration if status is OK
            if transit_element["status"] == "OK" and "duration" in transit_element:
                transit_duration = transit_element["duration"]["value"]
            # Optional debug print for transit status (keep commented unless actively debugging)
            # elif transit_element["status"] == "ZERO_RESULTS":
            #     print(f"DEBUG: Transit ZERO_RESULTS for {origin_name} to {destination_name}.")
            # else:
            #     print(f"DEBUG: Transit status not OK for {origin_name} to {destination_name}: {transit_element.get('status', 'N/A')}")


            # --- APPLY YOUR PREFERRED MODE LOGIC ---
            chosen_time = float('inf')
            chosen_mode = 'unroutable' # Default if no valid options are found

            # Preference 1: Walking if less than 20 minutes
            if walk_duration <= WALKING_PREFERENCE_THRESHOLD:
                chosen_time = walk_duration
                chosen_mode = 'walking'
            # Preference 2: Transit if walking is not preferred (too long or unavailable) AND transit is available
            elif transit_duration != float('inf'): # This means transit status was OK and duration was present
                chosen_time = transit_duration
                chosen_mode = 'transit'
            # Preference 3: Driving (Cab) if walking is not preferred AND transit is unavailable
            # We now estimate driving time here as there's no driving_matrix
            elif walk_duration != float('inf'): # If walking was at least possible (even if too long for preference)
                # Estimate driving time as a fraction of walking time, with a minimum
                estimated_drive_time = int(walk_duration * DRIVING_WALKING_TIME_FACTOR)
                chosen_time = max(MIN_DRIVING_TIME_SECONDS, estimated_drive_time) # Ensure a minimum driving time
                chosen_mode = 'driving' # Representing a cab
            else:
                # If even walking was unavailable (e.g., different continents in real API)
                chosen_time = float('inf')
                chosen_mode = 'unroutable'


            time_map[i][j] = chosen_time
            mode_map[i][j] = chosen_mode

            if chosen_time == float('inf') and i != j:
                st.warning(f"Could not find a valid route for {origin_name} to {destination_name} using walking (under 20 min), transit, or estimated driving. This segment might be unroutable.")

    return time_map, mode_map

def find_optimal_route_tsp(places_results, time_map, mode_map):
    """
    Finds a near-optimal route visiting all places using a Nearest Neighbor heuristic.
    Returns the optimal route names, total time (including activities),
    and the sequence of travel modes.
    """
    if not places_results or not time_map or not mode_map:
        return [], 0, [] # Return empty lists/0 for no data

    num_places = len(places_results)
    if num_places == 0:
        return [], 0, []
    if num_places == 1:
        # For a single place, total time is just its activity duration.
        # No travel modes needed.
        return [places_results[0]['name']], places_results[0].get('activity_duration_seconds', 0), []


    min_total_time = float('inf')
    optimal_route_indices = None
    optimal_travel_modes_sequence = [] # Sequence of modes for segments

    # Use the Nearest Neighbor TSP-like approach
    for start_node_idx in range(num_places):
        current_route_indices = [start_node_idx]
        current_total_time = 0
        current_travel_modes = [] # Modes for segments of the current route being built
        visited = {start_node_idx} # Use indices for visited set

        while len(current_route_indices) < num_places:
            last_node_idx = current_route_indices[-1]

            next_node_idx = None
            min_time_to_next = float('inf')
            chosen_mode_for_segment = None

            for next_candidate_idx in range(num_places):
                if next_candidate_idx not in visited:
                    travel_time = time_map[last_node_idx][next_candidate_idx]
                    travel_mode = mode_map[last_node_idx][next_candidate_idx]

                    if travel_time < min_time_to_next:
                        min_time_to_next = travel_time
                        next_node_idx = next_candidate_idx
                        chosen_mode_for_segment = travel_mode

            if next_node_idx is not None:
                current_route_indices.append(next_node_idx)
                current_total_time += min_time_to_next
                current_travel_modes.append(chosen_mode_for_segment)
                visited.add(next_node_idx)
            else:
                # This indicates an issue (e.g., unreachable place), break early
                current_total_time = float('inf') # Mark as invalid route
                break # Exit while loop if no next node found

        # If a complete route was found and it's better than the current best
        if len(current_route_indices) == num_places and current_total_time < min_total_time:
            min_total_time = current_total_time
            optimal_route_indices = current_route_indices
            optimal_travel_modes_sequence = current_travel_modes # Store the sequence

    optimal_route_names = [places_results[idx]['name'] for idx in optimal_route_indices] if optimal_route_indices else []

    # Add activity durations to the total travel time
    final_total_time_with_activities = min_total_time
    if optimal_route_indices:
        for place_idx in optimal_route_indices:
            place_data = places_results[place_idx]
            final_total_time_with_activities += place_data.get('activity_duration_seconds', 0)

    return optimal_route_names, final_total_time_with_activities, optimal_travel_modes_sequence


def get_initial_places(trip_data, use_live_api, total_limit, only_free_places=False): # IMPORTANT: only_free_places parameter added here
    """
    Fetches the initial set of places based on selected types, with a limit and deduplication.
    Now filters places by the geocoded country, can optionally filter for free places,
    and guarantees at least one place from each selected type if available.
    """
    mock_file_path = Path(project_root) / "ui" / "apidata" / "mock.json"

    if use_live_api:
        city = trip_data.get("destination_city", "")
        print(f"DEBUG: 'city' : {city}")
        place_types = trip_data.get("place_type", [])
        print(f"DEBUG: 'place_types' value received by get_initial_places: {place_types}")

        lat, lng, geocoded_country_code = geocode_city(city)
        if lat is None or lng is None or geocoded_country_code is None:
            #st.error("Could not geocode city or determine its country. Cannot fetch places.")
            return []

        # Store all candidate places here after initial filtering (country, lodging, free)
        all_candidate_places = []

        # Keep track of which types we've managed to guarantee at least one place for
        types_with_guaranteed_place = set()

        for ptype in place_types:
            raw_nearby_results = get_places(lat, lng, ptype)

            # Apply country and lodging filters
            current_type_filtered_by_country_lodging = []
            if geocoded_country_code:
                target_country_code_upper = geocoded_country_code.upper()

                country_aliases = {
                    "US": ["USA", "UNITED STATES OF AMERICA"],
                    "CA": ["CANADA"],
                    "GB": ["UNITED KINGDOM", "UK", "ENGLAND", "SCOTLAND", "WALES", "NORTHERN IRELAND"],
                    # Add any other countries as needed
                }

                allowed_country_strings_lower = [target_country_code_upper.lower()]
                if target_country_code_upper in country_aliases:
                    allowed_country_strings_lower.extend([alias.lower() for alias in country_aliases[target_country_code_upper]])

                for place in raw_nearby_results:
                    place_country_matches = False

                    if 'plus_code' in place and 'compound_code' in place['plus_code']:
                        compound_code_lower = place['plus_code']['compound_code'].lower()
                        for allowed_string in allowed_country_strings_lower:
                            if allowed_string in compound_code_lower:
                                place_country_matches = True
                                break

                    if not place_country_matches and 'formatted_address' in place:
                        formatted_address_lower = place['formatted_address'].lower()
                        for allowed_string in allowed_country_strings_lower:
                            if f" {allowed_string}" in formatted_address_lower or f",{allowed_string}" in formatted_address_lower or formatted_address_lower.endswith(allowed_string):
                                place_country_matches = True
                                break

                    if not place_country_matches and 'address_components' in place:
                        for component in place['address_components']:
                            if 'country' in component.get('types', []):
                                if component.get('short_name', '').upper() == target_country_code_upper:
                                    place_country_matches = True
                                    break
                                if component.get('long_name', '').lower() in allowed_country_strings_lower:
                                    place_country_matches = True
                                    break

                    is_lodging = "lodging" in place.get("types", [])

                    if place_country_matches and not is_lodging:
                        current_type_filtered_by_country_lodging.append(place)
                    else:
                        place_name = place.get('name', 'Unnamed Place')
                        place_address = place.get('formatted_address', place.get('vicinity', 'No address'))
                        reason_filtered = []
                        if not place_country_matches:
                            reason_filtered.append(f"country '{geocoded_country_code}' mismatch")
                        if is_lodging:
                            reason_filtered.append("is lodging")
                        print(f"DEBUG: Filtered out '{place_name}' (Address: '{place_address}') - Reason: {', '.join(reason_filtered)}. Types: {place.get('types', [])}")

            else: # If no country code, no country filter
                print(f"DEBUG: No geocoded_country_code available for filtering. Returning all {len(raw_nearby_results)} raw results for type '{ptype}'.")
                current_type_filtered_by_country_lodging = raw_nearby_results

            print(f"DEBUG: Initial filter for type '{ptype}' (Country/Lodging): {len(current_type_filtered_by_country_lodging)} remaining.")

            # Apply 'only_free_places' filter to the current batch
            final_filtered_for_type = []
            for place in current_type_filtered_by_country_lodging:
                if only_free_places:
                    place_id = place.get("place_id")
                    if place_id:
                        price_level = get_place_details_with_price_level(place_id)
                        if price_level == 0:
                            place['price_level'] = price_level # Store for later
                            final_filtered_for_type.append(place)
                        else:
                            print(f"DEBUG: Filtered out '{place.get('name', 'Unnamed Place')}' - Not free (Price Level: {price_level})")
                    else:
                        print(f"DEBUG: Skipping place without place_id for free filter: {place.get('name', 'Unnamed Place')}")
                else:
                    final_filtered_for_type.append(place)

            print(f"DEBUG: Final filtered results for type '{ptype}' ({len(final_filtered_for_type)} remaining).")

            # Add these finally filtered places to the overall candidate pool
            all_candidate_places.extend(final_filtered_for_type)

        # --- Now, build the final 'final_itinerary_places' list, guaranteeing one from each type ---
        final_itinerary_places = []
        added_place_ids = set() # To prevent duplicates in the final list

        # First Pass: Guarantee at least one place from each requested type
        for ptype in place_types:
            if ptype not in types_with_guaranteed_place: # Only try to guarantee if not already done for this type
                found_for_type = False
                # Iterate through all candidates to find one for this type
                for place in all_candidate_places:
                    # Check if this place matches the current type AND hasn't been added yet
                    if ptype in place.get('types', []) and place.get('place_id') not in added_place_ids:
                        # Ensure we fetch full details if not already done (for activity_duration)
                        if 'activity_duration_seconds' not in place: # Only fetch if not already populated
                            place_types_from_api = place.get('types', [])
                            place['activity_duration_seconds'] = get_estimated_activity_duration(place_types_from_api)
                            # Ensure entry_fee is set based on price_level (which should be on place if free filter active)
                            place['entry_fee'] = get_entry_fee(place.get('price_level'))

                        final_itinerary_places.append(place)
                        added_place_ids.add(place.get('place_id'))
                        types_with_guaranteed_place.add(ptype)
                        found_for_type = True
                        print(f"DEBUG: Guaranteed 1 for type '{ptype}': {place.get('name')}")
                        break # Move to the next type, as we've guaranteed one for this type
                if not found_for_type:
                    print(f"DEBUG: Could not guarantee a place for type '{ptype}'.")

        # Second Pass: Fill the remaining spots up to total_limit with other available candidates
        for place in all_candidate_places:
            if len(final_itinerary_places) >= total_limit:
                break # Reached total_limit, no need to add more

            place_id = place.get("place_id")
            # Add place if it's not a duplicate and we still need more places
            if place_id and place_id not in added_place_ids:
                # Ensure details are fully populated before adding
                if 'activity_duration_seconds' not in place: # Only fetch if not already populated
                    place_types_from_api = place.get('types', [])
                    place['activity_duration_seconds'] = get_estimated_activity_duration(place_types_from_api)
                    place['entry_fee'] = get_entry_fee(place.get('price_level'))

                final_itinerary_places.append(place)
                added_place_ids.add(place_id)
                print(f"DEBUG: Added fill-in place: {place.get('name')}")

        print(f"DEBUG: Final list of places for itinerary before return: {len(final_itinerary_places)} places.")
        return final_itinerary_places[:total_limit] # Final cap to ensure exact limit is met if guarantee + fill exceeded it (unlikely but safe)

    # Mock data path - This section does not require country filtering as mock data should be controlled
    else:
        # NOTE: For mock data, the guarantee logic is not implemented in this mock section.
        # If you need to test the guarantee logic with mock data, you'd need to
        # implement a similar two-pass system within this 'else' block as well.
        if os.path.exists(mock_file_path):
            with open(mock_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            mock_places_limited = []
            added_mock_ids = set()

            if isinstance(data, dict) and "places" in data:
                places_to_process = data["places"]
            elif isinstance(data, list):
                places_to_process = data
            else:
                st.error(f"Mock data format incorrect in {mock_file_path}. Expected a list or dict with 'places' key.")
                return []

            for place in places_to_process:
                if len(mock_places_limited) < total_limit:
                    place_id = place.get("place_id")
                    if place_id and place_id not in added_mock_ids:
                        place_price_level = place.get('price_level', 1) # Default to inexpensive
                        # If 'only_free_places' was passed, mock data should also respect it
                        # This part assumes 'only_free_places' might be true for mock testing too
                        if only_free_places and place_price_level != 0:
                            print(f"DEBUG: Skipping mock place '{place.get('name')}' as it's not free for free filter.")
                            continue

                        place['entry_fee'] = get_entry_fee(place_price_level)
                        place['activity_duration_seconds'] = place.get('activity_duration_seconds', 1.5 * 3600) # Use value from mock.json, with 1.5h fallback
                        place['price_level'] = place_price_level # Store price_level for consistency
                        mock_places_limited.append(place)
                        added_mock_ids.add(place_id)
                else:
                    break
            return mock_places_limited
        else:
            st.error(f"Mock data file not found at {mock_file_path}")
            return []

# --- NEW FUNCTION: Get Place Display Details ---
def get_place_display_details(places_list):
    """
    Extracts and formats display-ready details (name, types, rating) for a list of places.
    Assumes places_list contains dictionaries with 'name', 'types', 'rating', 'user_ratings_total'.
    """
    display_details = []
    for i, place_data in enumerate(places_list):
        place_name = place_data.get('name', 'N/A')
        place_types = place_data.get('types', [])
        place_rating = place_data.get('rating')
        user_ratings = place_data.get('user_ratings_total')

        # Format types nicely (e.g., "Tourist Attraction, Museum")
        formatted_types = [t.replace('_', ' ').title() for t in place_types]
        types_str = ", ".join(formatted_types) if formatted_types else "N/A"

        # Format rating string
        rating_str = "N/A"
        if place_rating is not None and user_ratings is not None:
            rating_str = f"{place_rating} ⭐ ({user_ratings:,} reviews)" # Add comma for readability

        display_details.append({
            "stop_number": i + 1,
            "name": place_name,
            "types": types_str,
            "rating_info": rating_str
        })
    return display_details

# --- END NEW FUNCTION ---


# Add this function somewhere globally in your script, e.g., near format_duration, etc.
def get_estimated_activity_duration(place_types):
    """
    Estimates an activity duration in seconds based on place types.
    You can customize these durations based on your research or intuition.
    """
    # Convert all types to lowercase for consistent matching
    place_types = [t.lower() for t in place_types]

    if "museum" in place_types or "art_gallery" in place_types:
        return 1 * 3600
    elif "tourist_attraction" in place_types:
        return 1.5 * 3600
    elif "park" in place_types or "garden" in place_types:
        return 1 * 3600
    elif "restaurant" in place_types or "cafe" in place_types or "food" in place_types:
        return 0.5 * 3600
    elif "church" in place_types or "synagogue" in place_types or "mosque" in place_types or "hindu_temple" in place_types:
        return 0.5 * 3600
    elif "landmark" in place_types or "point_of_interest" in place_types:
        # A generic point of interest could be quick or longer. 1 hour is a safe bet.
        return 0.75 * 3600
    elif "shopping_mall" in place_types or "store" in place_types:
        return 1 * 3600
    elif "historic_site" in place_types or "store" in place_types:
        return 1 * 3600
    else:
        # Fallback for any unknown types
        return 1 * 3600


def add_specific_place_to_itinerary(specific_place_query, current_places, trip_data, use_live_api, max_total_places=9): # max_total_places is now 9
    """
    Adds a specific place to an existing list of places, fetching only that one.
    """
    if not specific_place_query:
        st.warning("Please enter a place name to add.")
        return current_places

    if len(current_places) >= max_total_places:
        st.warning(f"Your itinerary already has {len(current_places)} places (max {max_total_places}). Cannot add more.")
        return current_places

    city = trip_data.get("destination_city", "")
    city_lat, city_lng = geocode_city(city)
    if city_lat is None or city_lng is None:
        st.error(f"Could not geocode city: {city}")
        return current_places

    if use_live_api:
        if not GOOGLE_API_KEY: # ADDED: API key check for live mode
            st.error("Google API key is not set for live API calls!")
            return current_places

        with st.spinner(f"Adding '{specific_place_query}' to your itinerary..."):
            specific_place = get_specific_place_by_name(specific_place_query, city_lat, city_lng, city)
            if specific_place:
                existing_place_ids = {p.get("place_id") for p in current_places if p.get("place_id")}
                if specific_place.get("place_id") not in existing_place_ids:
                    price_level = get_place_details_with_price_level(specific_place.get("place_id"))
                    specific_place['entry_fee'] = get_entry_fee(price_level)
                    specific_place['activity_duration_seconds'] = 1.5 * 3600 # Default 1h 30m
                    current_places.append(specific_place)
                    st.success(f"'{specific_place_query}' added to your itinerary!")
                else:
                    st.info(f"'{specific_place_query}' is already in your itinerary.")
            else:
                st.warning(f"Could not find '{specific_place_query}'. Please try a different name.")
    else: # Mock data path for adding specific place
        mock_file_path = MOCK_PLACES_PATH # Using the global constant
        if os.path.exists(mock_file_path):
            with open(mock_file_path, "r", encoding="utf-8") as f:
                all_mock_data = json.load(f)

            found_in_mock = next((p for p in all_mock_data if specific_place_query.lower() in p['name'].lower()), None)

            if found_in_mock:
                existing_place_ids = {p.get("place_id") for p in current_places if p.get("place_id")}
                if found_in_mock.get("place_id") not in existing_place_ids:
                    mock_place_price_level = found_in_mock.get('price_level', 1) # Default to inexpensive
                    found_in_mock['entry_fee'] = get_entry_fee(mock_place_price_level)
                    found_in_mock['activity_duration_seconds'] = found_in_mock.get('activity_duration_seconds', 1.5 * 3600)
                    current_places.append(found_in_mock)
                    st.success(f"'{specific_place_query}' added from mock data!")
                else:
                    st.info(f"'{specific_place_query}' is already in your itinerary (from mock).")
            else:
                st.warning(f"Could not find '{specific_place_query}' in mock data.")
        else:
            st.error(f"Mock data file not found at {mock_file_path}")

    return current_places


def sort_places_by_rating(places_list, limit=None): # <--- Added 'limit' parameter
    """
    Sorts a list of place dictionaries by their 'rating' in descending order.
    Places without a rating will be treated as having a rating of 0.
    Optionally, limits the returned list to a specified number of places after sorting.
    """
    # Ensure all places have a 'rating' key for consistent sorting, defaulting to 0
    # Also ensure 'user_ratings_total' is present for tie-breaking, defaulting to 0
    for place in places_list:
        if 'rating' not in place:
            place['rating'] = 0.0 # Use float for consistency
        if 'user_ratings_total' not in place:
            place['user_ratings_total'] = 0

    # Sort primarily by 'rating' (descending), secondarily by 'user_ratings_total' (descending)
    # This ensures places with higher ratings come first, and among equal ratings,
    # those with more reviews come first.
    sorted_places = sorted(
        places_list,
        key=lambda x: (x.get("rating", 0.0), x.get("user_ratings_total", 0)),
        reverse=True # Highest rating first
    )

    # --- NEW: Apply the limit after sorting ---
    if limit is not None and isinstance(limit, int) and limit > 0:
        return sorted_places[:limit]

    return sorted_places

import folium
from folium.features import DivIcon # You'll need to import this

import folium
from folium.features import DivIcon
import polyline # Make sure this is imported at the top of map_plotting.py

def generate_itinerary_map(places_data, optimal_route_names, direction_json=None):
    print("\n--- DEBUG: generate_itinerary_map START ---")
    print(f"Input: len(places_data)={len(places_data) if places_data else 0}, len(optimal_route_names)={len(optimal_route_names) if optimal_route_names else 0}")

    if not places_data or not optimal_route_names:
        print("DEBUG: places_data or optimal_route_names is empty/None. Returning None.")
        print("--- DEBUG: generate_itinerary_map END ---")
        return None

    place_lookup = {place['name']: place for place in places_data}
    print(f"DEBUG: Created place_lookup with {len(place_lookup)} entries.")

    ordered_coords = []
    found_all_coords = True

    for place_name in optimal_route_names:
        place = place_lookup.get(place_name)

        print(f"DEBUG: Processing place_name: '{place_name}'")

        if place:
            if 'geometry' in place and 'location' in place['geometry']:
                lat = place['geometry']['location'].get('lat')
                lon = place['geometry']['location'].get('lng')

                if lat is not None and lon is not None:
                    try:
                        lat = float(lat)
                        lon = float(lon)
                        ordered_coords.append([lat, lon])
                        print(f"DEBUG: Added coordinates for '{place_name}': [{lat}, {lon}]")
                    except ValueError:
                        print(f"DEBUG ERROR: Coordinates for '{place_name}' are not valid numbers: lat={lat}, lon={lon}. Skipping.")
                        found_all_coords = False
                        break
                else:
                    print(f"DEBUG ERROR: Place '{place_name}' has geometry.location but lat/lng are None. Full place data: {place}")
                    found_all_coords = False
                    break
            else:
                print(f"DEBUG ERROR: Place '{place_name}' found in places_data, but is MISSING 'geometry' or 'location' keys for coordinates. Full place data: {place}")
                found_all_coords = False
                break
        else:
            print(f"DEBUG ERROR: Place '{place_name}' from optimal_route_names NOT FOUND in places_data (place_lookup).")
            found_all_coords = False
            break

    if not found_all_coords:
        print("DEBUG: Not all coordinates found or were valid. Returning None.")
        print("--- DEBUG: generate_itinerary_map END ---")
        return None

    if not ordered_coords:
        print("DEBUG: ordered_coords list is empty after processing optimal_route_names. Returning None.")
        print("--- DEBUG: generate_itinerary_map END ---")
        return None

    print(f"DEBUG: Successfully gathered {len(ordered_coords)} ordered coordinates.")

    center_lat = sum(p[0] for p in ordered_coords) / len(ordered_coords)
    center_lon = sum(p[1] for p in ordered_coords) / len(ordered_coords)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    print(f"DEBUG: Map initialized at center: [{center_lat}, {center_lon}]")

    # Add numbered markers for each place
    for i, place_name in enumerate(optimal_route_names):
        place = place_lookup.get(place_name)
        # Use the same nested access for lat/lon here as well
        lat, lon = float(place['geometry']['location']['lat']), float(place['geometry']['location']['lng'])

        folium.Marker(
            location=[lat, lon],
            popup=f"<b>{place['name']}</b><br>Stop #{i+1}",
            icon=DivIcon(
                icon_size=(20,20),
                icon_anchor=(10,20),
                html=f'<div style="font-size: 12pt; color: white; background-color: #0078A8; border-radius: 50%; width: 20px; height: 20px; text-align: center; line-height: 20px;"><b>{i+1}</b></div>',
                class_name="custom-marker"
            )
        ).add_to(m)
        print(f"DEBUG: Added marker for '{place_name}' (Stop #{i+1}).")

    # --- Add detailed polylines for travel segments ---
    # **THIS IS THE MODIFIED SECTION FOR KEY MATCHING**
    if direction_json and len(direction_json) > 0:
        print("DEBUG: direction_json is provided AND contains data. Attempting to add polylines.")
        for i in range(len(optimal_route_names) - 1):
            from_place_name = optimal_route_names[i]
            to_place_name = optimal_route_names[i+1]

            # Define possible keys based on your JSON format
            # Now explicitly construct the key based on your JSON format
            # We will try both 'walking' and 'transit' keys as fallback
            possible_keys = [
                f"{from_place_name}-{to_place_name}-walking",
                f"{from_place_name}-{to_place_name}-transit"
            ]

            found_key = None
            for key_attempt in possible_keys:
                if key_attempt in direction_json:
                    found_key = key_attempt
                    break

            if found_key and direction_json[found_key] and len(direction_json[found_key]) > 0 and direction_json[found_key][0].get("overview_polyline"):
                encoded_polyline = direction_json[found_key][0]["overview_polyline"]["points"]
                try:
                    decoded_polyline = polyline.decode(encoded_polyline)
                    folium.PolyLine(
                        locations=decoded_polyline,
                        color="blue", # Use blue for detailed routes
                        weight=3,
                        opacity=0.8,
                        tooltip=f"{from_place_name} to {to_place_name} ({'Walking' if 'walking' in found_key else 'Transit'})"
                    ).add_to(m)
                    print(f"DEBUG: Added detailed polyline for {found_key}.")
                except Exception as e:
                    print(f"DEBUG ERROR: Failed to decode polyline for {found_key}: {e}. Fallback to straight line.")
                    folium.PolyLine([ordered_coords[i], ordered_coords[i+1]], color="red", weight=4, opacity=0.7).add_to(m)
            else:
                print(f"DEBUG: No detailed polyline data found for {from_place_name} to {to_place_name} with available modes or polyline missing. Using straight line fallback.")
                folium.PolyLine([ordered_coords[i], ordered_coords[i+1]], color="red", weight=4, opacity=0.7).add_to(m)
    else:
        print("DEBUG: direction_json not provided or is empty. Using straight lines for all segments.")
        # Draw straight lines for all segments if no direction data
        for i in range(len(optimal_route_names) - 1):
            folium.PolyLine([ordered_coords[i], ordered_coords[i+1]], color="red", weight=4, opacity=0.7).add_to(m)


    m.fit_bounds(m.get_bounds())
    print("DEBUG: Map bounds fitted.")
    print("--- DEBUG: generate_itinerary_map END (SUCCESS) ---")
    return m


def get_estimated_entry_cost(place_data):
    """
    Estimates the entry cost in GBP for a place, prioritizing valid price_level,
    then falling back to place types.
    """
    # Attempt to get price_level. It could be None, an integer, or even a string like 'NA' if parsed that way.
    price_level_raw = place_data.get('price_level')
    #st.write(f"DEBUG in get_estimated_entry_cost: Place: {place_data.get('name')}, Raw Price Level: {price_level_raw} (Type: {type(price_level_raw)})")
    # --- END DEBUG LINE ---


    # 1. Check if price_level is a valid integer (0-4) to use it.
    # This explicitly excludes None, empty string '', 'NA', or any other non-integer types.
    if isinstance(price_level_raw, int) and 0 <= price_level_raw <= 4:
        return get_entry_fee(price_level_raw)

    # 2. Fallback to place_types if price_level is not a valid integer or is unavailable
    place_types = [t.lower() for t in place_data.get('types', [])]

    TYPE_BASED_DEFAULT_FEES_GBP = {
        "museum": 20.00,
        "art_gallery": 10.00,
        "tourist_attraction": 25.00,
        "amusement_park": 40.00,
        "zoo": 25.00,
        "aquarium": 20.00,
        "cathedral": 10.00, # Process more specific types before general ones
        "church": 0.00,
        "park": 0.00,
        "garden": 0.00,
        "library": 0.00,
        "playground":0.00,
        "point_of_interest": 0.00,
        "landmark": 0.00,
    }

    # Iterate through place_types to find the first matching default fee
    for p_type in place_types:
        if p_type in TYPE_BASED_DEFAULT_FEES_GBP:
            return TYPE_BASED_DEFAULT_FEES_GBP[p_type]

    # 3. Final fallback if no estimation method works (neither valid price_level nor matching type)
    return 0.00

def get_entry_fee(price_level):
    """
    Maps Google Places API integer price_level (0-4) to an estimated GBP entry fee.
    This function *assumes* it receives a valid integer price_level (0-4).
    The validation for None, '', 'NA' etc., happens in get_estimated_entry_cost.
    """
    if price_level == 0:
        return 0.00 # Free
    elif price_level == 1:
        return 5.00 # Example for inexpensive
    elif price_level == 2:
        return 15.00 # Example for moderate
    elif price_level == 3:
        return 30.00 # Example for expensive
    elif price_level == 4:
        return 50.00 # Example for very expensive
    return 0 # Fallback

# --- Layout Columns ---
col_chat, col_main_content = st.columns([0.2, 0.7])

with col_chat:
    with st.container(height=460):
        for chat_message in st.session_state.history:
            with st.chat_message(chat_message["role"]):
                # Check if the content is a dictionary (for checkboxes)
                if isinstance(chat_message["content"], dict) and chat_message["content"].get("type") == "checkbox_options":
                    st.write(chat_message["content"]["message"])
                    st.session_state.checkbox_options = chat_message["content"]["options"] # Store options
                    st.session_state.chat_input_enabled = True # This was the change you made in the 'working code'
                    st.session_state.chat_input_key = "chat_input_disabled" # Update key when disabling

                    # Create checkboxes directly in the chat message area
                    for option in st.session_state.checkbox_options:
                        if option == "others":
                            checked = st.checkbox(option.capitalize(), key=f"place_type_checkbox_{option}_{st.session_state.rerun_count}_{id(chat_message)}")
                            other_text = st.text_input("Specify other (optional)", key=f"other_place_type_text_{st.session_state.rerun_count}_{id(chat_message)}")

                            if checked:
                                # Remove 'others' placeholder if it exists (we'll replace it with actual entries)
                                if "others" in st.session_state.selected_place_types:
                                    st.session_state.selected_place_types.remove("others")

                                # If textbox filled, split by comma and add each trimmed entry separately
                                if other_text.strip():
                                    #other_places = [x.strip() for x in other_text.split(",") if x.strip()]
                                    other_places = [x.strip() for x in other_text.replace(',', ' ').split() if x.strip()]
                                    for place in other_places:
                                        if place not in st.session_state.selected_place_types:
                                            st.session_state.selected_place_types.append(place)
                                else:
                                    # If textbox empty, add 'others' placeholder
                                    if "others" not in st.session_state.selected_place_types:
                                        st.session_state.selected_place_types.append("others")
                            else:
                                # Checkbox unchecked: remove 'others' placeholder if present
                                if "others" in st.session_state.selected_place_types:
                                    st.session_state.selected_place_types.remove("others")


                                # Also remove any previously added custom places from the textbox
                                #other_places = [x.strip() for x in other_text.split(",") if x.strip()]
                                other_places = [x.strip() for x in other_text.replace(',', ' ').split() if x.strip()]
                                for place in other_places:
                                    if place in st.session_state.selected_place_types:
                                        st.session_state.selected_place_types.remove(place)
                        else:
                            checked = st.checkbox(option.capitalize(), key=f"place_type_checkbox_{option}_{st.session_state.rerun_count}_{id(chat_message)}")

                            if checked and option not in st.session_state.selected_place_types:
                                st.session_state.selected_place_types.append(option)
                            elif not checked and option in st.session_state.selected_place_types:
                                st.session_state.selected_place_types.remove(option)

                    # Add a button to confirm selections
                    if st.button("Submit", key=f"confirm_place_type_selection_{st.session_state.rerun_count}_{id(chat_message)}"):
                        if st.session_state.selected_place_types:
                            # Find the index of the current checkbox message in history to modify it
                            current_message_index = -1
                            for i, msg in enumerate(st.session_state.history):
                                if msg is chat_message: # Compare by object identity to find the exact message
                                    current_message_index = i
                                    break

                            if current_message_index != -1:
                                # Replace the complex dictionary message with a simple text message.
                                # This prevents the checkboxes from being re-rendered on subsequent reruns.
                                st.session_state.history[current_message_index] = {
                                    "role": "assistant",
                                    "content": chat_message["content"]["message"] # Keep the original prompt text
                                }
                            selected_str = ", ".join(st.session_state.selected_place_types)

                            # Add user's selection to history
                            st.session_state.history.append({"role": "user", "content": f"You selected {selected_str} . Please confirm. Yes or No"})

                            # Update the intent context with the selected place types
                            st.session_state.intent_context["slots_filled"]["place_type"] = st.session_state.selected_place_types

                            # Reset checkbox state
                            st.session_state.selected_place_types = [] # Clear selections
                            st.session_state.checkbox_options = [] # Clear options (hides checkboxes)
                            st.session_state.chat_input_enabled = True # Crucial: Re-enable chat input
                            # Change key to force re-render enabled state
                            st.session_state.chat_input_key = "chat_input_enabled_" + str(st.session_state.rerun_count)
                            st.session_state.rerun_count += 1 # Increment for unique key

                            # Explicit rerun *immediately* after setting chat_input_enabled
                            st.rerun()

                        else:
                            st.session_state.history.append({"role": "assistant", "content": "Please select at least one type of place."})
                            st.rerun() # Rerun even if no selection


                # --- START: MODIFIED DROPDOWN LOGIC (With Confirm Button) ---
                elif isinstance(chat_message["content"], dict) and chat_message["content"].get("type") == "dropdown_options":
                    st.write(chat_message["content"]["message"]) # Display the prompt from JSON

                    dropdown_options = chat_message["content"]["options"]
                    slot_name = chat_message["content"]["slot_name"]

                    # Determine initial index. If "1" is an option, it's a good default.
                    # Otherwise, default to the first option available.
                    if "1" in dropdown_options:
                        default_index = dropdown_options.index("1")
                    elif dropdown_options: # If there are any options, pick the first one
                        default_index = 0
                    else: # No options, should not happen if JSON is correct
                        default_index = 0

                    dropdown_key = f"duration_selectbox_{st.session_state.rerun_count}"

                    # Ensure a default for this specific key
                    if dropdown_key not in st.session_state:
                        st.session_state[dropdown_key] = dropdown_options[default_index] if dropdown_options else ""

                    # The selectbox will update st.session_state[dropdown_key] when user interacts
                    selected_value = st.selectbox(
                        "Select number of days:", # A clear label for the dropdown widget
                        options=dropdown_options,
                        index=default_index,
                        key=dropdown_key # Use the unique key
                    )

                    # Add a button to confirm the selection
                    # This button will be displayed only when the dropdown message is active
                    confirm_button_key = f"confirm_duration_{st.session_state.rerun_count}"
                    if st.button("Confirm Selection", key=confirm_button_key):
                        # --- Process the confirmed selection ---
                        confirmed_value = st.session_state[dropdown_key] # Use the value stored in session state

                        # Find the index of the current dropdown message in history to modify it
                        current_message_index = -1
                        for i, msg in enumerate(st.session_state.history):
                            if msg is chat_message: # Compare by object identity
                                current_message_index = i
                                break

                        if current_message_index != -1:
                            # Replace the complex dictionary message with a simple text message.
                            # This prevents the dropdown from being re-rendered on subsequent reruns.
                            st.session_state.history[current_message_index] = {
                                "role": "assistant",
                                "content": chat_message["content"]["message"] # Keep the original prompt text
                            }

                            # Fill the slot in the intent context
                            st.session_state.intent_context["slots_filled"][slot_name] = confirmed_value

                            # Add user's "selection" as a new message to history
                            st.session_state.history.append({"role": "user", "content": f"Did you chose {confirmed_value} day?"})

                            st.session_state.chat_input_enabled = True # Re-enable the main chat input
                            st.session_state.chat_input_key = "chat_input_enabled_dropdown_confirmed_" + str(st.session_state.rerun_count)
                            st.session_state.rerun_count += 1
                            st.rerun() # ***IMPORTANT***: Rerun the app to process the next step
                        else:
                            # Fallback if message not found, although unlikely.
                            st.session_state.chat_input_enabled = False
                            st.session_state.chat_input_key = "chat_input_disabled_dropdown_pending"
                    else:
                        # Keep chat input disabled until confirmed
                        st.session_state.chat_input_enabled = False
                        st.session_state.chat_input_key = "chat_input_disabled_dropdown_pending"

                else: # Regular chat message (not checkbox prompt)
                    st.write(chat_message["content"])

    with st.container():
        # This block will always render st.chat_input
        if prompt := st.chat_input(
                "Ask your trip...",
                disabled=not st.session_state.chat_input_enabled, # Use the state variable
                key=st.session_state.chat_input_key # Use the dynamic key
        ):
            st.session_state.history.append({"role": "user", "content": prompt})

            context = st.session_state.intent_context

            # --- Intent Processing Logic ---
            if context["active_intent"] is None:
                intent_name, confidence = interpret_intent(prompt)

                if confidence > 0.7:
                    context["active_intent"] = intent_name
                    context["slots_filled"] = {}
                    context["pending_slot"] = None
                    st.session_state.chat_input_enabled = True # Ensure enabled for initial intent
                    st.session_state.chat_input_key = "chat_input_active_" + str(st.session_state.rerun_count)
                    st.session_state.rerun_count += 1
                    if intent_name == "plan_trip":
                        st.session_state.show_results = False
                else:
                    bot_response = "Sorry, I didn’t quite understand that. Could you please rephrase?"
                    st.session_state.history.append({"role": "assistant", "content": bot_response})
                    st.rerun()

            if context["active_intent"]:
                BASE_DIR = os.path.dirname(os.path.abspath(__file__))
                INTENT_PATH = os.path.join(BASE_DIR, "..", "utility", "intent_list.json")

                with open(INTENT_PATH, "r") as f:
                    intent_config = json.load(f)["intents"]

                intent = intent_config.get(context["active_intent"], {})
                slots = intent.get("slots", [])

                if context["pending_slot"]:
                    slot_name = context["pending_slot"]["name"]

                    # Only store user prompt if slot wasn't already filled
                    # This avoids overwriting checkbox selections with "yes"
                    if slot_name not in context["slots_filled"]:
                        context["slots_filled"][slot_name] = prompt

                    if context["pending_slot"]["type"] != "DROPDOWN":
                        context["pending_slot"] = None

                bot_response = None
                for slot in slots:
                    if slot["required"] and slot["name"] not in context["slots_filled"]:
                        context["pending_slot"] = slot
                        if slot["name"] == "place_type" and "options" in slot:
                            bot_response = {
                                "type": "checkbox_options",
                                "message": slot["prompt"],
                                "options": slot["options"]
                            }
                            st.session_state.chat_input_enabled = False # Disable chat input when sending checkboxes
                            st.session_state.chat_input_key = "chat_input_disabled_prompt" # Update key
                        elif slot["type"] == "DROPDOWN" and "options" in slot:
                            bot_response = {
                                "type": "dropdown_options",
                                "message": slot["prompt"],
                                "options": slot["options"],
                                "slot_name": slot["name"]
                            }
                        else:
                            bot_response = slot["prompt"]
                            st.session_state.chat_input_enabled = True # Ensure enabled for text input prompts
                            st.session_state.chat_input_key = "chat_input_enabled_prompt_" + str(st.session_state.rerun_count)
                            st.session_state.rerun_count += 1
                        break
                else:
                    filled = context["slots_filled"]
                    responses = intent.get("responses", [])
                    if responses:
                        try:
                            for r in responses:
                                filled_safe = {k: (", ".join(v) if isinstance(v, list) else v) for k, v in filled.items()}
                                formatted_response = r.format(**filled_safe)
                                st.session_state.history.append({"role": "assistant", "content": formatted_response})
                                st.session_state.trip_data = filled
                                print(f"DEBUG: st.session_state.trip_data after intent processing: {st.session_state.trip_data}") # Add this line
                                st.session_state.show_results = True
                        except AttributeError as e:
                            st.error("An internal error occurred: Typo in session_state access. Please contact support.")
                            st.session_state.show_results = False # Or handle as appropriate
                    else:
                        st.session_state.history.append({"role": "assistant", "content": "Thanks! I’ve recorded your request."})
                        st.session_state.show_results = True

                    context["active_intent"] = None
                    context["slots_filled"] = {}
                    context["pending_slot"] = None
                    st.session_state.chat_input_enabled = True # Ensure enabled if conversation ends
                    st.session_state.chat_input_key = "chat_input_final_" + str(st.session_state.rerun_count)
                    st.session_state.rerun_count += 1

                if bot_response is not None:
                    st.session_state.history.append({"role": "assistant", "content": bot_response})

                st.rerun() # Rerun after processing user prompt

with col_main_content:
    if not st.session_state.show_results:
        st.markdown(
            """ 
            <div class="title-tagline-box">
                <h1>Smart2SelfTrip</h1>
                <p>Plan Your Perfect Day Trip in a Snap</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:

        st.markdown(
            """
            <div class="title-result-1">
                <h1>YOUR PERSONALIZED ITINERARY</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
        if "trip_data"in st.session_state:


            with st.spinner("Fetching places and building your itinerary..."):

                #places = get_initial_places(st.session_state.trip_data, use_live_api, total_limit=8) - will change after working for 1 place
                places = get_initial_places(st.session_state.trip_data, use_live_api, total_limit=6)
                st.session_state.places_results = places
                print(f"DEBUG: Fetched places: {places}")

                #st.session_state.places_results = sort_places_by_rating(st.session_state.places_results, limit=5) - will change after working for 1 place
                st.session_state.places_results = sort_places_by_rating(st.session_state.places_results, limit=6)
                print(f"DEBUG: st.session_state.places_results: {st.session_state.places_results}")

            if st.session_state.places_results:
                origins_destinations = [f"place_id:{p['place_id']}" for p in st.session_state.places_results]

                with st.spinner("Fetching walking matrix... This might take a moment."):
                    st.session_state.walking_matrix = get_distance_matrix(
                        origins_destinations, origins_destinations, "walking", GOOGLE_API_KEY, use_live_api, MOCK_WALKING_MATRIX_PATH, MOCK_TRANSIT_MATRIX_PATH
                    )
                with st.spinner("Fetching transit matrix... This might take a moment."):
                    st.session_state.transit_matrix = get_distance_matrix(
                        origins_destinations, origins_destinations, "transit", GOOGLE_API_KEY, use_live_api, MOCK_WALKING_MATRIX_PATH, MOCK_TRANSIT_MATRIX_PATH
                    )

                if st.session_state.walking_matrix and st.session_state.transit_matrix:
                    time_map, mode_map = create_time_map(
                        st.session_state.places_results, st.session_state.walking_matrix, st.session_state.transit_matrix
                    )
                    st.session_state.time_map = time_map
                    st.session_state.mode_map = mode_map

                    if time_map and mode_map:
                        optimal_route_names, total_travel_time_seconds, optimal_travel_modes = find_optimal_route_tsp(
                            st.session_state.places_results, time_map, mode_map
                        )
                        # Store optimal_route_names in session state for map generation later
                        st.session_state.optimal_route_names = optimal_route_names
                        if optimal_route_names and total_travel_time_seconds is not None:
                            # --- Display Optimal Route, Total Expense, Total Time FIRST ---
                            # Initialize ALL total expense accumulators here, before the loop starts
                            total_expense = 0
                            total_transit_cost = 0        # Initialize total transit cost here
                            total_estimated_place_fees = 0 # Initialize total place fees here

                            itinerary_details = [] # This will be used for the Itinerary Details table later
                            current_time = datetime.datetime(2025, 7, 22, 10, 0, 0)
                            place_name_to_data = {p['name']: p for p in st.session_state.places_results}
                            st.session_state.direction_details = {} # Initialize for map plotting

                            for i in range(len(optimal_route_names)):
                                place_name = optimal_route_names[i]
                                place_data = place_name_to_data[place_name]

                                activity_duration_seconds = place_data.get('activity_duration_seconds', 0)

                                # Use your custom function to get the estimated entry fee
                                estimated_fee = get_estimated_entry_cost(place_data)
                                place_data['entry_fee'] = estimated_fee # Store it back in place_data for display later

                                # Accumulate place fees for subtotals and grand total
                                total_estimated_place_fees += estimated_fee
                                total_expense += estimated_fee # Add to overall total expense

                                itinerary_details.append({
                                    "Time": current_time.strftime("%I:%M %p"),
                                    "Mode": "Visit",
                                    "Duration": format_duration(activity_duration_seconds),
                                    "Activity / Place": f"Arrive at {place_name}",
                                    "Instructions": "Time to explore this amazing spot!"
                                })
                                current_time += datetime.timedelta(seconds=activity_duration_seconds)

                                if i < len(optimal_route_names) - 1:
                                    from_place_name = optimal_route_names[i]
                                    to_place_name = optimal_route_names[i+1]

                                    from_place_id = place_name_to_data[from_place_name]['place_id']
                                    to_place_id = place_name_to_data[to_place_name]['place_id']

                                    from_original_idx = next(idx for idx, p in enumerate(st.session_state.places_results) if p['name'] == from_place_name)
                                    to_original_idx = next(idx for idx, p in enumerate(st.session_state.places_results) if p['name'] == to_place_name)

                                    travel_mode = mode_map[from_original_idx][to_original_idx]
                                    travel_duration_seconds = time_map[from_original_idx][to_original_idx]

                                    transit_cost_for_segment = 0 # Temporary variable for THIS segment's transit cost
                                    if travel_mode == 'transit':
                                        transit_cost_for_segment = 3.50 # Using 3.50 as per your last snippet
                                        total_transit_cost += transit_cost_for_segment # Accumulate to total transit cost

                                    detailed_steps = []
                                    formatted_directions = "No detailed instructions available."

                                    if travel_mode in ['walking', 'transit']:
                                        detailed_steps = get_directions_details(
                                            origin_place_id=from_place_id,
                                            destination_place_id=to_place_id,
                                            travel_mode=travel_mode,
                                            api_key=GOOGLE_API_KEY,
                                            use_live=use_live_api,
                                            mock_directions_path=MOCK_DIRECTIONS_DETAILS_PATH,
                                            origin_name=from_place_name,
                                            destination_name=to_place_name
                                        )
                                        formatted_directions = format_instructions(detailed_steps)
                                        st.session_state.direction_details[f"{from_place_name}_to_{to_place_name}"] = detailed_steps
                                    else:
                                        if travel_mode == 'driving':
                                            formatted_directions = "Need to drive or take a cab."
                                        else:
                                            formatted_directions = f"Directions unavailable for mode: {travel_mode}"

                                    travel_mode_display = travel_mode.capitalize() # Default
                                    if travel_mode == 'walking':
                                        travel_mode_display = "🚶 Walking"
                                    elif travel_mode == 'transit':
                                        travel_mode_display = "🚌 Transit"
                                    elif travel_mode == 'driving':
                                        travel_mode_display = "🚗 Driving"

                                    itinerary_details.append({
                                        "Time": current_time.strftime("%I:%M %p"),
                                        "Mode": travel_mode_display,
                                        "Duration": format_duration(travel_duration_seconds),
                                        "Activity / Place": f"Travel to {to_place_name}",
                                        "Instructions": formatted_directions
                                    })

                                    total_expense += transit_cost_for_segment # Add to overall total expense
                                    current_time += datetime.timedelta(seconds=travel_duration_seconds)

                            # --- Define trip_place here before the summary markdown block ---
                            trip_place = "Not Specified" # Default value
                            if "trip_data" in st.session_state and "destination_city" in st.session_state.trip_data:
                                trip_place = st.session_state.trip_data["destination_city"]

                            col_image,col_summary, = st.columns([0.3, 0.7])

                            with col_image:
                                main_image_url = None
                                if trip_place and trip_place != "Not Specified":
                                    # Get the Place ID for the destination ci   ty
                                    destination_place_id = get_place_id_from_name(trip_place, GOOGLE_API_KEY)

                                    if destination_place_id:
                                        # Get the place details, specifically photos
                                        destination_details = get_place_details_with_photos(destination_place_id)

                                        if destination_details and 'photos' in destination_details and destination_details['photos']:
                                            # Use the first available photo
                                            photo_reference = destination_details['photos'][0].get('photo_reference')
                                            if photo_reference:
                                                main_image_url = get_place_photo_url(photo_reference, max_width=600)
                                                location_image_url = f'<img src="{main_image_url}" style="width:300px; height:300px; border-radius: 8px; margin-top: 10px;">' if main_image_url else ''
                                            else:
                                                st.write(f"*(No photo reference found for {trip_place} in details)*")
                                        else:
                                            st.write(f"*(No photo details found for {trip_place})*")
                                    else:
                                        st.write(f"*(Could not get Place ID for {trip_place})*")
                                else:
                                    st.write(f"*(Trip destination not specified)*")

                                st.markdown(f"""
                                        <div class="location_image">
                                            {location_image_url} 
                                            <h1 style="font-weight: bold; font-size: 1.2em;"><strong>Destination: </strong>{trip_place.upper()}</h1>
                                        </div>
                                        """, unsafe_allow_html=True)

                            with col_summary:
                                        #Summary title section
                                        st.markdown(f"""
                                        <div class="summary-top">
                                        <h1>Summary</h1>
                                        <p><strong>Total estimated expense: </strong>${total_expense:.2f}</p>
                                        <p><strong>Total estimated trip time: </strong>{format_duration(total_travel_time_seconds)}</p>
                                        <p><strong>Optimal Route: </strong>{' <strong>→</strong> '.join(optimal_route_names)}</p>
                                    </div>
                                    """, unsafe_allow_html=True)




                            #STOP POINTS
                            place_name_to_full_data = {p['name']: p for p in st.session_state.places_results}

                            # Create the column objects *once*
                            col1, col2, col3 = st.columns(3)
                            column_objects = [col1, col2, col3]

                            # Iterate through optimal_route_names to get details in the correct order
                            for i, place_name_in_route in enumerate(optimal_route_names):
                                current_col_idx = i % 3
                                current_column_placeholder = column_objects[current_col_idx]

                                with current_column_placeholder:
                                    place_data = place_name_to_full_data.get(place_name_in_route)

                                    if place_data:
                                        place_types = place_data.get('types', [])
                                        place_rating = place_data.get('rating')
                                        user_ratings = place_data.get('user_ratings_total')

                                        # --- Logic to get IMAGE URL (must be before the markdown block) ---

                                        # image_url = None
                                        # if 'photos' in place_data and place_data['photos']:
                                        #     # Get the photo_reference of the first photo
                                        #     photo_reference = place_data['photos'][0].get('photo_reference')
                                        #     if photo_reference:
                                        #         # Call the helper function to get the direct image URL
                                        #         # Make sure get_place_photo_url is defined elsewhere in your script
                                        #         image_url = get_place_photo_url(photo_reference, max_width=400) # You can adjust max_width
                                        #
                                        # # # --- END IMAGE URL LOGIC -
                                        #
                                        # # Create the image HTML string
                                        # image_html = f'<img src="{image_url}" style="width:300px; height:200px; border-radius: 8px; margin-top: 10px;">' if image_url else ''

                                        image_html=0

                                        formatted_types = [t.replace('_', ' ').title() for t in place_types]
                                        types_str = ", ".join(formatted_types) if formatted_types else "N/A"

                                        rating_str = "N/A"
                                        if place_rating is not None and user_ratings is not None:
                                            rating_str = f"{place_rating} ⭐ ({user_ratings:,} reviews)"

                                        st.markdown(f"""
                                        <div class="stop-details">
                                            <h1>Stop #{i+1}: {place_name_in_route}</h1>
                                            <p>Type(s): {types_str}</p>
                                            <p>Rating: {rating_str}</p>
                                            {image_html} 
                                        </div>
                                        """, unsafe_allow_html=True)

                                    else:
                                        st.warning(f"Could not find details for **{place_name_in_route}**.")
                                        st.write(f"DEBUG: `place_data` is None for {place_name_in_route}")


                            #Itinerary table
                            st.button("### Itinerary Details") # This adds a small header for the table

                            itinerary_df = pd.DataFrame(itinerary_details)

                            # Keep .set_index('Time') because you want 'Time' to be the index
                            styled_df = itinerary_df.set_index('Time').style \
                                .hide(axis='index') \
                                .set_properties(**{'background-color': '#FFFFFF', # Base styling for all data cells
                                                   'color': '#333',

                                                   }) \
                                .set_table_styles([
                                # General table styling: separate cells with spacing
                                {'selector': '', 'props': [('border-collapse', 'separate'), ('border-spacing', '0 10px'),('width', '100%'),('table-layout', 'fixed')]},
                                {'selector': 'th, th.col_heading, th.index_name, th[scope="col"]', 'props': [
                                    ('border-collapse', 'separate'),
                                    ('border-spacing', '0 10px'),
                                    ('font-size', '1.5em'),
                                    ('color', '#333'),
                                    ('font-family', "'Inter', sans-serif"),
                                    ('background-color', '#FFFFFF'), # Make all headers white
                                ]},
                                # The 'td' selector applies to all standard data cells.
                                {'selector': 'td, td.data, td.level0', 'props': [
                                    ('border-collapse', 'separate'),
                                    ('border-spacing', '0 10px'),
                                    ('font-size', '1.2em'),
                                    ('color', '#333'),
                                    ('font-family', "'Inter', sans-serif"),
                                ]},

                                # Target the 'Time' header specifically.
                                {'selector': 'th.index_name', 'props': [
                                    ('width', '120px'), # Set a fixed width for the Time column header
                                    ('min-width', '100px'), # Ensure it doesn't get too small
                                    ('max-width', '150px'), # Ensure it doesn't get too large
                                    ('text-align', 'center'), # Center the time values
                                    ('white-space', 'normal') # Allow "Time" header text to wrap if needed
                                ]},

                                # C. 'Mode' Column
                                # This is your second *data* column (td:nth-child(2))
                                {'selector': 'th.col_heading:nth-child(2)', 'props': [ # Header for 'Mode'
                                    ('width', '120px'), # Adjust width for 'Mode' header
                                    ('min-width', '80px'),
                                    ('max-width', '120px')
                                ]},
                                {'selector': 'td:nth-child(2)', 'props': [ # Data cells for 'Mode'
                                    ('width', '120px'), # Adjust width for 'Mode' data
                                    ('min-width', '80px'),
                                    ('max-width', '120px'),
                                    ('text-align', 'center') # Center the 'LOCAL' or 'Visit' text
                                ]},

                                # D. 'Duration' Column
                                # This is your third *data* column (td:nth-child(3))
                                {'selector': 'th.col_heading:nth-child(3)', 'props': [ # Header for 'Duration'
                                    ('width', '100px'), # Adjust width for 'Duration' header
                                    ('min-width', '80px'),
                                    ('max-width', '100px')
                                ]},
                                {'selector': 'td:nth-child(3)', 'props': [ # Data cells for 'Duration'
                                    ('width', '100px'), # Adjust width for 'Duration' data
                                    ('min-width', '80px'),
                                    ('max-width', '100px'),
                                    ('text-align', 'center') # Center the duration text
                                ]},

                                # E. 'Instructions' Column
                                # This is your fourth *data* column (td:nth-child(4))
                                {'selector': 'th.col_heading:nth-child(4)', 'props': [ # Header for 'Instructions'
                                    ('width', 'auto'), # Let it take remaining space
                                    ('min-width', '100px') # Ensure a minimum width for instructions
                                ]},
                                {'selector': 'td:nth-child(4)', 'props': [ # Data cells for 'Instructions'
                                    ('width', 'auto'), # Let it take remaining space
                                    ('min-width', '100px'),
                                    ('word-wrap', 'break-word'), # Crucial for long instructions
                                    ('white-space', 'normal') # Ensure text wraps
                                ]}

                            ])

                            st.table(styled_df)



                            #Generate map
                            st.markdown(f"""
                                        <div class="space-adding">
                                            <p></p>
                                        </div>
                                        """, unsafe_allow_html=True)
                            st.button("### Route Map") # This adds a small header for the map

                            itinerary_map = generate_itinerary_map(
                                st.session_state.places_results,
                                st.session_state.optimal_route_names, # Use the stored optimal_route_names
                                st.session_state.direction_details
                            )

                            st.set_page_config(layout="wide")

                            if itinerary_map:
                                st_folium(itinerary_map, width=1400, height=700, key="main_itinerary_map_display")
                            else:
                                st.warning("Could not generate map. Check if place coordinates are available.")



                            st.markdown(f"""
                                        <div class="space-adding">
                                            <p></p>
                                        </div>
                                        """, unsafe_allow_html=True)

                            st.button("## Budget Details Split:")

                            budget_details_list = []
                            for place_data in st.session_state.places_results:
                                budget_details_list.append({
                                    'Place': place_data.get('name', 'Unnamed Place'),
                                    'Expected Spending / Fees': place_data.get('entry_fee', 0.0)
                                })
                            budget_details_split = pd.DataFrame(budget_details_list)

                            # --- Apply Styling to budget_details_split ---
                            styled_budget_df = budget_details_split.style \
                                .hide(axis='index') \
                                .format({'Expected Spending / Fees': "${:,.2f}"}) \
                                .set_properties(subset=pd.IndexSlice[:, ['Place', 'Expected Spending / Fees']],
                                                **{'background-color': '#FFFFFF', 'color': 'black', 'text-align': 'left','width': '1350px'}) \
                                .set_table_styles([
                                # Header styles
                                # Style for table headers (<th>)
                                {'selector': 'th', 'props': [
                                    ('background-color', '#FFFFFF'), # A slightly darker blue for headers
                                    ('color', 'black'),
                                    ('text-align', 'left')
                                ]},
                                # Ensure the entire table has no default borders if you don't want them
                                {'selector': 'table', 'props': [
                                    ('border-collapse', 'collapse'),
                                    ('width', '1350px')
                                ]},
                                # Add a light border to all cells for definition, or set to 'none'
                                {'selector': 'th, td', 'props': [
                                    ('border', '1px solid #ddd') # Light grey border
                                ]}
                            ])

                            # Display the styled budget_details_split DataFrame
                            st.write(styled_budget_df.to_html(), unsafe_allow_html=True)

                            #Summary Data table
                            summary_data = {
                                'Category': [
                                    'Total Trip Expense',
                                    'Total Transit Estimated Expense',
                                    'Total Place Estimated Expense'
                                ],
                                'Amount': [
                                    total_expense,
                                    total_transit_cost,
                                    total_estimated_place_fees
                                ]
                            }
                            summary_df = pd.DataFrame(summary_data)

                            styled_summary_df = summary_df.style \
                                .hide(axis='index') \
                                .format({'Amount': "${:,.2f}"}) \
                                .set_properties(subset=pd.IndexSlice[:, ['Category', 'Amount']],
                                                **{'background-color': '#FFFFFF', 'color': 'black', 'text-align': 'left','width':'1350px'}) \
                                .set_table_styles([
                                # Style for table headers (<th>)
                                {'selector': 'th', 'props': [
                                    ('background-color', '#FFFFFF'), # A slightly darker blue for headers
                                    ('color', 'black'),
                                    ('text-align', 'left')
                                ]},
                                # Ensure the entire table has no default borders if you don't want them
                                {'selector': 'table', 'props': [
                                    ('border-collapse', 'collapse'),
                                    ('width', '1350px')
                                ]},
                                # Add a light border to all cells for definition, or set to 'none'
                                {'selector': 'th, td', 'props': [
                                    ('border', '1px solid #ddd') # Light grey border
                                ]}
                            ])

                            st.write(styled_summary_df.to_html(), unsafe_allow_html=True)

                        else:
                            st.warning("Could not find an optimal route or calculate details. Please check data.")
                    else:
                        st.warning("Could not generate time and mode maps. This might be due to API errors or no places found.")
                else:
                    st.warning("Could not fetch walking or transit matrices. Travel time calculation will be skipped.")
            else:
                st.markdown(f"""
                                <div class="nocity_response">
                                    <p>Hmm, I couldn't find any city or preferences. Could you try searching for the place again?</p>
                                </div>
                                """, unsafe_allow_html=True)
        else:
            st.info("Please start by planning your trip with the chatbot to define destination and preferences.")