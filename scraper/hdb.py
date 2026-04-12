"""Fetch HDB rental transaction data from data.gov.sg."""

import io
import requests
import pandas as pd

# Dataset: Renting Out of Flats from Jan 2021
DATASET_ID = "d_c9f57187485a850908655db0e8cfe651"
API_URL = f"https://api-open.data.gov.sg/v1/public/api/datasets/{DATASET_ID}/poll-download"

# HDB town to MRT station mapping
TOWN_TO_MRT = {
    "ANG MO KIO": ["Ang Mo Kio"],
    "BEDOK": ["Bedok", "Bedok North", "Bedok Reservoir", "Tanah Merah"],
    "BISHAN": ["Bishan"],
    "BUKIT BATOK": ["Bukit Batok", "Bukit Gombak"],
    "BUKIT MERAH": ["Redhill", "Queenstown", "Tiong Bahru"],
    "BUKIT PANJANG": ["Bukit Panjang"],
    "BUKIT TIMAH": ["Beauty World", "King Albert Park"],
    "CENTRAL": ["Dhoby Ghaut", "Clarke Quay", "Chinatown"],
    "CHOA CHU KANG": ["Choa Chu Kang"],
    "CLEMENTI": ["Clementi"],
    "GEYLANG": ["Aljunied", "Paya Lebar", "Eunos"],
    "HOUGANG": ["Hougang", "Kovan", "Buangkok"],
    "JURONG EAST": ["Jurong East"],
    "JURONG WEST": ["Boon Lay", "Pioneer", "Lakeside"],
    "KALLANG/WHAMPOA": ["Kallang", "Lavender", "Boon Keng", "Bendemeer"],
    "MARINE PARADE": ["Marine Parade", "Katong Park", "Mountbatten"],
    "PASIR RIS": ["Pasir Ris"],
    "PUNGGOL": ["Punggol"],
    "QUEENSTOWN": ["Queenstown", "Commonwealth"],
    "SEMBAWANG": ["Sembawang", "Canberra"],
    "SENGKANG": ["Sengkang"],
    "SERANGOON": ["Serangoon", "Lorong Chuan"],
    "TAMPINES": ["Tampines", "Tampines West", "Tampines East"],
    "TENGAH": [],
    "TOA PAYOH": ["Toa Payoh", "Braddell"],
    "WOODLANDS": ["Woodlands", "Admiralty", "Marsiling"],
    "YISHUN": ["Yishun", "Khatib"],
}

# Reverse mapping: MRT -> towns
MRT_TO_TOWNS: dict[str, list[str]] = {}
for town, mrts in TOWN_TO_MRT.items():
    for mrt in mrts:
        MRT_TO_TOWNS.setdefault(mrt, []).append(town)

# HDB flat type display names
FLAT_TYPE_MAP = {
    "1-ROOM": "1-Room",
    "2-ROOM": "2-Room",
    "3-ROOM": "3-Room",
    "4-ROOM": "4-Room",
    "5-ROOM": "5-Room",
    "EXECUTIVE": "Executive",
}


def fetch_hdb_rental_data(recent_months: int = 6) -> pd.DataFrame:
    """
    Fetch HDB rental transaction data from data.gov.sg.
    Aggregates recent transactions by town, flat_type, street_name.

    Returns DataFrame with columns:
      town, flat_type, street_name, block, monthly_rent, rent_approval_date,
      median_rent, min_rent, max_rent, transaction_count
    """
    resp = requests.get(API_URL, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"data.gov.sg API error: {data}")

    download_url = data["data"]["url"]
    csv_resp = requests.get(download_url, timeout=60)
    csv_resp.raise_for_status()

    df = pd.read_csv(io.StringIO(csv_resp.text))

    # Filter to recent months
    all_dates = sorted(df["rent_approval_date"].unique())
    if len(all_dates) > recent_months:
        cutoff = all_dates[-recent_months]
    else:
        cutoff = all_dates[0]
    df = df[df["rent_approval_date"] >= cutoff].copy()

    return df


def aggregate_hdb_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate HDB rental transactions by town + flat_type + street.
    Returns one row per (town, flat_type, street_name) with median/min/max rent.
    """
    agg = df.groupby(["town", "flat_type", "street_name"]).agg(
        median_rent=("monthly_rent", "median"),
        min_rent=("monthly_rent", "min"),
        max_rent=("monthly_rent", "max"),
        transaction_count=("monthly_rent", "count"),
        latest_block=("block", "first"),
        latest_date=("rent_approval_date", "max"),
    ).reset_index()

    agg["median_rent"] = agg["median_rent"].round(0).astype(int)
    return agg


def aggregate_hdb_by_town(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate by town + flat_type for overview.
    Returns one row per (town, flat_type) with stats.
    """
    agg = df.groupby(["town", "flat_type"]).agg(
        median_rent=("monthly_rent", "median"),
        p25_rent=("monthly_rent", lambda x: x.quantile(0.25)),
        p75_rent=("monthly_rent", lambda x: x.quantile(0.75)),
        min_rent=("monthly_rent", "min"),
        max_rent=("monthly_rent", "max"),
        transaction_count=("monthly_rent", "count"),
    ).reset_index()

    agg["median_rent"] = agg["median_rent"].round(0).astype(int)
    agg["p25_rent"] = agg["p25_rent"].round(0).astype(int)
    agg["p75_rent"] = agg["p75_rent"].round(0).astype(int)
    return agg


def get_towns_for_mrt(station_name: str) -> list[str]:
    """Get HDB towns near an MRT station."""
    return MRT_TO_TOWNS.get(station_name, [])


def get_all_towns() -> list[str]:
    """Return all HDB town names."""
    return sorted(TOWN_TO_MRT.keys())
