"""Filter engine and natural language query parser for condo search."""

import re
from typing import TypedDict

from geo import get_station_names, find_station


class Criteria(TypedDict, total=False):
    """Structured search criteria."""
    location: str           # Free-text location or area name
    mrt_station: str        # Target MRT station name
    radius_m: int           # Search radius from MRT in meters
    bedrooms: int           # Number of bedrooms
    bathrooms: int          # Number of bathrooms
    price_min: int          # Minimum monthly rent
    price_max: int          # Maximum monthly rent
    facing: str             # Preferred facing direction (N/S/E/W/NE/SE/SW/NW)
    min_floor: int          # Minimum floor level
    min_area_sqft: int      # Minimum floor area in sqft


# MRT station names for matching (lowercase)
_STATION_NAMES_LOWER: list[tuple[str, str]] = []


def _get_station_names_lower() -> list[tuple[str, str]]:
    global _STATION_NAMES_LOWER
    if not _STATION_NAMES_LOWER:
        _STATION_NAMES_LOWER = [(name, name.lower()) for name in get_station_names()]
    return _STATION_NAMES_LOWER


def parse_query(text: str) -> Criteria:
    """
    Parse a natural language query into structured criteria.

    Examples:
        "Queenstown 1b1b 3300" -> {mrt_station: "Queenstown", bedrooms: 1, bathrooms: 1, price_min: 2970, price_max: 3630}
        "找2房在Bishan附近，预算4000以内" -> {mrt_station: "Bishan", bedrooms: 2, price_max: 4000}
        "1 bedroom near Paya Lebar MRT, around $3500, south facing" -> {mrt_station: "Paya Lebar", bedrooms: 1, price_min: 3150, price_max: 3850, facing: "S"}
    """
    criteria: Criteria = {}
    text_lower = text.lower()

    # --- Extract MRT station ---
    # Match station names (longer names first to avoid partial matches)
    matched_station_span = None
    stations = sorted(_get_station_names_lower(), key=lambda x: len(x[1]), reverse=True)
    for name, name_lower in stations:
        idx = text_lower.find(name_lower)
        if idx != -1:
            criteria["mrt_station"] = name
            criteria["location"] = name
            matched_station_span = (idx, idx + len(name_lower))
            break

    # Build a "clean" text with station name removed for facing/floor parsing
    # to avoid e.g. "one-north" triggering "north" facing
    text_no_station = text_lower
    if matched_station_span:
        s, e = matched_station_span
        text_no_station = text_lower[:s] + " " * (e - s) + text_lower[e:]

    # --- Extract bedroom count ---
    # Patterns: "1b1b", "2b2b", "1 bedroom", "2房", "3br", "3-room", "studio"
    bed_match_span = None
    bed_patterns = [
        (r'(\d)\s*b\s*\d\s*b', 1),              # 1b1b, 2b2b
        (r'(\d)\s*[-\s]?room', 1),               # 3-room, 3 room
        (r'(\d)\s*(?:bed(?:room)?s?|br|bdr)', 1), # 1 bedroom, 2br
        (r'(\d)\s*房', 1),                        # 2房
        (r'studio', 0),                            # studio = 0 bedrooms
        (r'executive', 5),                         # executive = 5
    ]
    for pattern, group_or_val in bed_patterns:
        m = re.search(pattern, text_lower)
        if m:
            if group_or_val in (0, 5):
                criteria["bedrooms"] = group_or_val
            else:
                criteria["bedrooms"] = int(m.group(1))
            bed_match_span = (m.start(), m.end())
            break

    # --- Extract bathroom count ---
    bath_patterns = [
        (r'\d\s*b\s*(\d)\s*b', 1),           # 1b1b -> 1 bathroom
        (r'(\d)\s*(?:bath(?:room)?s?)', 1),   # 1 bathroom
        (r'(\d)\s*卫', 1),                    # 1卫
    ]
    for pattern, _ in bath_patterns:
        m = re.search(pattern, text_lower)
        if m:
            criteria["bathrooms"] = int(m.group(1))
            break

    # --- Extract price ---
    # "3300" / "$3,300" / "3300附近" / "3300左右" / "around 3300" / "预算4000以内" / "3000-3500"
    # Range patterns: "3000-3500", "3000 to 4000", "3000~4000", "3000到4000"
    range_match = re.search(r'\$?\s*(\d[\d,]*)\s*[-~到]\s*\$?\s*(\d[\d,]*)', text)
    if not range_match:
        range_match = re.search(r'\$?\s*(\d[\d,]*)\s+to\s+\$?\s*(\d[\d,]*)', text_lower)
    if range_match:
        v1 = int(range_match.group(1).replace(",", ""))
        v2 = int(range_match.group(2).replace(",", ""))
        if v1 >= 500 and v2 >= 500:  # sanity check: looks like rent
            criteria["price_min"] = v1
            criteria["price_max"] = v2
    if "price_min" not in criteria and "price_max" not in criteria:
        # "以内/以下/under/below/max" -> price_max only (handle both prefix and suffix)
        under_match = (
            re.search(r'(\d[\d,]+)\s*(?:以内|以下)', text_lower) or
            re.search(r'(?:under|below|max|不超过|低于)\s*\$?\s*(\d[\d,]+)', text_lower) or
            re.search(r'\$?\s*(\d[\d,]+)\s*(?:under|below|max)', text_lower)
        )
        if under_match:
            val = int(under_match.group(1).replace(",", ""))
            if val >= 500:
                criteria["price_max"] = val
        else:
            # "以上/above/at least/min" -> price_min only (handle both prefix and suffix)
            above_match = (
                re.search(r'(\d[\d,]+)\s*(?:以上|起)', text_lower) or
                re.search(r'(?:above|at\s*least|min(?:imum)?|不低于|至少)\s*\$?\s*(\d[\d,]+)', text_lower) or
                re.search(r'\$?\s*(\d[\d,]+)\s*(?:above|at\s*least)', text_lower)
            )
            if above_match:
                val = int(above_match.group(1).replace(",", ""))
                if val >= 500:
                    criteria["price_min"] = val
            else:
                # "附近/左右/around" / bare number -> ±10%
                # Use finditer to check ALL number matches, pick one that looks like rent
                for around_match in re.finditer(
                    r'(?:around|about|大约|大概|约|预算|月租|rent)?\s*\$?\s*(\d[\d,]+)\s*(?:附近|左右|around|per\s*month|/\s*month|pm|块|元)?',
                    text_lower
                ):
                    val = int(around_match.group(1).replace(",", ""))
                    # Only treat as price if reasonable rent (1000-30000) and NOT inside bedroom/floor match
                    if 1000 <= val <= 30000:
                        # Make sure this number isn't part of the bedroom match
                        if bed_match_span and around_match.start() >= bed_match_span[0] and around_match.end() <= bed_match_span[1]:
                            continue
                        criteria["price_min"] = int(val * 0.9)
                        criteria["price_max"] = int(val * 1.1)
                        break

    # --- Extract facing/orientation ---
    # Use text_no_station to avoid matching station names (e.g. "one-north" -> "north")
    facing_patterns = [
        # Longer/compound patterns first
        (r'(?:south\s*east|southeast|东南|朝东南)\s*(?:facing)?', "SE"),
        (r'(?:south\s*west|southwest|西南|朝西南)\s*(?:facing)?', "SW"),
        (r'(?:north\s*east|northeast|东北|朝东北)\s*(?:facing)?', "NE"),
        (r'(?:north\s*west|northwest|西北|朝西北)\s*(?:facing)?', "NW"),
        # Cardinal directions - use word boundary \b to avoid matching inside words
        # e.g. "least" should NOT match "east", "northwest" handled above
        (r'\bsouth\b\s*(?:facing)?', "S"),
        (r'(?:facing\s+south\b)', "S"),
        (r'(?:朝南|南向)', "S"),
        (r'\bnorth\b\s*(?:facing)?', "N"),
        (r'(?:facing\s+north\b)', "N"),
        (r'(?:朝北|北向)', "N"),
        (r'\beast\b\s*(?:facing)?', "E"),
        (r'(?:facing\s+east\b)', "E"),
        (r'(?:朝东|东向)', "E"),
        (r'\bwest\b\s*(?:facing)?', "W"),
        (r'(?:facing\s+west\b)', "W"),
        (r'(?:朝西|西向)', "W"),
    ]
    for pattern, direction in facing_patterns:
        m = re.search(pattern, text_no_station)
        if m:
            criteria["facing"] = direction
            break

    # --- Extract floor preference ---
    # First check for "high floor" / "高楼层" (set default 15)
    high_floor = re.search(r'(?:high\s*floor|高楼层?)', text_no_station)
    if high_floor:
        criteria["min_floor"] = 15

    # Then check for explicit floor number: "min floor 10", "floor >= 10", "楼层10"
    # Use text_no_station and avoid matching bedroom numbers
    floor_match = (
        re.search(r'(?:min(?:imum)?\s*)?(?:floor|楼层?|层)\s*(?:>=?\s*)?(\d+)', text_no_station) or
        re.search(r'(\d+)\s*(?:楼层?|层)', text_no_station)  # Chinese: "10楼"
    )
    if floor_match:
        floor_val = int(floor_match.group(1))
        # Sanity: floor numbers are typically 1-70; skip if this looks like a bedroom match
        if 2 <= floor_val <= 70:
            # Make sure it's not overlapping with the bedroom match
            if bed_match_span:
                if floor_match.start(1) >= bed_match_span[0] and floor_match.start(1) < bed_match_span[1]:
                    pass  # Skip: number is part of bedroom pattern
                else:
                    criteria["min_floor"] = floor_val
            else:
                criteria["min_floor"] = floor_val

    # "低楼层" / "low floor"
    low_floor = re.search(r'(?:low\s*floor|低楼层?)', text_no_station)
    if low_floor:
        criteria.pop("min_floor", None)  # remove any min_floor, it's a preference for low

    # --- Extract area preference ---
    area_match = re.search(r'(\d+)\s*(?:sqft|sq\s*ft|平方英尺)', text_lower)
    if area_match:
        criteria["min_area_sqft"] = int(area_match.group(1))

    # --- Extract radius ---
    radius_match = re.search(r'(\d+)\s*(?:m|米|meters?)\s*(?:radius|范围|内)', text_lower)
    if radius_match:
        criteria["radius_m"] = int(radius_match.group(1))
    km_match = re.search(r'([\d.]+)\s*(?:km|公里)\s*(?:radius|范围|内)?', text_lower)
    if km_match:
        criteria["radius_m"] = int(float(km_match.group(1)) * 1000)

    return criteria


