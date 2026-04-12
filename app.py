"""
SG Rental Search - Interactive Streamlit Dashboard

Data: URA condo stats + HDB rental transactions via data.gov.sg
Links to 99.co / PropertyGuru for live listings

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
from scraper.hdb import (
    fetch_hdb_rental_data, aggregate_hdb_by_town, aggregate_hdb_data,
    get_towns_for_mrt, FLAT_TYPE_MAP,
)

# --- Page Config ---
st.set_page_config(
    page_title="SG Rental Search",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏠 SG Rental Search")
st.caption("URA & HDB official data + links to 99.co & PropertyGuru")


# --- Cache ---
@st.cache_data(ttl=3600)
def load_condo_data():
    return fetch_rental_data()


@st.cache_data(ttl=3600)
def load_hdb_data():
    return fetch_hdb_rental_data(recent_months=6)


@st.cache_data(ttl=86400)
def geocode_cached(name: str):
    return geocode_address(name)


# --- Natural Language Input ---
nl_query = st.text_input(
    "🔍 Search (e.g. 'Queenstown 1b1b 3300' or '找Bishan附近HDB 3房2500')",
    placeholder="Type your search here and press Enter...",
    key="nl_query",
)

nl_criteria: Criteria = {}
if nl_query:
    nl_criteria = parse_query(nl_query)
    if nl_criteria:
        st.info(f"📋 Parsed: **{criteria_to_display(nl_criteria)}**")

# --- Sidebar ---
st.sidebar.header("🔧 Filters")

# Property type toggle
property_type = st.sidebar.radio(
    "Property Type",
    ["🏢 Condo", "🏘️ HDB", "🏢+🏘️ Both"],
    index=0,
    horizontal=True,
)
show_condo = property_type in ["🏢 Condo", "🏢+🏘️ Both"]
show_hdb = property_type in ["🏘️ HDB", "🏢+🏘️ Both"]

# MRT Station
station_names = ["(Any)"] + get_station_names()
default_station_idx = 0
if nl_criteria.get("mrt_station"):
    try:
        default_station_idx = station_names.index(nl_criteria["mrt_station"])
    except ValueError:
        pass

selected_station = st.sidebar.selectbox("MRT Station", station_names, index=default_station_idx)

# --- Condo-specific filters ---
if show_condo:
    st.sidebar.markdown("**Condo Filters**")
    condo_bedrooms = st.sidebar.selectbox(
        "Condo Bedrooms",
        [1, 2, 3, 4, 0],
        index=[1, 2, 3, 4, 0].index(nl_criteria.get("bedrooms", DEFAULT_BEDROOMS)),
        format_func=lambda x: "Studio" if x == 0 else f"{x} Bedroom{'s' if x > 1 else ''}",
    )
    condo_price = st.sidebar.slider(
        "Condo Monthly Rent (SGD)",
        min_value=1000, max_value=15000,
        value=(nl_criteria.get("price_min", DEFAULT_PRICE_MIN),
               nl_criteria.get("price_max", DEFAULT_PRICE_MAX)),
        step=100, format="$%d",
    )

# --- HDB-specific filters ---
if show_hdb:
    st.sidebar.markdown("**HDB Filters**")
    hdb_flat_types = st.sidebar.multiselect(
        "Flat Type",
        ["2-ROOM", "3-ROOM", "4-ROOM", "5-ROOM", "EXECUTIVE"],
        default=["3-ROOM"],
        format_func=lambda x: FLAT_TYPE_MAP.get(x, x),
    )
    hdb_price = st.sidebar.slider(
        "HDB Monthly Rent (SGD)",
        min_value=500, max_value=8000,
        value=(nl_criteria.get("price_min", 1500),
               min(nl_criteria.get("price_max", 4000), 8000)),
        step=100, format="$%d",
    )

# Sort
sort_by = st.sidebar.selectbox(
    "Sort by",
    ["Rent (Low to High)", "Rent (High to Low)", "Most Popular"],
)

# Search
search_clicked = st.sidebar.button("🔍 Search", type="primary", use_container_width=True)

# Links
location_query = nl_criteria.get("mrt_station") or (selected_station if selected_station != "(Any)" else "")
st.sidebar.markdown("---")
st.sidebar.markdown("**Browse live listings:**")
url_99 = build_99co_url(location=location_query)
url_pg = build_propertyguru_url(location=location_query)
st.sidebar.markdown(f"[🔗 99.co]({url_99}) | [🔗 PropertyGuru]({url_pg})")
st.sidebar.markdown("[📊 URA Rental](https://www.ura.gov.sg/property-market-information/pmiResidentialRentalSearch) | [🏡 SRX](https://www.srx.com.sg/)")

# =========================================================================
# MAIN CONTENT
# =========================================================================
if search_clicked or nl_query:
    target_station = nl_criteria.get("mrt_station") or (selected_station if selected_station != "(Any)" else None)
    station_info = find_station(target_station) if target_station else None

    # Map setup
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
            radius=DEFAULT_RADIUS_M, color="red", fill=True, fill_opacity=0.05, weight=1,
        ).add_to(m)

    # ==== CONDO TAB / HDB TAB ====
    if show_condo and show_hdb:
        tab_condo, tab_hdb = st.tabs(["🏢 Condo", "🏘️ HDB"])
    elif show_condo:
        tab_condo = st.container()
        tab_hdb = None
    else:
        tab_condo = None
        tab_hdb = st.container()

    # ======================== CONDO ========================
    if show_condo:
        with tab_condo:
            with st.spinner("Loading condo data..."):
                try:
                    condo_df = load_condo_data()
                except Exception as e:
                    st.error(f"Failed to load condo data: {e}")
                    condo_df = pd.DataFrame()

            if not condo_df.empty:
                # Filter by district
                target_districts = get_districts_for_mrt(target_station) if target_station else []
                if target_districts:
                    filtered_condo = condo_df[condo_df["postal_district"].isin(target_districts)].copy()
                else:
                    filtered_condo = condo_df.copy()

                # Filter by estimated rent
                rent_col = f"est_rent_{condo_bedrooms}br"
                if rent_col in filtered_condo.columns:
                    filtered_condo = filtered_condo[
                        (filtered_condo[rent_col] >= condo_price[0]) &
                        (filtered_condo[rent_col] <= condo_price[1])
                    ].copy()

                # Sort
                if "High to Low" in sort_by:
                    filtered_condo = filtered_condo.sort_values(rent_col, ascending=False)
                elif "Most Popular" in sort_by:
                    filtered_condo = filtered_condo.sort_values("rental_contracts", ascending=False)
                else:
                    filtered_condo = filtered_condo.sort_values(rent_col)

                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Condo Projects", len(filtered_condo))
                with col2:
                    if not filtered_condo.empty:
                        st.metric(f"Avg {condo_bedrooms}BR", f"${int(filtered_condo[rent_col].mean()):,}")
                    else:
                        st.metric(f"Avg {condo_bedrooms}BR", "N/A")
                with col3:
                    if not filtered_condo.empty:
                        st.metric("Range", f"${int(filtered_condo[rent_col].min()):,} - ${int(filtered_condo[rent_col].max()):,}")
                    else:
                        st.metric("Range", "N/A")

                # Map markers for condos
                geocode_limit = min(len(filtered_condo), 30)
                for _, row in filtered_condo.head(geocode_limit).iterrows():
                    coords = geocode_cached(row["project_name"])
                    if coords:
                        lat, lng = coords
                        est_rent = int(row[rent_col])
                        url_c = build_99co_url(project_name=row["project_name"], bedrooms=condo_bedrooms)
                        popup_html = f"""
                        <div style="min-width:220px;">
                            <b>🏢 {row['project_name']}</b><br>
                            📍 District {row['postal_district']} - {row['district_area']}<br>
                            💰 Est. {condo_bedrooms}BR: <b>${est_rent:,}/mo</b><br>
                            📊 Median ${row['median_psf']:.2f} psf<br>
                            📝 {int(row['rental_contracts'])} contracts<br>
                            <a href="{url_c}" target="_blank">99.co →</a>
                        </div>
                        """
                        price_ratio = (est_rent - condo_price[0]) / max(condo_price[1] - condo_price[0], 1)
                        color = "green" if price_ratio < 0.33 else ("blue" if price_ratio < 0.66 else "orange")
                        folium.Marker(
                            [lat, lng],
                            popup=folium.Popup(popup_html, max_width=300),
                            tooltip=f"🏢 ${est_rent:,} - {row['project_name']}",
                            icon=folium.Icon(color=color, icon="building", prefix="fa"),
                        ).add_to(m)

                # Listing cards
                st.subheader(f"Condo Projects ({len(filtered_condo)})")
                if filtered_condo.empty:
                    st.warning("No condos match. Try adjusting filters.")
                else:
                    typical_size = TYPICAL_SIZES.get(condo_bedrooms, 530)
                    for _, row in filtered_condo.iterrows():
                        est_rent = int(row[rent_col])
                        url_99p = build_99co_url(project_name=row["project_name"], bedrooms=condo_bedrooms,
                                                 price_min=int(est_rent * 0.85), price_max=int(est_rent * 1.15))
                        url_pgp = build_propertyguru_url(project_name=row["project_name"], bedrooms=condo_bedrooms,
                                                         price_min=int(est_rent * 0.85), price_max=int(est_rent * 1.15))
                        with st.container():
                            c1, c2, c3 = st.columns([3, 2, 2])
                            with c1:
                                st.markdown(f"**{row['project_name']}**")
                                st.caption(f"📍 D{row['postal_district']} {row['district_area']} | 📝 {int(row['rental_contracts'])} contracts")
                            with c2:
                                st.markdown(f"### ${est_rent:,}/mo")
                                st.caption(f"Est. {condo_bedrooms}BR ({typical_size}sqft) | Median ${row['median_psf']:.2f} psf | P25-P75: ${row['p25_psf']:.2f}-${row['p75_psf']:.2f}")
                            with c3:
                                st.markdown(f"[99.co]({url_99p}) | [PropertyGuru]({url_pgp})")
                            st.divider()

                # Table
                with st.expander("📊 Condo Data Table"):
                    if not filtered_condo.empty:
                        disp = filtered_condo[["project_name", "postal_district", "district_area",
                                                "median_psf", "p25_psf", "p75_psf", "rental_contracts", rent_col]].copy()
                        disp.columns = ["Project", "District", "Area", "Median PSF", "P25", "P75", "Contracts", f"Est {condo_bedrooms}BR"]
                        st.dataframe(disp, use_container_width=True, hide_index=True)

    # ======================== HDB ========================
    if show_hdb:
        with tab_hdb:
            with st.spinner("Loading HDB data..."):
                try:
                    hdb_raw = load_hdb_data()
                except Exception as e:
                    st.error(f"Failed to load HDB data: {e}")
                    hdb_raw = pd.DataFrame()

            if not hdb_raw.empty:
                # Filter by town (MRT-based)
                target_towns = get_towns_for_mrt(target_station) if target_station else []
                if target_towns:
                    hdb_filtered = hdb_raw[hdb_raw["town"].isin(target_towns)].copy()
                else:
                    hdb_filtered = hdb_raw.copy()

                # Filter by flat type
                if hdb_flat_types:
                    hdb_filtered = hdb_filtered[hdb_filtered["flat_type"].isin(hdb_flat_types)].copy()

                # Filter by price
                hdb_filtered = hdb_filtered[
                    (hdb_filtered["monthly_rent"] >= hdb_price[0]) &
                    (hdb_filtered["monthly_rent"] <= hdb_price[1])
                ].copy()

                # Aggregate by town + flat_type
                hdb_town_agg = aggregate_hdb_by_town(hdb_filtered)

                # Sort
                if "High to Low" in sort_by:
                    hdb_town_agg = hdb_town_agg.sort_values("median_rent", ascending=False)
                elif "Most Popular" in sort_by:
                    hdb_town_agg = hdb_town_agg.sort_values("transaction_count", ascending=False)
                else:
                    hdb_town_agg = hdb_town_agg.sort_values("median_rent")

                # Aggregate by street for detail view
                hdb_street_agg = aggregate_hdb_data(hdb_filtered)
                if "High to Low" in sort_by:
                    hdb_street_agg = hdb_street_agg.sort_values("median_rent", ascending=False)
                elif "Most Popular" in sort_by:
                    hdb_street_agg = hdb_street_agg.sort_values("transaction_count", ascending=False)
                else:
                    hdb_street_agg = hdb_street_agg.sort_values("median_rent")

                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("HDB Transactions", len(hdb_filtered))
                with col2:
                    if not hdb_filtered.empty:
                        st.metric("Median Rent", f"${int(hdb_filtered['monthly_rent'].median()):,}")
                    else:
                        st.metric("Median Rent", "N/A")
                with col3:
                    if not hdb_filtered.empty:
                        st.metric("Range", f"${hdb_filtered['monthly_rent'].min():,} - ${hdb_filtered['monthly_rent'].max():,}")
                    else:
                        st.metric("Range", "N/A")

                # Map markers for HDB streets
                geocode_hdb_limit = min(len(hdb_street_agg), 30)
                for _, row in hdb_street_agg.head(geocode_hdb_limit).iterrows():
                    addr = f"{row['latest_block']} {row['street_name']} Singapore"
                    coords = geocode_cached(addr)
                    if coords:
                        lat, lng = coords
                        popup_html = f"""
                        <div style="min-width:200px;">
                            <b>🏘️ {row['street_name']}</b><br>
                            📍 {row['town']} | {FLAT_TYPE_MAP.get(row['flat_type'], row['flat_type'])}<br>
                            💰 Median: <b>${int(row['median_rent']):,}/mo</b><br>
                            📊 Range: ${int(row['min_rent']):,} - ${int(row['max_rent']):,}<br>
                            📝 {row['transaction_count']} transactions
                        </div>
                        """
                        price_ratio = (row['median_rent'] - hdb_price[0]) / max(hdb_price[1] - hdb_price[0], 1)
                        color = "green" if price_ratio < 0.33 else ("cadetblue" if price_ratio < 0.66 else "purple")
                        folium.Marker(
                            [lat, lng],
                            popup=folium.Popup(popup_html, max_width=300),
                            tooltip=f"🏘️ ${int(row['median_rent']):,} - {row['street_name']}",
                            icon=folium.Icon(color=color, icon="home", prefix="fa"),
                        ).add_to(m)

                # HDB Town overview cards
                st.subheader(f"HDB Rental Overview ({len(hdb_town_agg)} town-type combos)")
                if hdb_town_agg.empty:
                    st.warning("No HDB listings match. Try adjusting filters.")
                else:
                    for _, row in hdb_town_agg.iterrows():
                        flat_label = FLAT_TYPE_MAP.get(row["flat_type"], row["flat_type"])
                        with st.container():
                            c1, c2, c3 = st.columns([2, 3, 2])
                            with c1:
                                st.markdown(f"**{row['town']}** — {flat_label}")
                                st.caption(f"📝 {row['transaction_count']} transactions (last 6 months)")
                            with c2:
                                st.markdown(f"### ${int(row['median_rent']):,}/mo")
                                st.caption(f"P25: ${int(row['p25_rent']):,} | P75: ${int(row['p75_rent']):,} | Range: ${int(row['min_rent']):,}-${int(row['max_rent']):,}")
                            with c3:
                                url_hdb_99 = build_99co_url(location=row["town"].title())
                                st.markdown(f"[🔗 99.co]({url_hdb_99})")
                            st.divider()

                # Street detail table
                with st.expander("📊 HDB Street-Level Data"):
                    if not hdb_street_agg.empty:
                        disp = hdb_street_agg[["town", "flat_type", "street_name", "latest_block",
                                                "median_rent", "min_rent", "max_rent", "transaction_count"]].copy()
                        disp.columns = ["Town", "Type", "Street", "Block", "Median", "Min", "Max", "Txns"]
                        st.dataframe(disp, use_container_width=True, hide_index=True)

    # ======================== MAP (shared) ========================
    st.subheader("📍 Map")
    st_folium(m, width=None, height=500, use_container_width=True)

    # Tips
    with st.expander("💡 Tips"):
        st.markdown("""
        **Condo tips:**
        - Google "*condo name* + brochure" for floor plans
        - Check URA Rental Transactions for exact unit history
        - Aim for P25 price when negotiating

        **HDB tips:**
        - HDB rental data shows actual approved rents (not asking prices)
        - Compare similar flat types on the same street for fair pricing
        - Check if the flat is within the minimum occupation period (MOP)
        """)

else:
    # ======================== WELCOME ========================
    st.markdown("""
    ### How to use

    **1. Choose property type** — Condo, HDB, or Both (sidebar)

    **2. Search** — Natural language or sidebar filters:
    - `Queenstown 1b1b 3300` → 1BR condos ~$3,300/mo
    - `找Bishan附近HDB 3房 2500` → HDB 3-room near Bishan
    - `Paya Lebar 1 bedroom 3000-3500` → 1BR condos $3,000-$3,500

    ---

    **Data sources:**
    - **Condo:** URA official rental statistics (551 projects, Q4 2025)
    - **HDB:** HDB rental transactions (200K+ records, 2021-2026)
    - Click through to **99.co** / **PropertyGuru** for live listings
    """)

    st.subheader("Popular Searches")
    popular = [
        ("QT Condo 1BR", "Queenstown 1b1b 3300"),
        ("Bishan Condo 2BR", "Bishan 2 bedroom 4000"),
        ("Toa Payoh 1BR", "Toa Payoh 1b1b 2800"),
        ("Paya Lebar 1BR", "Paya Lebar 1 bedroom 3500"),
        ("Holland V 1BR", "Holland Village 1b1b 3500"),
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
