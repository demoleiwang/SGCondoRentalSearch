"""
Smart Search: auto-expand a natural language query into multiple search strategies.

Given "SMU附近 1br 3300", the system:
1. Recognizes "SMU" as a landmark → geocodes it
2. Finds nearby MRT stations (Bras Basah, City Hall, Dhoby Ghaut, etc.)
3. Identifies walkable areas (Orchard is ~1km from SMU)
4. Generates multiple search strategies from different angles
5. Runs each through the existing condo/HDB data
6. Aggregates and returns all results with reasoning
"""

import re
from dataclasses import dataclass, field

from geo import geocode_address, get_stations_within_radius, haversine, find_station
from engine import parse_query, Criteria
from scraper.data_gov import (
    fetch_rental_data, get_districts_for_mrt, DISTRICT_AREAS, TYPICAL_SIZES,
    build_propertyguru_url, build_google_search_url,
)

# Try to use current UI language; fall back to English when Streamlit isn't active
try:
    from i18n import get_lang as _get_lang
except Exception:  # pragma: no cover
    def _get_lang() -> str:
        return "en"

# In-memory geocode cache
_geocode_cache: dict[str, tuple[float, float] | None] = {}


def _cached_geocode(query: str) -> tuple[float, float] | None:
    if query not in _geocode_cache:
        _geocode_cache[query] = geocode_address(query)
    return _geocode_cache[query]


# Common Singapore landmarks that users might mention
LANDMARKS = {
    # Universities
    "smu": "Singapore Management University",
    "nus": "National University of Singapore",
    "ntu": "Nanyang Technological University",
    "sutd": "Singapore University of Technology and Design",
    "sim": "Singapore Institute of Management",
    "sit": "Singapore Institute of Technology",
    # Business areas
    "cbd": "Raffles Place Singapore",
    "marina bay financial centre": "Marina Bay Financial Centre",
    "mbfc": "Marina Bay Financial Centre",
    "oue downtown": "OUE Downtown One",
    "mapletree business city": "Mapletree Business City",
    "one-north": "one-north Singapore",
    "changi business park": "Changi Business Park",
    "science park": "Singapore Science Park",
    # Hospitals
    "sgh": "Singapore General Hospital",
    "nuh": "National University Hospital",
    "ttsh": "Tan Tock Seng Hospital",
    # Others
    "orchard": "Orchard Road Singapore",
    "sentosa": "Sentosa Singapore",
    "changi airport": "Changi Airport Singapore",
    "jewel": "Jewel Changi Airport",
}


@dataclass
class SearchStrategy:
    """A single search strategy with reasoning."""
    name: str               # e.g. "Bras Basah MRT (最近站, 178m)"
    reason: str             # why this strategy
    station: str            # MRT station name
    distance_m: int         # distance from landmark to this station
    criteria: Criteria      # parsed search criteria
    query_text: str         # the query string


@dataclass
class SearchResult:
    """A condo/project result from one strategy."""
    project_name: str
    district: int
    area_desc: str
    est_rent: int
    median_psf: float
    contracts: int
    strategy_name: str
    url_propertyguru: str
    url_google: str = ""
    # P25/P75 rent estimates (derived from psf percentiles * typical size).
    # 0 when upstream data lacks percentile columns.
    est_rent_p25: int = 0
    est_rent_p75: int = 0
    # Median est-rent for this project's district at the requested bedroom count.
    # Used to render a "vs area median" badge. 0 when district-only dataset is empty.
    district_median_rent: int = 0


@dataclass
class SmartSearchResult:
    """Aggregated results from all strategies."""
    landmark_name: str
    landmark_address: str
    landmark_coords: tuple[float, float] | None
    strategies: list[SearchStrategy]
    results: list[SearchResult]    # all results, deduplicated
    summary: str                   # human-readable summary


def detect_landmark(text: str) -> tuple[str, str] | None:
    """
    Detect if the query mentions a landmark.
    Returns (landmark_key, full_address) or None.
    """
    text_lower = text.lower()
    # Check longest keys first to avoid partial matches
    for key in sorted(LANDMARKS.keys(), key=len, reverse=True):
        if key in text_lower:
            return key, LANDMARKS[key]
    return None


