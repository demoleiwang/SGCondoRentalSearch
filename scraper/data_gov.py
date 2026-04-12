"""Fetch condo rental data from data.gov.sg (URA source)."""

import io
import os
import time
from pathlib import Path

import requests
import pandas as pd

# Local cache directory
_CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_CONDO_CACHE = _CACHE_DIR / "condo_rental.csv"
_CACHE_TTL = 86400  # 24 hours

# Dataset: Rentals of Non-Landed Residential Buildings, Quarterly
DATASET_ID = "d_149ac00a2734bb0a03867bbe2ec0e7b0"
API_URL = f"https://api-open.data.gov.sg/v1/public/api/datasets/{DATASET_ID}/poll-download"

# Postal district to area mapping
DISTRICT_AREAS = {
    1: "Raffles Place, Marina",
    2: "Tanjong Pagar, Chinatown",
    3: "Queenstown, Tiong Bahru, Alexandra",
    4: "Harbourfront, Telok Blangah",
    5: "Buona Vista, Clementi, Pasir Panjang",
    7: "Beach Road, Bugis, Rochor",
    8: "Farrer Park, Little India",
    9: "Orchard, River Valley",
    10: "Tanglin, Holland",
    11: "Newton, Novena, Thomson",
    12: "Toa Payoh, Balestier",
    13: "Macpherson, Potong Pasir",
    14: "Eunos, Geylang, Paya Lebar",
    15: "East Coast, Marine Parade, Katong",
    16: "Bedok, Upper East Coast",
    17: "Changi, Loyang",
    18: "Tampines, Pasir Ris",
    19: "Serangoon, Hougang, Punggol",
    20: "Bishan, Ang Mo Kio",
    21: "Clementi, Upper Bukit Timah",
    22: "Jurong, Boon Lay",
    23: "Bukit Batok, Bukit Panjang, Choa Chu Kang",
    25: "Woodlands, Admiralty",
    26: "Mandai, Upper Thomson",
    27: "Yishun, Sembawang",
    28: "Seletar, Yio Chu Kang",
}

# MRT station to district mapping (approximate)
MRT_TO_DISTRICT = {
    "Raffles Place": [1], "Marina Bay": [1], "Marina South Pier": [1],
    "Tanjong Pagar": [2], "Chinatown": [2], "Outram Park": [2, 3],
    "Queenstown": [3], "Commonwealth": [3], "Redhill": [3], "Tiong Bahru": [3],
    "HarbourFront": [4], "Telok Blangah": [4], "Labrador Park": [4],
    "Buona Vista": [5], "Clementi": [5, 21], "Dover": [5], "one-north": [5],
    "Kent Ridge": [5], "Pasir Panjang": [5], "Haw Par Villa": [5],
    "Bugis": [7], "Lavender": [7, 8], "Rochor": [7],
    "Farrer Park": [8], "Boon Keng": [8],
    "Little India": [8],
    "Orchard": [9, 10], "Somerset": [9],
    "Newton": [11], "Novena": [11], "Stevens": [11],
    "Holland Village": [10], "Farrer Road": [10],
    "Botanic Gardens": [10, 11],
    "Toa Payoh": [12], "Braddell": [12], "Caldecott": [12],
    "Marymount": [20], "Bishan": [20], "Ang Mo Kio": [20],
    "Serangoon": [19], "Kovan": [19], "Hougang": [19],
    "Punggol": [19], "Sengkang": [19], "Buangkok": [19],
    "Paya Lebar": [14], "Eunos": [14], "Aljunied": [14],
    "Kembangan": [14, 15], "Bedok": [16], "Tanah Merah": [16],
    "Simei": [16], "Tampines": [18], "Pasir Ris": [18],
    "Dhoby Ghaut": [9], "City Hall": [1, 7],
    "Kallang": [7, 8], "Mountbatten": [15], "Dakota": [14, 15],
    "Stadium": [7], "Nicoll Highway": [7],
    "MacPherson": [13], "Tai Seng": [13], "Bartley": [13, 19],
    "Potong Pasir": [13], "Woodleigh": [13],
    "Lorong Chuan": [19],
    "Jurong East": [22], "Boon Lay": [22], "Lakeside": [22],
    "Chinese Garden": [22], "Pioneer": [22],
    "Bukit Batok": [23], "Bukit Gombak": [23],
    "Bukit Panjang": [23], "Choa Chu Kang": [23],
    "Woodlands": [25], "Admiralty": [25], "Marsiling": [25],
    "Sembawang": [27], "Yishun": [27], "Canberra": [27],
    "Yio Chu Kang": [28], "Khatib": [27],
    "Bedok North": [16], "Bedok Reservoir": [16],
    "Tampines West": [18], "Tampines East": [18],
    "Katong Park": [15], "Tanjong Katong": [15],
    "Marine Parade": [15], "Marine Terrace": [15],
    "Siglap": [15], "Bayshore": [16],
    "Great World": [9], "Havelock": [3],
    "Upper Thomson": [26], "Bright Hill": [20],
    "Lentor": [26], "Mayflower": [20],
    "King Albert Park": [21], "Beauty World": [21],
    "Sixth Avenue": [10], "Tan Kah Kee": [10, 21],
    "Hillview": [23], "Cashew": [23],
}

