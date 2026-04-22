"""
SG Rental Search - Interactive Streamlit Dashboard

Data: URA condo stats + HDB rental transactions via data.gov.sg
Links to PropertyGuru for live listings

Usage: streamlit run app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import altair as alt
import folium
from streamlit_folium import st_folium
import pandas as pd

from config import DEFAULT_PRICE_MIN, DEFAULT_PRICE_MAX, DEFAULT_BEDROOMS, DEFAULT_RADIUS_M, SG_CENTER
from geo import find_station, get_station_names, geocode_address
from engine import parse_query, criteria_to_display, Criteria
from scraper.data_gov import (
    fetch_rental_data, fetch_trend_data, get_districts_for_mrt,
    DISTRICT_AREAS, TYPICAL_SIZES,
    build_propertyguru_url, build_google_search_url, build_99co_url,
)
from scraper.hdb import (
    fetch_hdb_rental_data, aggregate_hdb_by_town, aggregate_hdb_data,
    get_towns_for_mrt, FLAT_TYPE_MAP,
)
from smart_search import expand_query, detect_landmark
from i18n import t, get_lang, set_lang, bedroom_label
import features_showcase

# --- Page Config ---
st.set_page_config(
    page_title="SG Rental Search",
    page_icon="\U0001f3e0",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Language selector (top of sidebar, before anything else) ---
st.sidebar.markdown(f"**{t('sidebar.language')}**")
lang_options = {"English": "en", "\u4e2d\u6587": "zh"}
current = get_lang()
default_idx = list(lang_options.values()).index(current) if current in lang_options.values() else 0
chosen_label = st.sidebar.radio(
    "lang_toggle",
    list(lang_options.keys()),
    index=default_idx,
    horizontal=True,
    label_visibility="collapsed",
)
if lang_options[chosen_label] != current:
    set_lang(lang_options[chosen_label])
    st.rerun()

st.sidebar.markdown("---")

# --- Title ---
st.title(f"\U0001f3e0 {t('page.title')}")
st.caption(t("page.caption"))


# --- Cache ---
@st.cache_data(ttl=3600)
def load_condo_data():
    return fetch_rental_data()


@st.cache_data(ttl=3600)
def load_trend_data():
    return fetch_trend_data(recent_quarters=8)


@st.cache_data(ttl=3600)
def load_hdb_data():
    return fetch_hdb_rental_data(recent_months=6)


@st.cache_data(ttl=86400)
def geocode_cached(name: str):
    return geocode_address(name)


# --- Natural Language Input ---
if "_popular_query" in st.session_state:
    st.session_state["nl_query"] = st.session_state.pop("_popular_query")

nl_query = st.text_input(
    f"\U0001f50d {t('page.search_label')}",
    placeholder=t("page.search_placeholder"),
    key="nl_query",
)

nl_criteria: Criteria = {}
if nl_query:
    nl_criteria = parse_query(nl_query)
    if nl_criteria:
        st.info(f"\U0001f4cb {t('page.parsed')}: **{criteria_to_display(nl_criteria)}**")

# --- Sidebar Filters ---
st.sidebar.header(f"\U0001f527 {t('sidebar.filters')}")

# Property type toggle
pt_labels = [
    f"\U0001f3e2 {t('sidebar.condo')}",
    f"\U0001f3d8\ufe0f {t('sidebar.hdb')}",
    f"\U0001f3e2+\U0001f3d8\ufe0f {t('sidebar.both')}",
]
property_type = st.sidebar.radio(t("sidebar.property_type"), pt_labels, index=0, horizontal=True)
show_condo = property_type in [pt_labels[0], pt_labels[2]]
show_hdb = property_type in [pt_labels[1], pt_labels[2]]

# MRT Station
station_names = [t("sidebar.any")] + get_station_names()
default_station_idx = 0
if nl_criteria.get("mrt_station"):
    try:
        default_station_idx = station_names.index(nl_criteria["mrt_station"])
    except ValueError:
        pass

selected_station = st.sidebar.selectbox(t("sidebar.mrt_station"), station_names, index=default_station_idx)

# --- Condo-specific filters ---
if show_condo:
    st.sidebar.markdown(f"**{t('sidebar.condo_filters')}**")
    condo_bedrooms = st.sidebar.selectbox(
        t("sidebar.condo_bedrooms"),
        [1, 2, 3, 4, 0],
        index=[1, 2, 3, 4, 0].index(nl_criteria.get("bedrooms", DEFAULT_BEDROOMS)),
        format_func=bedroom_label,
    )
    condo_price = st.sidebar.slider(
        t("sidebar.condo_rent"),
        min_value=1000, max_value=15000,
        value=(nl_criteria.get("price_min", DEFAULT_PRICE_MIN),
               nl_criteria.get("price_max", DEFAULT_PRICE_MAX)),
        step=100, format="$%d",
    )

# --- HDB-specific filters ---
if show_hdb:
    st.sidebar.markdown(f"**{t('sidebar.hdb_filters')}**")
    hdb_flat_types = st.sidebar.multiselect(
        t("sidebar.flat_type"),
        ["2-ROOM", "3-ROOM", "4-ROOM", "5-ROOM", "EXECUTIVE"],
        default=["3-ROOM"],
        format_func=lambda x: FLAT_TYPE_MAP.get(x, x),
    )
    hdb_price = st.sidebar.slider(
        t("sidebar.hdb_rent"),
        min_value=500, max_value=8000,
        value=(nl_criteria.get("price_min", 1500),
               min(nl_criteria.get("price_max", 4000), 8000)),
        step=100, format="$%d",
    )

# Sort
sort_options = [t("sidebar.sort_low"), t("sidebar.sort_high"), t("sidebar.sort_popular")]
sort_by = st.sidebar.selectbox(t("sidebar.sort"), sort_options)

# Search
search_clicked = st.sidebar.button(f"\U0001f50d {t('sidebar.search_btn')}", type="primary", use_container_width=True)

# Links
location_query = nl_criteria.get("mrt_station") or (selected_station if selected_station != t("sidebar.any") else "")
st.sidebar.markdown("---")
st.sidebar.markdown(f"**{t('sidebar.browse')}**")
url_pg = build_propertyguru_url(location=location_query)
url_google = build_google_search_url(location=location_query)
st.sidebar.markdown(f"[\U0001f517 PropertyGuru]({url_pg})")
st.sidebar.markdown(f"[\U0001f50d Google Search]({url_google})")


# =========================================================================
# HELPER: Render rent trend chart for a condo project
# =========================================================================
def render_trend_chart(project_name: str, bedrooms: int):
    """
    Show rent trend / distribution inside an expander.

    Behavior:
      - 2+ quarters available: line chart with historical trend
      - 1 quarter only:        horizontal P25/median/P75 bar + info note
      - Project not found:     skip silently
    """
    try:
        trend_df = load_trend_data()
    except Exception:
        return
    if trend_df is None or trend_df.empty:
        return

    proj_df = trend_df[trend_df["project_name"] == project_name].copy()
    if proj_df.empty:
        return

    rent_col = f"est_rent_{bedrooms}br"
    if rent_col not in proj_df.columns:
        return

    proj_df = proj_df.sort_values("qtr")
    typical_size = TYPICAL_SIZES.get(bedrooms, 530)

    with st.expander(f"\U0001f4c8 {t('trend.expand')}"):
        # ---------- Key metrics ----------
        current_rent = int(proj_df[rent_col].iloc[-1])
        hist_low = int(proj_df[rent_col].min())
        hist_high = int(proj_df[rent_col].max())

        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.metric(t("trend.current"), f"${current_rent:,}")
        with mc2:
            st.metric(t("trend.low"), f"${hist_low:,}")
        with mc3:
            st.metric(t("trend.high"), f"${hist_high:,}")

        # ---------- Quarter-over-quarter change ----------
        if len(proj_df) >= 2:
            prev_rent = int(proj_df[rent_col].iloc[-2])
            delta = current_rent - prev_rent
            pct = (delta / prev_rent * 100) if prev_rent else 0
            delta_str = f"+${delta:,}" if delta >= 0 else f"-${abs(delta):,}"
            st.caption(f"{t('trend.change')}: {delta_str} ({pct:+.1f}%)")

        # ---------- P75 bargain room ----------
        if "p75_psf" in proj_df.columns:
            p75_rent = int(proj_df["p75_psf"].iloc[-1] * typical_size)
            if p75_rent > current_rent:
                st.markdown(t("trend.bargain_room", delta=p75_rent - current_rent))

        # ---------- Chart: branch on data availability ----------
        if len(proj_df) >= 2:
            # Historical trend line
            chart_data = proj_df[["qtr", rent_col]].copy()
            chart_data.columns = ["qtr", "rent"]
            base = alt.Chart(chart_data).encode(
                x=alt.X("qtr:N", sort=None, title=t("trend.quarter")),
                y=alt.Y("rent:Q", title=t("trend.est_rent"), scale=alt.Scale(zero=False)),
                tooltip=[
                    alt.Tooltip("qtr:N", title=t("trend.quarter")),
                    alt.Tooltip("rent:Q", title=t("trend.est_rent"), format="$,.0f"),
                ],
            )
            line = base.mark_line(color="#1f77b4", strokeWidth=2)
            points = base.mark_circle(color="#1f77b4", size=60)
            chart = (line + points).properties(
                title=t("trend.title", name=project_name),
                height=260,
            ).configure_axis(grid=True)
            st.altair_chart(chart, use_container_width=True)

            # P25-P75 band chart
            if "p25_psf" in proj_df.columns and "p75_psf" in proj_df.columns:
                band_data = proj_df[["qtr"]].copy()
                band_data["p25"] = (proj_df["p25_psf"] * typical_size).round(0).astype(int)
                band_data["p75"] = (proj_df["p75_psf"] * typical_size).round(0).astype(int)
                band_data["rent"] = proj_df[rent_col].values
                band = alt.Chart(band_data).mark_area(opacity=0.15, color="#1f77b4").encode(
                    x=alt.X("qtr:N", sort=None, title=t("trend.quarter")),
                    y=alt.Y("p25:Q", title=t("trend.est_rent")),
                    y2=alt.Y2("p75:Q"),
                )
                mid_line = alt.Chart(band_data).mark_line(
                    color="#1f77b4", strokeWidth=2
                ).encode(x=alt.X("qtr:N", sort=None), y=alt.Y("rent:Q"))
                combined = (band + mid_line).properties(
                    title=t("trend.p25_p75"),
                    height=200,
                )
                st.altair_chart(combined, use_container_width=True)
        else:
            # Single-quarter fallback: show price distribution bar
            latest_qtr = str(proj_df["qtr"].iloc[-1])
            row = proj_df.iloc[-1]
            contracts = int(row.get("rental_contracts", 0) or 0)

            if "p25_psf" in proj_df.columns and "p75_psf" in proj_df.columns:
                p25_rent = int(row["p25_psf"] * typical_size)
                median_rent = current_rent
                p75_rent = int(row["p75_psf"] * typical_size)

                # Horizontal bar chart for P25/Median/P75.
                # Keep label order consistent by using the raw label as the sort value.
                labels = [t("trend.p25"), t("trend.median"), t("trend.p75")]
                dist_data = pd.DataFrame({
                    "label": labels,
                    "value": [p25_rent, median_rent, p75_rent],
                })

                st.markdown(f"**{t('trend.price_dist', qtr=latest_qtr)}**")
                bar = alt.Chart(dist_data).mark_bar(color="#1f77b4").encode(
                    x=alt.X("value:Q", title=t("trend.est_rent")),
                    y=alt.Y("label:N", title="", sort=labels),
                    tooltip=[
                        alt.Tooltip("label:N", title=""),
                        alt.Tooltip("value:Q", title=t("trend.est_rent"), format="$,.0f"),
                    ],
                ).properties(height=160)
                st.altair_chart(bar, use_container_width=True)

            if contracts:
                st.caption(t("trend.contracts_qtr", n=contracts))
            st.info(t("trend.single_qtr_info", qtr=latest_qtr))


# =========================================================================
# MAIN CONTENT
# =========================================================================
if search_clicked or nl_query:
    # --- Smart Expand: auto-detect landmarks ---
    smart_result = expand_query(nl_query or "") if nl_query else None

    if smart_result and len(smart_result.strategies) > 1:
        # ============ SMART EXPAND RESULTS ============
        sr = smart_result
        st.success(f"\U0001f9e0 {t('smart.detected', landmark=sr.landmark_name.upper(), n=len(sr.strategies))}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(t("smart.strategies"), len(sr.strategies))
        with col2:
            st.metric(t("smart.total_condos"), len(sr.results))
        with col3:
            if sr.results:
                rents = [r.est_rent for r in sr.results]
                st.metric(t("smart.rent_range"), f"${min(rents):,} - ${max(rents):,}")

        # Map
        st.subheader(f"\U0001f4cd {t('smart.map')}")
        clat, clng = sr.landmark_coords if sr.landmark_coords else SG_CENTER
        m = folium.Map(location=[clat, clng], zoom_start=14, tiles="CartoDB positron")

        if sr.landmark_coords:
            folium.Marker(
                [sr.landmark_coords[0], sr.landmark_coords[1]],
                popup=f"\U0001f4cd {sr.landmark_name.upper()}: {sr.landmark_address}",
                tooltip=f"\U0001f4cd {sr.landmark_name.upper()}",
                icon=folium.Icon(color="red", icon="star", prefix="fa"),
            ).add_to(m)
            folium.Circle(
                [sr.landmark_coords[0], sr.landmark_coords[1]],
                radius=1500, color="red", fill=True, fill_opacity=0.05, weight=1,
            ).add_to(m)

        for i, strat in enumerate(sr.strategies):
            s_info = find_station(strat.station)
            if s_info:
                color = "green" if i < 3 else ("blue" if i < 6 else "lightgray")
                popup_html = f"""
                <div style="min-width:200px;">
                    <b>#{i+1} {strat.station}</b> ({strat.distance_m}m)<br>
                    {strat.reason}<br>
                    Query: {strat.query_text}
                </div>
                """
                folium.Marker(
                    [s_info["lat"], s_info["lng"]],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"#{i+1} {strat.station} ({strat.distance_m}m)",
                    icon=folium.Icon(color=color, icon="home", prefix="fa"),
                ).add_to(m)

        st_folium(m, width=None, height=500, use_container_width=True)

        # Results grouped by strategy
        bedrooms_smart = nl_criteria.get("bedrooms", 1)
        st.subheader(f"\U0001f4cb {t('smart.results_by_area', n=len(sr.results))}")

        for i, strat in enumerate(sr.strategies):
            strat_results = [r for r in sr.results if r.strategy_name == strat.name]
            if not strat_results:
                continue
            rank = "\U0001f947" if i == 0 else ("\U0001f948" if i == 1 else ("\U0001f949" if i == 2 else f"#{i+1}"))
            with st.expander(
                f"{rank} **{strat.station}** ({strat.distance_m}m) — {len(strat_results)} {t('smart.condos')} | {strat.reason}",
                expanded=(i < 3),
            ):
                # Show first 5 immediately
                for r in strat_results[:5]:
                    url_g = build_google_search_url(project_name=r.project_name)
                    st.markdown(
                        f"**{r.project_name}** — ${r.est_rent:,}/mo "
                        f"(${r.median_psf:.2f} psf, {r.contracts} contracts) "
                        f"[PropertyGuru]({r.url_propertyguru}) | [Google]({url_g})"
                    )
                    render_trend_chart(r.project_name, bedrooms_smart)
                # Remaining items in a nested expander so they are actually accessible
                if len(strat_results) > 5:
                    with st.expander(t("smart.show_more", n=len(strat_results) - 5)):
                        for r in strat_results[5:]:
                            url_g = build_google_search_url(project_name=r.project_name)
                            st.markdown(
                                f"**{r.project_name}** — ${r.est_rent:,}/mo "
                                f"(${r.median_psf:.2f} psf, {r.contracts} contracts) "
                                f"[PropertyGuru]({r.url_propertyguru}) | [Google]({url_g})"
                            )
                            render_trend_chart(r.project_name, bedrooms_smart)

        with st.expander(f"\U0001f4ca {t('smart.full_table')}"):
            if sr.results:
                rows = [{
                    t("smart.col_project"): r.project_name,
                    t("smart.col_area"): r.strategy_name,
                    t("smart.col_est_rent", n=bedrooms_smart): r.est_rent,
                    t("smart.col_median_psf"): r.median_psf,
                    t("smart.col_contracts"): r.contracts,
                } for r in sr.results]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        with st.expander(f"\U0001f9e0 {t('smart.analysis')}"):
            st.markdown(sr.summary)

    else:
        # ============ REGULAR SEARCH ============
        target_station = nl_criteria.get("mrt_station") or (selected_station if selected_station != t("sidebar.any") else None)
        station_info = find_station(target_station) if target_station else None

        center_lat, center_lng = SG_CENTER
        zoom = 12
        if station_info:
            center_lat, center_lng = station_info["lat"], station_info["lng"]
            zoom = 14

        m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom, tiles="CartoDB positron")

        if station_info:
            folium.Marker(
                [station_info["lat"], station_info["lng"]],
                popup=f"\U0001f687 {station_info['name']} MRT ({station_info['code']})",
                tooltip=f"\U0001f687 {station_info['name']} MRT",
                icon=folium.Icon(color="red", icon="train", prefix="fa"),
            ).add_to(m)
            folium.Circle(
                [station_info["lat"], station_info["lng"]],
                radius=DEFAULT_RADIUS_M, color="red", fill=True, fill_opacity=0.05, weight=1,
            ).add_to(m)

        # Tabs
        if show_condo and show_hdb:
            tab_condo, tab_hdb = st.tabs([f"\U0001f3e2 {t('sidebar.condo')}", f"\U0001f3d8\ufe0f {t('sidebar.hdb')}"])
        elif show_condo:
            tab_condo = st.container()
            tab_hdb = None
        else:
            tab_condo = None
            tab_hdb = st.container()

        # ======================== CONDO ========================
        if show_condo:
            with tab_condo:
                with st.spinner(t("loading.condo")):
                    try:
                        condo_df = load_condo_data()
                    except Exception as e:
                        st.error(f"{t('loading.failed_condo')}: {e}")
                        condo_df = pd.DataFrame()

                if not condo_df.empty:
                    target_districts = get_districts_for_mrt(target_station) if target_station else []
                    if target_districts:
                        filtered_condo = condo_df[condo_df["postal_district"].isin(target_districts)].copy()
                    else:
                        filtered_condo = condo_df.copy()

                    rent_col = f"est_rent_{condo_bedrooms}br"
                    if rent_col in filtered_condo.columns:
                        filtered_condo = filtered_condo[
                            (filtered_condo[rent_col] >= condo_price[0]) &
                            (filtered_condo[rent_col] <= condo_price[1])
                        ].copy()

                    # Sort
                    if sort_by == sort_options[1]:  # High to Low
                        filtered_condo = filtered_condo.sort_values(rent_col, ascending=False)
                    elif sort_by == sort_options[2]:  # Most Popular
                        filtered_condo = filtered_condo.sort_values("rental_contracts", ascending=False)
                    else:
                        filtered_condo = filtered_condo.sort_values(rent_col)

                    # Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(t("result.condo_projects"), len(filtered_condo))
                    with col2:
                        if not filtered_condo.empty:
                            st.metric(t("result.avg_br", n=condo_bedrooms), f"${int(filtered_condo[rent_col].mean()):,}")
                        else:
                            st.metric(t("result.avg_br", n=condo_bedrooms), "N/A")
                    with col3:
                        if not filtered_condo.empty:
                            st.metric(t("result.range"), f"${int(filtered_condo[rent_col].min()):,} - ${int(filtered_condo[rent_col].max()):,}")
                        else:
                            st.metric(t("result.range"), "N/A")

                    # Map markers
                    geocode_limit = min(len(filtered_condo), 30)
                    for _, row in filtered_condo.head(geocode_limit).iterrows():
                        coords = geocode_cached(row["project_name"])
                        if coords:
                            lat, lng = coords
                            est_rent = int(row[rent_col])
                            url_c = build_99co_url(project_name=row["project_name"], bedrooms=condo_bedrooms)
                            popup_html = f"""
                            <div style="min-width:220px;">
                                <b>\U0001f3e2 {row['project_name']}</b><br>
                                \U0001f4cd District {row['postal_district']} - {row['district_area']}<br>
                                \U0001f4b0 Est. {condo_bedrooms}BR: <b>${est_rent:,}/mo</b><br>
                                \U0001f4ca Median ${row['median_psf']:.2f} psf<br>
                                \U0001f4dd {int(row['rental_contracts'])} contracts<br>
                                <a href="{url_c}" target="_blank">99.co \u2192</a>
                            </div>
                            """
                            price_ratio = (est_rent - condo_price[0]) / max(condo_price[1] - condo_price[0], 1)
                            color = "green" if price_ratio < 0.33 else ("blue" if price_ratio < 0.66 else "orange")
                            folium.Marker(
                                [lat, lng],
                                popup=folium.Popup(popup_html, max_width=300),
                                tooltip=f"\U0001f3e2 ${est_rent:,} - {row['project_name']}",
                                icon=folium.Icon(color=color, icon="building", prefix="fa"),
                            ).add_to(m)

                    # Listing cards
                    st.subheader(t("result.condo_heading", n=len(filtered_condo)))
                    if filtered_condo.empty:
                        st.warning(t("result.no_condo"))
                    else:
                        typical_size = TYPICAL_SIZES.get(condo_bedrooms, 530)
                        for _, row in filtered_condo.iterrows():
                            est_rent = int(row[rent_col])
                            url_pgp = build_propertyguru_url(
                                project_name=row["project_name"], bedrooms=condo_bedrooms,
                                price_min=int(est_rent * 0.85), price_max=int(est_rent * 1.15),
                            )
                            url_gp = build_google_search_url(project_name=row["project_name"], bedrooms=condo_bedrooms)
                            with st.container():
                                c1, c2, c3 = st.columns([3, 2, 2])
                                with c1:
                                    st.markdown(f"**{row['project_name']}**")
                                    st.caption(f"\U0001f4cd D{row['postal_district']} {row['district_area']} | \U0001f4dd {t('result.contracts', n=int(row['rental_contracts']))}")
                                with c2:
                                    st.markdown(f"### ${est_rent:,}/mo")
                                    st.caption(f"Est. {condo_bedrooms}BR ({typical_size}sqft) | Median ${row['median_psf']:.2f} psf | P25-P75: ${row['p25_psf']:.2f}-${row['p75_psf']:.2f}")
                                with c3:
                                    st.markdown(f"[PropertyGuru]({url_pgp}) | [Google]({url_gp})")
                                # Trend chart for this project
                                render_trend_chart(row["project_name"], condo_bedrooms)
                                st.divider()

                    # Full table
                    with st.expander(f"\U0001f4ca {t('result.condo_table')}"):
                        if not filtered_condo.empty:
                            disp = filtered_condo[["project_name", "postal_district", "district_area",
                                                    "median_psf", "p25_psf", "p75_psf", "rental_contracts", rent_col]].copy()
                            disp.columns = [t("smart.col_project"), "District", t("smart.col_area"),
                                            t("smart.col_median_psf"), "P25", "P75",
                                            t("smart.col_contracts"), t("smart.col_est_rent", n=condo_bedrooms)]
                            st.dataframe(disp, use_container_width=True, hide_index=True)

        # ======================== HDB ========================
        if show_hdb:
            with tab_hdb:
                with st.spinner(t("loading.hdb")):
                    try:
                        hdb_raw = load_hdb_data()
                    except Exception as e:
                        st.error(f"{t('loading.failed_hdb')}: {e}")
                        hdb_raw = pd.DataFrame()

                if not hdb_raw.empty:
                    target_towns = get_towns_for_mrt(target_station) if target_station else []
                    if target_towns:
                        hdb_filtered = hdb_raw[hdb_raw["town"].isin(target_towns)].copy()
                    else:
                        hdb_filtered = hdb_raw.copy()

                    if hdb_flat_types:
                        hdb_filtered = hdb_filtered[hdb_filtered["flat_type"].isin(hdb_flat_types)].copy()

                    hdb_filtered = hdb_filtered[
                        (hdb_filtered["monthly_rent"] >= hdb_price[0]) &
                        (hdb_filtered["monthly_rent"] <= hdb_price[1])
                    ].copy()

                    hdb_town_agg = aggregate_hdb_by_town(hdb_filtered)
                    hdb_street_agg = aggregate_hdb_data(hdb_filtered)

                    # Sort
                    if sort_by == sort_options[1]:
                        hdb_town_agg = hdb_town_agg.sort_values("median_rent", ascending=False)
                        hdb_street_agg = hdb_street_agg.sort_values("median_rent", ascending=False)
                    elif sort_by == sort_options[2]:
                        hdb_town_agg = hdb_town_agg.sort_values("transaction_count", ascending=False)
                        hdb_street_agg = hdb_street_agg.sort_values("transaction_count", ascending=False)
                    else:
                        hdb_town_agg = hdb_town_agg.sort_values("median_rent")
                        hdb_street_agg = hdb_street_agg.sort_values("median_rent")

                    # Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(t("hdb.transactions"), len(hdb_filtered))
                    with col2:
                        if not hdb_filtered.empty:
                            st.metric(t("hdb.median_rent"), f"${int(hdb_filtered['monthly_rent'].median()):,}")
                        else:
                            st.metric(t("hdb.median_rent"), "N/A")
                    with col3:
                        if not hdb_filtered.empty:
                            st.metric(t("result.range"), f"${hdb_filtered['monthly_rent'].min():,} - ${hdb_filtered['monthly_rent'].max():,}")
                        else:
                            st.metric(t("result.range"), "N/A")

                    # Map markers for HDB streets
                    geocode_hdb_limit = min(len(hdb_street_agg), 30)
                    for _, row in hdb_street_agg.head(geocode_hdb_limit).iterrows():
                        addr = f"{row['latest_block']} {row['street_name']} Singapore"
                        coords = geocode_cached(addr)
                        if coords:
                            lat, lng = coords
                            popup_html = f"""
                            <div style="min-width:200px;">
                                <b>\U0001f3d8\ufe0f {row['street_name']}</b><br>
                                \U0001f4cd {row['town']} | {FLAT_TYPE_MAP.get(row['flat_type'], row['flat_type'])}<br>
                                \U0001f4b0 Median: <b>${int(row['median_rent']):,}/mo</b><br>
                                \U0001f4ca Range: ${int(row['min_rent']):,} - ${int(row['max_rent']):,}<br>
                                \U0001f4dd {row['transaction_count']} transactions
                            </div>
                            """
                            price_ratio = (row['median_rent'] - hdb_price[0]) / max(hdb_price[1] - hdb_price[0], 1)
                            color = "green" if price_ratio < 0.33 else ("cadetblue" if price_ratio < 0.66 else "purple")
                            folium.Marker(
                                [lat, lng],
                                popup=folium.Popup(popup_html, max_width=300),
                                tooltip=f"\U0001f3d8\ufe0f ${int(row['median_rent']):,} - {row['street_name']}",
                                icon=folium.Icon(color=color, icon="home", prefix="fa"),
                            ).add_to(m)

                    # HDB cards
                    st.subheader(t("hdb.overview", n=len(hdb_town_agg)))
                    if hdb_town_agg.empty:
                        st.warning(t("hdb.no_match"))
                    else:
                        for _, row in hdb_town_agg.iterrows():
                            flat_label = FLAT_TYPE_MAP.get(row["flat_type"], row["flat_type"])
                            with st.container():
                                c1, c2, c3 = st.columns([2, 3, 2])
                                with c1:
                                    st.markdown(f"**{row['town']}** \u2014 {flat_label}")
                                    st.caption(f"\U0001f4dd {t('hdb.txn_count', n=row['transaction_count'])}")
                                with c2:
                                    st.markdown(f"### ${int(row['median_rent']):,}/mo")
                                    st.caption(f"P25: ${int(row['p25_rent']):,} | P75: ${int(row['p75_rent']):,} | Range: ${int(row['min_rent']):,}-${int(row['max_rent']):,}")
                                with c3:
                                    url_hdb_pg = build_propertyguru_url(location=row["town"].title())
                                    url_hdb_g = build_google_search_url(location=row["town"].title())
                                    st.markdown(f"[PropertyGuru]({url_hdb_pg}) | [Google]({url_hdb_g})")
                                st.divider()

                    with st.expander(f"\U0001f4ca {t('hdb.street_table')}"):
                        if not hdb_street_agg.empty:
                            disp = hdb_street_agg[["town", "flat_type", "street_name", "latest_block",
                                                    "median_rent", "min_rent", "max_rent", "transaction_count"]].copy()
                            disp.columns = ["Town", "Type", "Street", "Block", "Median", "Min", "Max", "Txns"]
                            st.dataframe(disp, use_container_width=True, hide_index=True)

        # ======================== MAP (shared) ========================
        st.subheader(f"\U0001f4cd {t('map.title')}")
        st_folium(m, width=None, height=500, use_container_width=True)

        # Tips
        with st.expander(f"\U0001f4a1 {t('tips.title')}"):
            st.markdown(t("tips.condo"))
            st.markdown(t("tips.hdb"))

else:
    # ======================== WELCOME ========================
    features_showcase.render(expanded=True)

    st.markdown(t("welcome.how_to"))

    st.subheader(t("welcome.popular"))
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
                st.session_state["_popular_query"] = query
                st.rerun()