def expand_query(text: str, radius_m: int = 1500) -> SmartSearchResult | None:
    """
    Given a natural language query mentioning a landmark or address,
    expand it into multiple search strategies.

    Returns SmartSearchResult with all strategies and aggregated results,
    or None if no landmark/location detected.
    """
    # Parse base criteria
    base_criteria = parse_query(text)

    # Detect landmark
    landmark = detect_landmark(text)
    if landmark:
        landmark_key, landmark_addr = landmark
    elif base_criteria.get("mrt_station"):
        # If just an MRT station, use its known coordinates directly
        station_info = find_station(base_criteria["mrt_station"])
        if station_info:
            landmark_key = base_criteria["mrt_station"]
            landmark_addr = base_criteria["mrt_station"] + " MRT"
        else:
            return None
    else:
        return None

    # Get coordinates: use station DB for MRT stations, geocode for landmarks
    if not landmark and base_criteria.get("mrt_station"):
        station_info = find_station(base_criteria["mrt_station"])
        coords = (station_info["lat"], station_info["lng"]) if station_info else None
    else:
        coords = _cached_geocode(landmark_addr)
    if not coords:
        return None

    lat, lng = coords

    # Find nearby MRT stations
    nearby = get_stations_within_radius(lat, lng, radius_m)
    if not nearby:
        return None

    # Build strategies
    strategies = []
    bedrooms = base_criteria.get("bedrooms", 1)
    price_min = base_criteria.get("price_min")
    price_max = base_criteria.get("price_max")
    extra_parts = []
    if base_criteria.get("facing"):
        extra_parts.append(f"{base_criteria['facing'].lower()} facing")
    if base_criteria.get("min_floor"):
        extra_parts.append(f"high floor")
    extra = " ".join(extra_parts)

    lang = _get_lang()
    for station_name, dist_m in nearby:
        # Build reason (language-aware)
        if lang == "zh":
            if dist_m < 300:
                reason = f"最近MRT站，步行{int(dist_m)}米"
            elif dist_m < 600:
                reason = f"步行可达，约{int(dist_m)}米 ({int(dist_m/80)}分钟)"
            elif dist_m < 1000:
                reason = f"较近，约{int(dist_m)}米，可步行或搭巴士"
            else:
                reason = f"附近区域，约{int(dist_m)}米，可能更便宜"
        else:
            if dist_m < 300:
                reason = f"Closest MRT, ~{int(dist_m)}m walk"
            elif dist_m < 600:
                reason = f"Walkable, ~{int(dist_m)}m ({int(dist_m/80)} min)"
            elif dist_m < 1000:
                reason = f"Nearby, ~{int(dist_m)}m (walk or bus)"
            else:
                reason = f"Nearby area, ~{int(dist_m)}m (often cheaper)"

        # Get station's MRT lines for extra context
        s_info = find_station(station_name)
        if s_info:
            lines = "/".join(s_info.get("line", []))
            reason += f" [{lines}]" if lang != "zh" else f" [{lines}线]"

        # Build query
        bed_part = f"{bedrooms}b{bedrooms}b" if bedrooms <= 2 else f"{bedrooms}br"
        price_part = ""
        if price_min and price_max:
            price_part = f"{price_min}-{price_max}"
        elif price_max:
            price_part = f"{price_max}以内"
        elif price_min:
            price_part = str(price_min)

        query_text = f"{station_name} {bed_part} {price_part} {extra}".strip()
        criteria = parse_query(query_text)

        strategies.append(SearchStrategy(
            name=f"{station_name} ({int(dist_m)}m)",
            reason=reason,
            station=station_name,
            distance_m=int(dist_m),
            criteria=criteria,
            query_text=query_text,
        ))

    # Run searches against condo data
    results = _run_searches(strategies, bedrooms)

    # Build summary
    summary = _build_summary(landmark_key, landmark_addr, strategies, results)

    return SmartSearchResult(
        landmark_name=landmark_key,
        landmark_address=landmark_addr,
        landmark_coords=coords,
        strategies=strategies,
        results=results,
        summary=summary,
    )


