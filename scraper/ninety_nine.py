"""Scraper for 99.co Singapore condo rental listings."""

import re
import time
import json
from urllib.parse import urlencode, quote

import requests
from bs4 import BeautifulSoup

from config import HEADERS, NINETY_NINE_BASE, REQUEST_DELAY


def build_search_url(query: str, bedrooms: int | None = None,
                     price_min: int | None = None, price_max: int | None = None,
                     page: int = 1) -> str:
    """Build 99.co search URL from criteria."""
    # 99.co URL pattern: /singapore/rent/condos-apartments?query=...
    params = {}
    if query:
        params["query"] = query
    if bedrooms is not None:
        params["bedroom_num"] = str(bedrooms)
    if price_min is not None and price_max is not None:
        params["rental_range"] = f"{price_min}-{price_max}"
    elif price_min is not None:
        params["rental_range"] = f"{price_min}-any"
    elif price_max is not None:
        params["rental_range"] = f"any-{price_max}"
    if page > 1:
        params["page_num"] = str(page)

    return f"{NINETY_NINE_BASE}?{urlencode(params)}"


def _extract_json_data(html: str) -> list[dict] | None:
    """Try to extract listing data from embedded JSON in the page."""
    # 99.co often embeds listing data in __NEXT_DATA__ or similar script tags
    soup = BeautifulSoup(html, "lxml")

    # Try __NEXT_DATA__ (Next.js pattern)
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if script and script.string:
        try:
            data = json.loads(script.string)
            # Navigate the Next.js data structure to find listings
            props = data.get("props", {}).get("pageProps", {})
            # Try common paths
            for key in ["listings", "results", "searchResults", "initialListings"]:
                if key in props:
                    return props[key]
            # Try nested cluster results
            cluster = props.get("clusterResults", {})
            if isinstance(cluster, dict):
                for key in ["listings", "results"]:
                    if key in cluster:
                        return cluster[key]
        except (json.JSONDecodeError, AttributeError):
            pass

    # Try any script tag with listing-like JSON
    for script in soup.find_all("script"):
        if script.string and '"listings"' in (script.string or ""):
            try:
                # Find JSON object in script
                match = re.search(r'\{.*"listings"\s*:\s*\[.*?\].*?\}', script.string, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    return data.get("listings", [])
            except (json.JSONDecodeError, AttributeError):
                continue

    return None


def _parse_listing_from_json(item: dict) -> dict | None:
    """Parse a single listing from JSON data."""
    try:
        # 99.co JSON structure varies; handle common patterns
        listing = {
            "name": item.get("name") or item.get("project_name") or item.get("title", ""),
            "price": None,
            "bedrooms": None,
            "area_sqft": None,
            "address": item.get("address") or item.get("address_name", ""),
            "lat": None,
            "lng": None,
            "facing": item.get("facing") or item.get("direction", ""),
            "floor": item.get("floor") or item.get("floor_level", ""),
            "listing_url": "",
            "image_url": "",
            "district": item.get("district", ""),
        }

        # Price
        price = item.get("price") or item.get("rental_price") or item.get("asking_price_rental")
        if price:
            listing["price"] = int(float(str(price).replace(",", "").replace("$", "")))

        # Bedrooms
        beds = item.get("bedrooms") or item.get("bedroom_num") or item.get("num_beds")
        if beds is not None:
            listing["bedrooms"] = int(beds)

        # Area
        area = item.get("area") or item.get("size_sqft") or item.get("floor_area")
        if area:
            listing["area_sqft"] = int(float(str(area).replace(",", "")))

        # Coordinates
        lat = item.get("latitude") or item.get("lat")
        lng = item.get("longitude") or item.get("lng") or item.get("lon")
        if lat and lng:
            listing["lat"] = float(lat)
            listing["lng"] = float(lng)

        # URL
        slug = item.get("url_path") or item.get("slug") or item.get("listing_url", "")
        if slug:
            if slug.startswith("http"):
                listing["listing_url"] = slug
            else:
                listing["listing_url"] = f"https://www.99.co{slug}" if slug.startswith("/") else f"https://www.99.co/{slug}"

        # Image
        photos = item.get("photos") or item.get("images") or item.get("photo_urls") or []
        if photos:
            if isinstance(photos[0], dict):
                listing["image_url"] = photos[0].get("url", "")
            else:
                listing["image_url"] = photos[0]
        elif item.get("photo_url"):
            listing["image_url"] = item["photo_url"]

        return listing
    except (ValueError, TypeError, IndexError):
        return None


def _parse_listings_from_html(html: str) -> list[dict]:
    """Fallback: parse listings from HTML if JSON extraction fails."""
    soup = BeautifulSoup(html, "lxml")
    listings = []

    # Look for listing cards - 99.co uses various class patterns
    cards = soup.find_all("div", {"data-testid": re.compile(r"listing|search-result", re.I)})
    if not cards:
        cards = soup.find_all("a", href=re.compile(r"/singapore/rent/"))
        # Filter to actual listing links
        cards = [c for c in cards if c.find_parent("div") and len(c.get_text(strip=True)) > 20]

    for card in cards:
        listing = {
            "name": "", "price": None, "bedrooms": None, "area_sqft": None,
            "address": "", "lat": None, "lng": None, "facing": "",
            "floor": "", "listing_url": "", "image_url": "", "district": "",
        }

        # Extract name
        title_el = card.find(["h2", "h3", "h4", "p"], string=True)
        if title_el:
            listing["name"] = title_el.get_text(strip=True)

        # Extract price
        price_text = card.get_text()
        price_match = re.search(r'\$\s*([\d,]+)', price_text)
        if price_match:
            listing["price"] = int(price_match.group(1).replace(",", ""))

        # Extract bedrooms
        bed_match = re.search(r'(\d+)\s*(?:bed|br|bdr|bedroom)', price_text, re.I)
        if bed_match:
            listing["bedrooms"] = int(bed_match.group(1))

        # Extract area
        area_match = re.search(r'([\d,]+)\s*(?:sqft|sq\s*ft)', price_text, re.I)
        if area_match:
            listing["area_sqft"] = int(area_match.group(1).replace(",", ""))

        # Extract URL
        link = card.find("a", href=True) if card.name != "a" else card
        if link and link.get("href"):
            href = link["href"]
            listing["listing_url"] = href if href.startswith("http") else f"https://www.99.co{href}"

        # Extract image
        img = card.find("img", src=True)
        if img:
            listing["image_url"] = img["src"]

        if listing["name"] or listing["price"]:
            listings.append(listing)

    return listings


def search_listings(query: str, bedrooms: int | None = None,
                    price_min: int | None = None, price_max: int | None = None,
                    max_pages: int = 3) -> list[dict]:
    """
    Search 99.co for condo rental listings.

    Returns list of listing dicts with keys:
    name, price, bedrooms, area_sqft, address, lat, lng,
    facing, floor, listing_url, image_url, district
    """
    all_listings = []

    for page in range(1, max_pages + 1):
        url = build_search_url(query, bedrooms, price_min, price_max, page)

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[99.co] Request failed for page {page}: {e}")
            break

        html = resp.text

        # Try JSON extraction first (more reliable)
        json_listings = _extract_json_data(html)
        if json_listings:
            for item in json_listings:
                parsed = _parse_listing_from_json(item)
                if parsed:
                    all_listings.append(parsed)
        else:
            # Fallback to HTML parsing
            page_listings = _parse_listings_from_html(html)
            all_listings.extend(page_listings)

        # Check if there are more pages
        if not json_listings and not _parse_listings_from_html(html):
            break

        # Rate limiting
        if page < max_pages:
            time.sleep(REQUEST_DELAY)

    # Deduplicate by listing_url
    seen = set()
    unique = []
    for l in all_listings:
        key = l.get("listing_url") or l.get("name", "")
        if key and key not in seen:
            seen.add(key)
            unique.append(l)

    return unique
