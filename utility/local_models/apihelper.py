import requests

GOOGLE_API_KEY = st.secrets.get("google_maps_api_key", None)

def geocode_city(city_name):
    if not GOOGLE_API_KEY:
        st.error("Google API key not found in secrets!")
        return None, None

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": city_name, "key": GOOGLE_API_KEY}
    resp = requests.get(url, params=params)
    data = resp.json()

    if data.get("status") == "OK" and data.get("results"):
        loc = data["results"][0]["geometry"]["location"]
        return loc["lat"], loc["lng"]
    else:
        st.error(f"Geocode error: {data.get('status')}")
        return None, None


def get_places(lat, lng, place_type):
    if not GOOGLE_API_KEY:
        st.error("Google API key not found in secrets!")
        return []

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": 10000,  # 10 km radius
        "type": place_type,
        "key": GOOGLE_API_KEY
    }
    resp = requests.get(url, params=params)
    data = resp.json()

    if data.get("status") == "OK":
        return data.get("results", [])
    else:
        st.error(f"Places API error: {data.get('status')}")
        return []
