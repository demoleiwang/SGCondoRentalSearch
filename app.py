"""
SG Condo Rental Search - Interactive Streamlit Dashboard

Data source: URA rental statistics via data.gov.sg
Links to 99.co / PropertyGuru for actual listings

Usage: streamlit run app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

from config import DEFAULT_PRICE_MIN, DEFAULT_PRICE_MAX, DEFAULT_BEDROOMS, DEFAULT_RADIUS_M, SG_CENTER
from geo import find_station, get_station_names, geocode_address
from engine import parse_query, criteria_to_display, Criteria
from scraper.data_gov import (
    fetch_rental_data, get_districts_for_mrt, DISTRICT_AREAS, TYPICAL_SIZES,
    build_99co_url, build_propertyguru_url,
)

# --- Page Config ---
st.set_page_config(
    page_title="SG Condo Rental Search",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏠 SG Condo Rental Search")
st.caption("URA official rental data + links to 99.co & PropertyGuru for live listings")


# --- Cache data loading ---
@st.cache_data(ttl=3600)
def load_data():
    return fetch_rental_data()


@st.cache_data(ttl=86400)
def geocode_cached(name: str):
    """Geocode a condo project name + Singapore."""
    return geocode_address(f"{name} Singapore condo")


# --- Natural Language Input ---
nl_query = st.text_input(
    "🔍 Search (e.g. 'Queenstown 1b1b 3300' or '找Bishan附近2房4000以内')",
    placeholder="Type your search here and press Enter...",
    key="nl_query",
)

nl_criteria: Criteria = {}
if nl_query:
    nl_criteria = parse_query(nl_query)
    if nl_criteria:
        st.info(f"📋 Parsed: **{criteria_to_display(nl_criteria)}**")

# --- Sidebar Filters ---
st.sidebar.header("🔧 Filters")

# MRT Station
station_names = ["(Any)"] + get_station_names()
default_station_idx = 0
if nl_criteria.get("mrt_station"):
    try:
        default_station_idx = station_names.index(nl_criteria["mrt_station"])
    except ValueError:
        pass

selected_station = st.sidebar.selectbox(
    "MRT Station", station_names, index=default_station_idx,
)

# Bedrooms
bedrooms = st.sidebar.selectbox(
    "Bedrooms",
    [1, 2, 3, 4, 0],
    index=[1, 2, 3, 4, 0].index(nl_criteria.get("bedrooms", DEFAULT_BEDROOMS)),
    format_func=lambda x: "Studio" if x == 0 else f"{x} Bedroom{'s' if x > 1 else ''}",
)

# Price range
price_range = st.sidebar.slider(
    "Monthly Rent (SGD)",
    min_value=1000, max_value=15000,
    value=(
        nl_criteria.get("price_min", DEFAULT_PRICE_MIN),
        nl_criteria.get("price_max", DEFAULT_PRICE_MAX),
    ),
    step=100, format="$%d",
)

# Sort option
sort_by = st.sidebar.selectbox(
    "Sort by",
    ["Estimated Rent (Low to High)", "Estimated Rent (High to Low)",
     "Median PSF (Low to High)", "Rental Contracts (Most Popular)"],
)

# --- Search ---
search_clicked = st.sidebar.button("🔍 Search", type="primary", use_container_width=True)

# Quick links in sidebar
location_query = nl_criteria.get("mrt_station") or (selected_station if selected_station != "(Any)" else "")
url_99 = build_99co_url(location=location_query, bedrooms=bedrooms,
                        price_min=price_range[0], price_max=price_range[1])
url_pg = build_propertyguru_url(location=location_query, bedrooms=bedrooms,
                                price_min=price_range[0], price_max=price_range[1])
st.sidebar.markdown("---")
st.sidebar.markdown("**Browse live listings:**")
st.sidebar.markdown(f"[🔗 99.co]({url_99})")
st.sidebar.markdown(f"[🔗 PropertyGuru]({url_pg})")
st.sidebar.markdown("---")
st.sidebar.markdown("**Reference:**")
st.sidebar.markdown("[📊 URA Rental Transactions](https://www.ura.gov.sg/property-market-information/pmiResidentialRentalSearch)")
st.sidebar.markdown("[🏡 SRX](https://www.srx.com.sg/)")

# --- Main Content ---
if search_clicked or nl_query:
    # Load URA data
    with st.spinner("Loading URA rental data..."):
        try:
            df = load_data()
        except Exception as e:
            st.error(f"Failed to load data: {e}")
            st.stop()

    # --- Filter by district (MRT-based) ---
    target_station = nl_criteria.get("mrt_station") or (selected_station if selected_station != "(Any)" else None)
    station_info = find_station(target_station) if target_station else None
    target_districts = get_districts_for_mrt(target_station) if target_station else []

    if target_districts:
        filtered_df = df[df["postal_district"].isin(target_districts)].copy()
    else:
        filtered_df = df.copy()

    # --- Filter by estimated rent ---
    rent_col = f"est_rent_{bedrooms}br"
    if rent_col in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df[rent_col] >= price_range[0]) &
            (filtered_df[rent_col] <= price_range[1])
        ].copy()

    # --- Sort ---
    if "Low to High" in sort_by and "PSF" in sort_by:
        filtered_df = filtered_df.sort_values("median_psf")
    elif "High to Low" in sort_by:
        filtered_df = filtered_df.sort_values(rent_col, ascending=False)
    elif "Most Popular" in sort_by:
        filtered_df = filtered_df.sort_values("rental_contracts", ascending=False)
    else:
        filtered_df = filtered_df.sort_values(rent_col)

    # --- Results Header ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Condo Projects", len(filtered_df))
    with col2:
        if not filtered_df.empty:
            avg_rent = int(filtered_df[rent_col].mean())
            st.metric(f"Avg {bedrooms}BR Rent", f"${avg_rent:,}")
        else:
            st.metric(f"Avg {bedrooms}BR Rent", "N/A")
    with col3:
        if not filtered_df.empty:
            st.metric("Rent Range",
                       f"${int(filtered_df[rent_col].min()):,} - ${int(filtered_df[rent_col].max()):,}")
        else:
            st.metric("Rent Range", "N/A")
    with col4:
        if target_districts:
            areas = ", ".join([DISTRICT_AREAS.get(d, str(d)) for d in target_districts])
            st.metric("Area", areas[:30])
        else:
            st.metric("Area", "All Singapore")

    # --- Map ---
    st.subheader("📍 Map")
    center_lat, center_lng = SG_CENTER
    zoom = 12
    if station_info:
        center_lat, center_lng = station_info["lat"], station_info["lng"]
        zoom = 14

    m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom, tiles="CartoDB positron")

    # MRT marker
    if station_info:
        folium.Marker(
            [station_info["lat"], station_info["lng"]],
            popup=f"🚇 {station_info['name']} MRT ({station_info['code']})",
            tooltip=f"🚇 {station_info['name']} MRT",
            icon=folium.Icon(color="red", icon="train", prefix="fa"),
        ).add_to(m)
        folium.Circle(
            [station_info["lat"], station_info["lng"]],
            radius=DEFAULT_RADIUS_M,
            color="red", fill=True, fill_opacity=0.05, weight=1,
        ).add_to(m)

    # Geocode and add condo markers (limit to avoid API overload)
    geocode_limit = min(len(filtered_df), 30)
    geocoded_count = 0
    for _, row in filtered_df.head(geocode_limit).iterrows():
        coords = geocode_cached(row["project_name"])
        if coords:
            lat, lng = coords
            est_rent = int(row[rent_col])
            url_99_project = build_99co_url(project_name=row["project_name"],
                                            bedrooms=bedrooms, price_min=price_range[0], price_max=price_range[1])
            popup_html = f"""
            <div style="min-width:220px;">
                <b>{row['project_name']}</b><br>
                📍 District {row['postal_district']} - {row['district_area']}<br>
                💰 Est. {bedrooms}BR: <b>${est_rent:,}/mo</b><br>
                📊 Median ${row['median_psf']:.2f} psf | P25-P75: ${row['p25_psf']:.2f}-${row['p75_psf']:.2f}<br>
                📝 {int(row['rental_contracts'])} contracts last quarter<br>
                <a href="{url_99_project}" target="_blank">Search on 99.co →</a>
            </div>
            """
            # Color code by price
            if est_rent < price_range[0] + (price_range[1] - price_range[0]) * 0.33:
                color = "green"
            elif est_rent < price_range[0] + (price_range[1] - price_range[0]) * 0.66:
                color = "blue"
            else:
                color = "orange"

            folium.Marker(
                [lat, lng],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"${est_rent:,} - {row['project_name']}",
                icon=folium.Icon(color=color, icon="home", prefix="fa"),
            ).add_to(m)
            geocoded_count += 1

    st_folium(m, width=None, height=500, use_container_width=True)
    if geocoded_count < len(filtered_df):
        st.caption(f"Showing {geocoded_count} of {len(filtered_df)} projects on map (geocoding limit)")

    # --- Condo Project Cards ---
    st.subheader(f"📋 Condo Projects ({len(filtered_df)})")

    if filtered_df.empty:
        st.warning("No condo projects match your criteria. Try adjusting filters.")
        st.markdown(f"**Browse live listings on [99.co]({url_99}) or [PropertyGuru]({url_pg})**")
    else:
        typical_size = TYPICAL_SIZES.get(bedrooms, 530)

        for _, row in filtered_df.iterrows():
            est_rent = int(row[rent_col])
            url_99_project = build_99co_url(
                project_name=row["project_name"], bedrooms=bedrooms,
                price_min=int(est_rent * 0.85), price_max=int(est_rent * 1.15),
            )
            url_pg_project = build_propertyguru_url(
                project_name=row["project_name"], bedrooms=bedrooms,
                price_min=int(est_rent * 0.85), price_max=int(est_rent * 1.15),
            )

            with st.container():
                col_info, col_stats, col_links = st.columns([3, 2, 2])

                with col_info:
                    st.markdown(f"**{row['project_name']}**")
                    st.caption(
                        f"📍 District {row['postal_district']} - {row['district_area']}  \n"
                        f"📝 {int(row['rental_contracts'])} rental contracts (last quarter)"
                    )

                with col_stats:
                    st.markdown(f"### ${est_rent:,}/mo")
                    st.caption(
                        f"Est. {bedrooms}BR ({typical_size} sqft)  \n"
                        f"Median ${row['median_psf']:.2f} psf | "
                        f"Range ${row['p25_psf']:.2f} - ${row['p75_psf']:.2f} psf"
                    )

                with col_links:
                    st.markdown(f"[🔗 Search on 99.co]({url_99_project})")
                    st.markdown(f"[🔗 Search on PropertyGuru]({url_pg_project})")
                    ura_url = "https://www.ura.gov.sg/property-market-information/pmiResidentialRentalSearch"
                    st.markdown(f"[📊 URA History]({ura_url})")

                st.divider()

    # --- Data Table ---
    with st.expander("📊 Full Data Table"):
        if not filtered_df.empty:
            display_df = filtered_df[["project_name", "postal_district", "district_area",
                                       "median_psf", "p25_psf", "p75_psf",
                                       "rental_contracts", rent_col]].copy()
            display_df = display_df.rename(columns={
                "project_name": "Project",
                "postal_district": "District",
                "district_area": "Area",
                "median_psf": "Median PSF",
                "p25_psf": "P25 PSF",
                "p75_psf": "P75 PSF",
                "rental_contracts": "Contracts",
                rent_col: f"Est. {bedrooms}BR Rent",
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    # --- Tip ---
    with st.expander("💡 Tips for finding the best deal"):
        st.markdown(f"""
        **Your search:** {criteria_to_display(nl_criteria) if nl_criteria else criteria_to_display({"bedrooms": bedrooms, "price_min": price_range[0], "price_max": price_range[1]})}

        **How to use this data:**
        1. The rent estimates are based on URA Q4 2025 official data (median $/psf x {typical_size} sqft typical {bedrooms}BR size)
        2. Click the **99.co** or **PropertyGuru** links on each project to see actual current listings
        3. The **P25-P75 range** shows you the bargaining range - aim for P25 or below
        4. Projects with more **rental contracts** have more data points and thus more reliable pricing

        **Negotiation tips from the rental guide:**
        - Google "*condo name* + brochure" to find the floor plan and exact unit sizes
        - Unit number format: `xx-xx` (floor-unit), use it to find the exact layout
        - Check **URA Rental Transactions** for that specific condo's transaction history
        - Use historical data as leverage when negotiating rent
        """)

else:
    # --- Welcome Screen ---
    st.markdown("""
    ### How to use

    **Option 1: Natural Language**
    Type in the search box, e.g.:
    - `Queenstown 1b1b 3300` → 1BR condos near Queenstown MRT, ~$3300/mo
    - `找Bishan附近的2房condo，预算4000以内` → 2BR near Bishan, max $4000
    - `Paya Lebar 1 bedroom 3000-3500` → 1BR near Paya Lebar, $3000-$3500

    **Option 2: Sidebar Filters**
    Select MRT station, bedroom count, and price range, then click **Search**.

    ---

    **Data:** URA official rental statistics (Q4 2025, 551 condo projects).
    Estimated monthly rent = median $/psf × typical unit size.
    Click through to **99.co** or **PropertyGuru** for actual live listings.
    """)

    st.subheader("Popular Searches")
    popular = [
        ("Queenstown 1BR", "Queenstown 1b1b 3300"),
        ("Bishan 2BR", "Bishan 2 bedroom 4000"),
        ("Toa Payoh 1BR", "Toa Payoh 1b1b 2800"),
        ("Paya Lebar 1BR", "Paya Lebar 1 bedroom 3500"),
        ("Holland Village 1BR", "Holland Village 1b1b 3500"),
        ("Novena 2BR", "Novena 2 bedroom 5000"),
        ("Tiong Bahru 1BR", "Tiong Bahru 1b1b 3200"),
        ("Orchard 1BR", "Orchard 1 bedroom 4000"),
        ("Buona Vista 1BR", "Buona Vista 1b1b 3000"),
        ("Clementi 2BR", "Clementi 2 bedroom 3500"),
    ]
    cols = st.columns(5)
    for i, (label, query) in enumerate(popular):
        with cols[i % 5]:
            if st.button(label, key=f"pop_{i}", use_container_width=True):
                st.session_state["nl_query"] = query
                st.rerun()