def _run_searches(strategies: list[SearchStrategy], bedrooms: int) -> list[SearchResult]:
    """Run all strategies against condo data and return deduplicated results."""
    try:
        df = fetch_rental_data()
    except Exception:
        return []

    rent_col = f"est_rent_{bedrooms}br"
    if rent_col not in df.columns:
        return []

    # Typical unit size for this bedroom count — needed to turn psf percentiles
    # into dollar rents for P25/P75 badges.
    typical_size = TYPICAL_SIZES.get(bedrooms, 0)

    # Precompute median rent per district for the "vs area" badge.
    district_median_map: dict[int, int] = {}
    if rent_col in df.columns:
        grouped = df.groupby("postal_district")[rent_col].median().round(0).astype(int)
        district_median_map = grouped.to_dict()

    seen_projects = set()
    results = []

    for strategy in strategies:
        districts = get_districts_for_mrt(strategy.station)
        if not districts:
            continue

        area_df = df[df["postal_district"].isin(districts)].copy()

        # Apply price filter
        c = strategy.criteria
        if c.get("price_min"):
            area_df = area_df[area_df[rent_col] >= c["price_min"]]
        if c.get("price_max"):
            area_df = area_df[area_df[rent_col] <= c["price_max"]]

        area_df = area_df.sort_values(rent_col)

        for _, row in area_df.iterrows():
            pname = row["project_name"]
            if pname in seen_projects:
                continue
            seen_projects.add(pname)

            est_rent = int(row[rent_col])
            p25_psf = float(row.get("p25_psf", 0) or 0)
            p75_psf = float(row.get("p75_psf", 0) or 0)
            est_rent_p25 = int(round(p25_psf * typical_size)) if typical_size and p25_psf else 0
            est_rent_p75 = int(round(p75_psf * typical_size)) if typical_size and p75_psf else 0
            district = int(row["postal_district"])
            results.append(SearchResult(
                project_name=pname,
                district=district,
                area_desc=row.get("district_area", ""),
                est_rent=est_rent,
                median_psf=row["median_psf"],
                contracts=int(row["rental_contracts"]),
                strategy_name=strategy.name,
                url_propertyguru=build_propertyguru_url(project_name=pname, bedrooms=bedrooms,
                                                        price_min=int(est_rent * 0.85),
                                                        price_max=int(est_rent * 1.15)),
                url_google=build_google_search_url(project_name=pname, bedrooms=bedrooms),
                est_rent_p25=est_rent_p25,
                est_rent_p75=est_rent_p75,
                district_median_rent=int(district_median_map.get(district, 0)),
            ))

    # Sort by rent
    results.sort(key=lambda r: r.est_rent)
    return results


def _build_summary(landmark_key: str, landmark_addr: str,
                   strategies: list[SearchStrategy],
                   results: list[SearchResult]) -> str:
    """Build human-readable summary of the smart search (language-aware)."""
    lang = _get_lang()
    lines = []

    if lang == "zh":
        lines.append(f"## 🔍 Smart Search: {landmark_key.upper()} 附近租房分析\n")
        lines.append(f"**目标位置**: {landmark_addr}\n")
        lines.append(f"### 搜索思路 ({len(strategies)} 个方向)\n")
        for i, s in enumerate(strategies, 1):
            count = sum(1 for r in results if r.strategy_name == s.name)
            lines.append(f"{i}. **{s.name}** — {s.reason} → {count} 个condo")
        lines.append(f"\n### 搜索结果 (共 {len(results)} 个condo)\n")
        if results:
            prices = [r.est_rent for r in results]
            lines.append(f"- 租金范围: ${min(prices):,} - ${max(prices):,}/月")
            lines.append(f"- 中位租金: ${sorted(prices)[len(prices)//2]:,}/月")
            lines.append("\n### 按区域分组\n")
            by_strategy: dict[str, list[SearchResult]] = {}
            for r in results:
                by_strategy.setdefault(r.strategy_name, []).append(r)
            for sname, sresults in by_strategy.items():
                lines.append(f"**{sname}** ({len(sresults)} 个condo)")
                for r in sresults[:3]:
                    lines.append(f"  - {r.project_name}: ${r.est_rent:,}/月 "
                                 f"(${r.median_psf:.2f} psf, {r.contracts} contracts)")
                if len(sresults) > 3:
                    lines.append(f"  - ... 还有 {len(sresults) - 3} 个")
                lines.append("")
    else:
        lines.append(f"## 🔍 Smart Search: rentals near {landmark_key.upper()}\n")
        lines.append(f"**Target**: {landmark_addr}\n")
        lines.append(f"### Search strategies ({len(strategies)})\n")
        for i, s in enumerate(strategies, 1):
            count = sum(1 for r in results if r.strategy_name == s.name)
            lines.append(f"{i}. **{s.name}** — {s.reason} → {count} condos")
        lines.append(f"\n### Results ({len(results)} condos total)\n")
        if results:
            prices = [r.est_rent for r in results]
            lines.append(f"- Rent range: ${min(prices):,} - ${max(prices):,}/mo")
            lines.append(f"- Median rent: ${sorted(prices)[len(prices)//2]:,}/mo")
            lines.append("\n### Grouped by area\n")
            by_strategy: dict[str, list[SearchResult]] = {}
            for r in results:
                by_strategy.setdefault(r.strategy_name, []).append(r)
            for sname, sresults in by_strategy.items():
                lines.append(f"**{sname}** ({len(sresults)} condos)")
                for r in sresults[:3]:
                    lines.append(f"  - {r.project_name}: ${r.est_rent:,}/mo "
                                 f"(${r.median_psf:.2f} psf, {r.contracts} contracts)")
                if len(sresults) > 3:
                    lines.append(f"  - ... and {len(sresults) - 3} more")
                lines.append("")

    return "\n".join(lines)
