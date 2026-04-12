"""
Smart commute-based rental search.

Given multiple destinations (school, office, etc.), analyzes MRT connectivity
and generates optimal rental search queries.
"""

import json
from dataclasses import dataclass, field

from geo import (
    geocode_address, get_stations_within_radius, get_nearest_mrt,
    haversine, find_station, get_all_stations,
)
from engine import parse_query, Criteria
from scraper.data_gov import get_districts_for_mrt, DISTRICT_AREAS


_geocode_cache: dict[str, tuple[float, float] | None] = {}


@dataclass
class Location:
    """A destination the user commutes to."""
    name: str           # e.g. "SMU", "Office"
    address: str        # e.g. "Singapore Management University"
    lat: float = 0.0
    lng: float = 0.0
    nearby_stations: list[tuple[str, float]] = field(default_factory=list)  # [(name, dist_m)]


@dataclass
class StationScore:
    """A candidate station to live near, with commute scores."""
    name: str
    code: str
    lines: list[str]
    lat: float
    lng: float
    commute_details: dict = field(default_factory=dict)  # {location_name: {"distance_m": ..., "transfers": ...}}
    total_score: float = 0.0
    districts: list[int] = field(default_factory=list)


def geocode_location(loc: Location) -> Location:
    """Geocode a location and find nearby MRT stations."""
    # Use in-memory cache to avoid repeated API calls
    if loc.address in _geocode_cache:
        coords = _geocode_cache[loc.address]
    else:
        coords = geocode_address(loc.address)
        _geocode_cache[loc.address] = coords

    if coords:
        loc.lat, loc.lng = coords
    elif loc.lat == 0.0:
        if loc.name in _geocode_cache:
            coords = _geocode_cache[loc.name]
        else:
            coords = geocode_address(loc.name)
            _geocode_cache[loc.name] = coords
        if coords:
            loc.lat, loc.lng = coords

    if loc.lat and loc.lng:
        loc.nearby_stations = get_stations_within_radius(loc.lat, loc.lng, 1000)

    return loc


def _get_station_lines(station_name: str) -> list[str]:
    """Get MRT lines for a station."""
    s = find_station(station_name)
    return s["line"] if s else []


def _find_shared_lines(locations: list[Location]) -> dict[str, list[str]]:
    """
    Find MRT lines that connect to stations near each location.
    Returns {line_name: [station_near_loc1, station_near_loc2, ...]}.
    """
    # Collect lines -> stations for each location
    loc_lines: list[dict[str, list[str]]] = []
    for loc in locations:
        lines_map: dict[str, list[str]] = {}
        for station_name, _ in loc.nearby_stations:
            for line in _get_station_lines(station_name):
                lines_map.setdefault(line, []).append(station_name)
        loc_lines.append(lines_map)

    if not loc_lines:
        return {}

    # Single location: use all lines from that location
    if len(loc_lines) == 1:
        return loc_lines[0]

    # Multiple locations: find lines present in ALL locations
    common_lines = set(loc_lines[0].keys())
    for ll in loc_lines[1:]:
        common_lines &= set(ll.keys())

    result = {}
    for line in common_lines:
        stations = []
        for ll in loc_lines:
            stations.extend(ll.get(line, []))
        result[line] = list(set(stations))

    return result


def _stations_on_line(line: str) -> list[dict]:
    """Get all stations on a given MRT line."""
    return [s for s in get_all_stations() if line in s.get("line", [])]