def filter_listings(listings: list[dict], criteria: Criteria) -> list[dict]:
    """
    Apply structured criteria to filter a list of listings.
    Only filters on fields that are set in criteria.
    """
    result = []

    for listing in listings:
        # Price filter
        if "price_min" in criteria and listing.get("price"):
            if listing["price"] < criteria["price_min"]:
                continue
        if "price_max" in criteria and listing.get("price"):
            if listing["price"] > criteria["price_max"]:
                continue

        # Bedroom filter
        if "bedrooms" in criteria and listing.get("bedrooms") is not None:
            if listing["bedrooms"] != criteria["bedrooms"]:
                continue

        # Facing filter
        if "facing" in criteria and listing.get("facing"):
            listing_facing = listing["facing"].upper().strip()
            target_facing = criteria["facing"].upper()
            if target_facing not in listing_facing:
                continue

        # Floor filter
        if "min_floor" in criteria and listing.get("floor"):
            try:
                floor_num = int(re.search(r'\d+', str(listing["floor"])).group())
                if floor_num < criteria["min_floor"]:
                    continue
            except (AttributeError, ValueError):
                pass  # Can't parse floor, keep it

        # Area filter
        if "min_area_sqft" in criteria and listing.get("area_sqft"):
            if listing["area_sqft"] < criteria["min_area_sqft"]:
                continue

        result.append(listing)

    return result


def criteria_to_display(criteria: Criteria) -> str:
    """Format criteria as a human-readable string."""
    parts = []
    if "mrt_station" in criteria:
        parts.append(f"Near {criteria['mrt_station']} MRT")
    elif "location" in criteria:
        parts.append(f"Location: {criteria['location']}")
    if "bedrooms" in criteria:
        parts.append(f"{criteria['bedrooms']} bedroom(s)")
    if "price_min" in criteria or "price_max" in criteria:
        pmin = criteria.get("price_min", "any")
        pmax = criteria.get("price_max", "any")
        parts.append(f"${pmin} - ${pmax}/mo")
    if "facing" in criteria:
        parts.append(f"Facing: {criteria['facing']}")
    if "min_floor" in criteria:
        parts.append(f"Floor >= {criteria['min_floor']}")
    if "radius_m" in criteria:
        parts.append(f"Within {criteria['radius_m']}m")
    return " | ".join(parts) if parts else "No filters applied"
