"""Take screenshots of the Streamlit app for README."""

import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8501"
OUT_DIR = "docs/screenshots"


def take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        # 1. Welcome / Home page
        print("1. Home page...")
        page.goto(BASE_URL, wait_until="networkidle")
        time.sleep(3)
        page.screenshot(path=f"{OUT_DIR}/01_home.png", full_page=False)

        # 2. Condo search results (top: metrics + first listings)
        print("2. Condo search...")
        search_input = page.locator('input[aria-label*="Search"]')
        search_input.fill("Queenstown 1b1b 3300")
        search_input.press("Enter")
        time.sleep(10)  # Wait for data + geocoding
        page.screenshot(path=f"{OUT_DIR}/02_condo_search.png", full_page=False)

        # 3. Scroll to map (it's after the listings, at bottom)
        print("3. Map view...")
        # Find the map iframe/element
        map_el = page.locator("iframe").first
        if map_el.count() > 0:
            map_el.scroll_into_view_if_needed()
            time.sleep(2)
            page.screenshot(path=f"{OUT_DIR}/03_map_view.png", full_page=False)
        else:
            # Try scrolling to the map header
            page.evaluate("document.querySelectorAll('h2').forEach(h => { if(h.textContent.includes('Map')) h.scrollIntoView() })")
            time.sleep(2)
            page.screenshot(path=f"{OUT_DIR}/03_map_view.png", full_page=False)

        # 4. Condo listing cards (scroll back up a bit)
        print("4. Condo listings...")
        page.evaluate("document.querySelectorAll('h2').forEach(h => { if(h.textContent.includes('Condo Projects')) h.scrollIntoView() })")
        time.sleep(1)
        page.screenshot(path=f"{OUT_DIR}/04_condo_listings.png", full_page=False)

        # 5. Full page condo search
        print("5. Full page condo...")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
        page.screenshot(path=f"{OUT_DIR}/05_full_condo.png", full_page=True)

        # 6. Switch to HDB
        print("6. HDB search...")
        page.goto(BASE_URL, wait_until="networkidle")
        time.sleep(3)

        # Click HDB radio
        hdb_label = page.locator('label:has-text("HDB")')
        if hdb_label.count() > 0:
            hdb_label.first.click()
            time.sleep(1)

        search_input = page.locator('input[aria-label*="Search"]')
        search_input.fill("Queenstown 3-room 2500")
        search_input.press("Enter")
        time.sleep(10)
        page.screenshot(path=f"{OUT_DIR}/06_hdb_search.png", full_page=False)

        # 7. HDB listings
        print("7. HDB listings...")
        page.evaluate("document.querySelectorAll('h2').forEach(h => { if(h.textContent.includes('HDB')) h.scrollIntoView() })")
        time.sleep(1)
        page.screenshot(path=f"{OUT_DIR}/07_hdb_listings.png", full_page=False)

        # 8. HDB map
        print("8. HDB map...")
        map_el = page.locator("iframe").first
        if map_el.count() > 0:
            map_el.scroll_into_view_if_needed()
            time.sleep(2)
            page.screenshot(path=f"{OUT_DIR}/08_hdb_map.png", full_page=False)

        browser.close()
        print(f"Done! Screenshots saved to {OUT_DIR}/")


if __name__ == "__main__":
    take_screenshots()