def analyze_commute(locations: list[Location], radius_m: int = 1000) -> list[StationScore]:
    """
    Analyze commute from candidate residential stations to all destinations.

    Strategy:
    1. Find MRT lines that connect to stations near each location
    2. Find all stations on those shared lines
    3. Also consider stations near each location (for short commutes)
    4. Score each candidate station by total commute distance/convenience

    Returns sorted list of StationScore (best first).
    """
    # Geocode all locations
    for loc in locations:
        if loc.lat == 0.0 or loc.lng == 0.0:
            geocode_location(loc)

    # Find shared lines
    shared_lines = _find_shared_lines(locations)

    # Collect candidate stations
    candidates: dict[str, StationScore] = {}

    # Add all stations on shared lines
    for line, _ in shared_lines.items():
        for s in _stations_on_line(line):
            if s["name"] not in candidates:
                candidates[s["name"]] = StationScore(
                    name=s["name"], code=s["code"],
                    lines=s["line"], lat=s["lat"], lng=s["lng"],
                    districts=get_districts_for_mrt(s["name"]),
                )

    # Add stations near each location (within radius)
    for loc in locations:
        for station_name, dist in loc.nearby_stations:
            if station_name not in candidates:
                s = find_station(station_name)
                if s:
                    candidates[station_name] = StationScore(
                        name=s["name"], code=s["code"],
                        lines=s["line"], lat=s["lat"], lng=s["lng"],
                        districts=get_districts_for_mrt(s["name"]),
                    )

    # Score each candidate
    for cand in candidates.values():
        total_dist = 0
        for loc in locations:
            dist = haversine(cand.lat, cand.lng, loc.lat, loc.lng)

            # Check if direct line exists (no transfer needed)
            cand_lines = set(cand.lines)
            loc_station_lines = set()
            for sn, _ in loc.nearby_stations:
                loc_station_lines.update(_get_station_lines(sn))
            shared = cand_lines & loc_station_lines
            transfers = 0 if shared else 1

            cand.commute_details[loc.name] = {
                "distance_m": int(dist),
                "direct_lines": list(shared),
                "transfers": transfers,
            }
            # Score: distance + transfer penalty (1 transfer = 2km equivalent)
            total_dist += dist + transfers * 2000

        cand.total_score = total_dist

    # Sort by score (lower = better)
    scored = sorted(candidates.values(), key=lambda x: x.total_score)
    return scored


def generate_queries(
    stations: list[StationScore],
    bedrooms: int = 1,
    price_min: int | None = None,
    price_max: int | None = None,
    max_queries: int = 10,
    extra_criteria: str = "",
) -> list[dict]:
    """
    Generate search queries for the top-ranked stations.

    Returns list of {station, query_text, criteria, reason}.
    """
    queries = []
    seen_stations = set()

    for s in stations[:max_queries * 2]:  # scan more to allow dedup
        if len(queries) >= max_queries:
            break
        if s.name in seen_stations:
            continue
        seen_stations.add(s.name)

        # Build reason text
        reasons = []
        for loc_name, details in s.commute_details.items():
            dist_km = details["distance_m"] / 1000
            if details["direct_lines"]:
                lines_str = "/".join(details["direct_lines"])
                reasons.append(f"{dist_km:.1f}km to {loc_name} (direct via {lines_str})")
            else:
                reasons.append(f"{dist_km:.1f}km to {loc_name} (1 transfer)")

        # Build query
        price_part = ""
        if price_min and price_max:
            price_part = f"{price_min}-{price_max}"
        elif price_max:
            price_part = f"{price_max}以内"
        elif price_min:
            price_part = f"{price_min}"

        bed_part = f"{bedrooms}b{bedrooms}b" if bedrooms <= 2 else f"{bedrooms}br"
        query_text = f"{s.name} {bed_part} {price_part}".strip()
        if extra_criteria:
            query_text += f" {extra_criteria}"

        criteria = parse_query(query_text)

        queries.append({
            "station": s.name,
            "query_text": query_text,
            "criteria": criteria,
            "reason": " | ".join(reasons),
            "score": s.total_score,
            "commute": s.commute_details,
            "lines": s.lines,
            "districts": s.districts,
        })

    return queries


def format_analysis_report(
    locations: list[Location],
    queries: list[dict],
) -> str:
    """Format a human-readable report of the commute analysis."""
    lines = []
    lines.append("## Commute Analysis Report\n")

    lines.append("### Your Destinations")
    for loc in locations:
        if loc.nearby_stations:
            nearest = loc.nearby_stations[0]
            lines.append(f"- **{loc.name}** ({loc.address}): nearest MRT = {nearest[0]} ({int(nearest[1])}m)")
        else:
            lines.append(f"- **{loc.name}** ({loc.address})")

    lines.append("\n### Recommended Areas (ranked by commute)")
    for i, q in enumerate(queries, 1):
        lines.append(f"\n**{i}. {q['station']}** ({'/'.join(q['lines'])})")
        lines.append(f"   Query: `{q['query_text']}`")
        lines.append(f"   Why: {q['reason']}")

    return "\n".join(lines)
