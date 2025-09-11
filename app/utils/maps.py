import os
from typing import Tuple
import requests


class MapsApiError(Exception):
    pass


def get_google_maps_api_key() -> str:
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    print(api_key)
    if not api_key:
        raise MapsApiError("GOOGLE_MAPS_API_KEY environment variable is not set")
    return api_key


def get_distance_km_between_locations(origin: str, destination: str) -> float:
    """
    Returns the driving distance in kilometers between origin and destination
    using Google Distance Matrix API. Raises MapsApiError on failure.
    """
    api_key = get_google_maps_api_key()
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destination,
        "units": "metric",
        "key": api_key,
    }

    response = requests.get(url, params=params, timeout=15)
    if response.status_code != 200:
        raise MapsApiError(f"Distance Matrix API failed with status {response.status_code}")

    data = response.json()
    if data.get("status") != "OK":
        raise MapsApiError(f"Distance Matrix API error: {data.get('status')}")

    rows = data.get("rows") or []
    if not rows or not rows[0].get("elements"):
        raise MapsApiError("Invalid Distance Matrix API response format")

    element = rows[0]["elements"][0]
    if element.get("status") != "OK":
        raise MapsApiError(f"Route not found: {element.get('status')}")

    distance_meters = element["distance"]["value"]
    duration_text = element["duration"]["text"]
    distance_km = float(distance_meters) / 1000.0
    return round(distance_km),duration_text


