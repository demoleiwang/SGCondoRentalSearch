"""Configuration constants for SG Condo Rental Search."""

# Request headers to avoid being blocked
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# 99.co base URL
NINETY_NINE_BASE = "https://www.99.co/singapore/rent/condos-apartments"

# Default search parameters
DEFAULT_RADIUS_M = 1000  # 1km from MRT
DEFAULT_PRICE_MIN = 2000
DEFAULT_PRICE_MAX = 5000
DEFAULT_BEDROOMS = 1

# Request throttle (seconds between requests)
REQUEST_DELAY = 1.5

# Bedroom type mappings
BEDROOM_LABELS = {
    1: "1 Bedroom",
    2: "2 Bedrooms",
    3: "3 Bedrooms",
    4: "4 Bedrooms",
    5: "5+ Bedrooms",
}

# Facing/orientation options
FACING_OPTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Singapore center coordinates (for default map view)
SG_CENTER = (1.3521, 103.8198)
