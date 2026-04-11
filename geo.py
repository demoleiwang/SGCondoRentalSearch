"""Geographic utilities: MRT station lookup, distance calculation, geocoding."""

import json
import math
from pathlib import Path

import requests

# Load MRT stations data
_DATA_DIR = Path(__file__).parent / "data"
_MRT_STATIONS: list[dict] = []


def _load_stations() -> list[dict]:
    global _MRT_STATIONS
    if not _MRT_STATIONS:
        with open(_DATA_DIR / "mrt_stations.json", "r") as f:
            _MRT_STATIONS = json.load(f)
    return _MRT_STATIONS


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in meters between two points using Haversine formula."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def get_all_stations() -> list[dict]:
    """Return all MRT stations."""
    return _load_stations()


def get_station_names() -> list[str]:
    """Return sorted list of all MRT station names."""
    return sorted(set(s["name"] for s in _load_stations()))


def find_station(name: str) -> dict | None:
    """Find a station by name (case-insensitive partial match)."""
    name_lower = name.lower().strip()
    stations = _load_stations()

    # Exact match first
    for s in stations:
        if s["name"].lower() == name_lower:
            return s

    # Partial match
    for s in stations:
        if name_lower in s["name"].lower():
            return s

    return None


def get_nearest_mrt(lat: float, lng: float) -> tuple[str, float]:
    """
    Find the nearest MRT station to a given point.
    Returns (station_name, distance_in_meters).
    """
    stations = _load_stations()
    nearest = None
    min_dist = float("inf")

    for s in stations:
        dist = haversine(lat, lng, s["lat"], s["lng"])
        if dist < min_dist:
            min_dist = dist
            nearest = s["name"]

    return nearest, min_dist


def get_stations_within_radius(lat: float, lng: float, radius_m: float) -> list[tuple[str, float]]:
    """Find all MRT stations within a given radius. Returns [(name, distance_m)]."""
    stations = _load_stations()
    results = []
    for s in stations:
        dist = haversine(lat, lng, s["lat"], s["lng"])
        if dist <= radius_m:
            results.append((s["name"], dist))
    return sorted(results, key=lambda x: x[1])


def geocode_address(address: str) -> tuple[float, float] | None:
    """
    Geocode an address using OneMap API.
    Returns (lat, lng) or None if not found.
    """
    try:
        resp = requests.get(
            "https://www.onemap.gov.sg/api/common/elastic/search",
            params={"searchVal": address, "returnGeom": "Y", "getAddrDetails": "Y"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("found", 0) > 0:
            result = data["results"][0]
            return float(result["LATITUDE"]), float(result["LONGITUDE"])
    except (requests.RequestException, KeyError, IndexError, ValueError):
        pass
    return None