# Typical unit sizes by bedroom count (sqft)
TYPICAL_SIZES = {
    0: 450,   # studio
    1: 530,   # 1 bedroom
    2: 750,   # 2 bedrooms
    3: 1100,  # 3 bedrooms
    4: 1400,  # 4 bedrooms
    5: 1800,  # 5+ bedrooms
}


def _download_csv(api_url: str, cache_path: Path) -> str:
    """Download CSV from data.gov.sg and cache locally. Returns CSV text."""
    # Use cache if fresh
    if cache_path.exists():
        age = time.time() - cache_path.stat().st_mtime
        if age < _CACHE_TTL:
            return cache_path.read_text()

    resp = requests.get(api_url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0 or data.get("data", {}).get("status") != "DOWNLOAD_SUCCESS":
        # If API fails but cache exists (even stale), use it
        if cache_path.exists():
            return cache_path.read_text()
        raise RuntimeError(f"data.gov.sg API error: {data}")

    download_url = data["data"]["url"]
    csv_resp = requests.get(download_url, timeout=60)
    csv_resp.raise_for_status()

    # Save to cache
    cache_path.write_text(csv_resp.text)
    return csv_resp.text


def fetch_rental_data() -> pd.DataFrame:
    """
    Fetch latest URA condo rental data from data.gov.sg.
    Uses local file cache (24h TTL) to avoid rate limits.
    """
    csv_text = _download_csv(API_URL, _CONDO_CACHE)
    df = pd.read_csv(io.StringIO(csv_text))

    # Use latest quarter only
    latest_qtr = df["qtr"].max()
    df = df[df["qtr"] == latest_qtr].copy()

    # Add area descriptions
    df["district_area"] = df["postal_district"].map(DISTRICT_AREAS).fillna("Other")

    # Rename for clarity
    df = df.rename(columns={
        "25th_percentile": "p25_psf",
        "median": "median_psf",
        "75th_percentile": "p75_psf",
    })

    # Estimate total monthly rent for each unit type
    for beds, size in TYPICAL_SIZES.items():
        col_name = f"est_rent_{beds}br"
        df[col_name] = (df["median_psf"] * size).round(0).astype(int)

    return df


def get_districts_for_mrt(station_name: str) -> list[int]:
    """Get postal districts near an MRT station."""
    return MRT_TO_DISTRICT.get(station_name, [])


def build_99co_url(project_name: str = "", location: str = "",
                   bedrooms: int | None = None,
                   price_min: int | None = None,
                   price_max: int | None = None) -> str:
    """Build 99.co search URL for a specific condo or area."""
    base = "https://www.99.co/singapore/rent/condos-apartments"
    params = []
    query = project_name or location
    if query:
        params.append(f"query={requests.utils.quote(query)}")
    if bedrooms is not None:
        params.append(f"bedroom_num={bedrooms}")
    if price_min is not None and price_max is not None:
        params.append(f"rental_range={price_min}-{price_max}")
    elif price_max is not None:
        params.append(f"rental_range=any-{price_max}")
    elif price_min is not None:
        params.append(f"rental_range={price_min}-any")
    return f"{base}?{'&'.join(params)}" if params else base


def build_propertyguru_url(project_name: str = "", location: str = "",
                           bedrooms: int | None = None,
                           price_min: int | None = None,
                           price_max: int | None = None) -> str:
    """Build PropertyGuru search URL."""
    base = "https://www.propertyguru.com.sg/property-for-rent"
    params = ["market=residential", "property_type=C"]
    query = project_name or location
    if query:
        params.append(f"freetext={requests.utils.quote(query)}")
    if bedrooms is not None:
        params.append(f"bedroom_num={bedrooms}")
    if price_min is not None:
        params.append(f"minprice={price_min}")
    if price_max is not None:
        params.append(f"maxprice={price_max}")
    return f"{base}?{'&'.join(params)}"
