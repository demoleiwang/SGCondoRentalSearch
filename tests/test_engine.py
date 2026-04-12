"""Tests for the NL query parser and filter engine."""

import sys
sys.path.insert(0, ".")

import pytest
from engine import parse_query, filter_listings, criteria_to_display


# ===================== MRT STATION EXTRACTION =====================

class TestStationParsing:
    def test_simple_station(self):
        c = parse_query("Queenstown 1br 3300")
        assert c["mrt_station"] == "Queenstown"

    def test_multi_word_station(self):
        c = parse_query("Holland Village 1br 3500")
        assert c["mrt_station"] == "Holland Village"

    def test_hyphenated_station(self):
        c = parse_query("one-north 1br 3000")
        assert c["mrt_station"] == "one-north"

    def test_chinese_context(self):
        c = parse_query("找Bishan附近2房")
        assert c["mrt_station"] == "Bishan"

    def test_no_station(self):
        c = parse_query("1 bedroom 3000")
        assert "mrt_station" not in c

    def test_station_only(self):
        c = parse_query("Queenstown")
        assert c["mrt_station"] == "Queenstown"

    def test_longer_station_preferred(self):
        """Paya Lebar should match before Lebar alone (if it existed)."""
        c = parse_query("Paya Lebar 1br 3200")
        assert c["mrt_station"] == "Paya Lebar"


# ===================== BEDROOM PARSING =====================

class TestBedroomParsing:
    def test_1b1b(self):
        assert parse_query("Queenstown 1b1b 3300")["bedrooms"] == 1

    def test_2b2b(self):
        assert parse_query("Bishan 2b2b 4000")["bedrooms"] == 2

    def test_1_bedroom(self):
        assert parse_query("Novena 1 bedroom 3500")["bedrooms"] == 1

    def test_2br(self):
        assert parse_query("Toa Payoh 2br 4000")["bedrooms"] == 2

    def test_3_room(self):
        assert parse_query("Queenstown 3-room 2500")["bedrooms"] == 3

    def test_3_room_space(self):
        assert parse_query("Bishan 4 room 3000")["bedrooms"] == 4

    def test_chinese_房(self):
        assert parse_query("找Novena附近2房")["bedrooms"] == 2

    def test_studio(self):
        assert parse_query("Dhoby Ghaut studio 2500")["bedrooms"] == 0

    def test_executive(self):
        assert parse_query("executive flat Bishan")["bedrooms"] == 5

    def test_no_bedrooms(self):
        c = parse_query("Queenstown 3300")
        assert "bedrooms" not in c


# ===================== PRICE PARSING =====================

class TestPriceParsing:
    # Approximate (±10%)
    def test_bare_number(self):
        c = parse_query("Queenstown 1br 3300")
        assert c["price_min"] == 2970
        assert c["price_max"] == 3630

    # Ranges
    def test_dash_range(self):
        c = parse_query("Bishan 1br 3000-3500")
        assert c["price_min"] == 3000
        assert c["price_max"] == 3500

    def test_tilde_range(self):
        c = parse_query("Novena 2br 2500~3500")
        assert c["price_min"] == 2500
        assert c["price_max"] == 3500

    def test_to_range(self):
        c = parse_query("Queenstown 1br 3000 to 4000")
        assert c["price_min"] == 3000
        assert c["price_max"] == 4000

    def test_chinese_到_range(self):
        c = parse_query("Bishan 1br 3500到4500")
        assert c["price_min"] == 3500
        assert c["price_max"] == 4500

    def test_dollar_sign_range(self):
        c = parse_query("$3,000-$3,500 1br Queenstown")
        assert c["price_min"] == 3000
        assert c["price_max"] == 3500

    def test_dollar_to_range(self):
        c = parse_query("$3,500 to $4,500 2br Bishan")
        assert c["price_min"] == 3500
        assert c["price_max"] == 4500

    # Under / max
    def test_under_suffix(self):
        c = parse_query("Bishan 1b1b 3500以内")
        assert "price_min" not in c
        assert c["price_max"] == 3500

    def test_under_prefix(self):
        c = parse_query("Orchard 1br under 4000")
        assert c["price_max"] == 4000

    def test_below_prefix(self):
        c = parse_query("Queenstown 2br below 5000")
        assert c["price_max"] == 5000

    def test_不超过(self):
        c = parse_query("Novena studio 不超过2500")
        assert c["price_max"] == 2500

    def test_低于(self):
        c = parse_query("Buona Vista 1br 低于3200")
        assert c["price_max"] == 3200

    def test_dollar_under(self):
        c = parse_query("rent under $4,000 Orchard 1br")
        assert c["price_max"] == 4000

    # Above / min
    def test_at_least_prefix(self):
        c = parse_query("Orchard 2br at least 5000")
        assert c["price_min"] == 5000
        assert "price_max" not in c

    def test_above_prefix(self):
        c = parse_query("Clementi 1br above 2500")
        assert c["price_min"] == 2500

    def test_以上(self):
        c = parse_query("Newton 3br 6000以上")
        assert c["price_min"] == 6000

    def test_至少(self):
        c = parse_query("Novena 2br 至少4000")
        assert c["price_min"] == 4000

    def test_起(self):
        c = parse_query("Queenstown 2房 3000起")
        assert c["price_min"] == 3000

    # Edge: "at least" should not trigger "east" facing
    def test_at_least_no_east_facing(self):
        c = parse_query("Clementi 2br at least 3000")
        assert "facing" not in c


# ===================== FACING PARSING =====================

class TestFacingParsing:
    def test_south_facing(self):
        assert parse_query("Queenstown 1br 3300 south facing")["facing"] == "S"

    def test_north_facing(self):
        assert parse_query("Bishan 2br north facing")["facing"] == "N"

    def test_facing_south(self):
        assert parse_query("Paya Lebar 1br facing south")["facing"] == "S"

    def test_east_facing(self):
        assert parse_query("east facing 2br Toa Payoh")["facing"] == "E"

    def test_west_facing(self):
        assert parse_query("Holland Village 1br west facing")["facing"] == "W"

    def test_southeast(self):
        assert parse_query("southeast facing Queenstown")["facing"] == "SE"

    def test_northeast(self):
        assert parse_query("Bishan 2br northeast facing")["facing"] == "NE"

    def test_southwest(self):
        assert parse_query("southwest facing Clementi")["facing"] == "SW"

    def test_northwest(self):
        assert parse_query("Orchard 1br northwest")["facing"] == "NW"

    def test_chinese_朝南(self):
        assert parse_query("朝南的1房 Novena")["facing"] == "S"

    def test_chinese_朝东南(self):
        assert parse_query("找朝东南的1房 Novena")["facing"] == "SE"

    # False positive prevention
    def test_one_north_no_facing(self):
        """Station name 'one-north' should NOT trigger north facing."""
        c = parse_query("one-north 1br 3000")
        assert "facing" not in c

    def test_least_no_east(self):
        """'at least' should NOT trigger east facing."""
        c = parse_query("Clementi 2br at least 3000")
        assert "facing" not in c


# ===================== FLOOR PARSING =====================

class TestFloorParsing:
    def test_high_floor(self):
        c = parse_query("high floor 1br Queenstown 3500")
        assert c["min_floor"] == 15

    def test_高楼层(self):
        c = parse_query("高楼层 Bishan 2房 4500")
        assert c["min_floor"] == 15

    def test_min_floor_number(self):
        c = parse_query("Novena 1br min floor 10")
        assert c["min_floor"] == 10

    def test_floor_gte(self):
        c = parse_query("Queenstown 1br floor >= 8")
        assert c["min_floor"] == 8

    def test_chinese_楼(self):
        c = parse_query("10楼以上 Bishan 2房 4000")
        assert c["min_floor"] == 10

    def test_low_floor_no_min(self):
        c = parse_query("low floor Bishan 2br 4000")
        assert "min_floor" not in c

    # False positive prevention
    def test_high_floor_1br_not_floor_1(self):
        """'high floor 1br' should be floor >= 15, NOT floor >= 1."""
        c = parse_query("high floor 1br Queenstown 3500")
        assert c["min_floor"] == 15

    def test_高楼层1b1b_not_floor_1(self):
        c = parse_query("帮我找Queenstown附近高楼层1b1b 3300")
        assert c["min_floor"] == 15


# ===================== RADIUS PARSING =====================

class TestRadiusParsing:
    def test_meters(self):
        c = parse_query("500m radius Queenstown 1br 3300")
        assert c["radius_m"] == 500

    def test_km(self):
        c = parse_query("2km内 Bishan 2房")
        assert c["radius_m"] == 2000

    def test_decimal_km(self):
        c = parse_query("1.5km范围 Bishan 1br")
        assert c["radius_m"] == 1500

    def test_chinese_米(self):
        c = parse_query("Clementi 500米内 2房")
        assert c["radius_m"] == 500


# ===================== COMPLEX QUERIES =====================

class TestComplexQueries:
    def test_all_features(self):
        c = parse_query("帮我找Queenstown附近朝南的高楼层1b1b月租3300左右")
        assert c["mrt_station"] == "Queenstown"
        assert c["bedrooms"] == 1
        assert c["facing"] == "S"
        assert c["min_floor"] == 15
        assert 2900 <= c["price_min"] <= 3000
        assert 3600 <= c["price_max"] <= 3700

    def test_english_complex(self):
        c = parse_query("2 bedroom condo near Bishan budget 4000 to 5000 south facing high floor")
        assert c["mrt_station"] == "Bishan"
        assert c["bedrooms"] == 2
        assert c["price_min"] == 4000
        assert c["price_max"] == 5000
        assert c["facing"] == "S"
        assert c["min_floor"] == 15

    def test_hdb_query(self):
        c = parse_query("Queenstown 3-room 2500")
        assert c["mrt_station"] == "Queenstown"
        assert c["bedrooms"] == 3
        assert 2200 <= c["price_min"] <= 2300

    def test_with_radius(self):
        c = parse_query("Clementi地铁站500米内的2房，不超过4500")
        assert c["mrt_station"] == "Clementi"
        assert c["bedrooms"] == 2
        assert c["price_max"] == 4500
        assert c["radius_m"] == 500


# ===================== FILTER ENGINE =====================

class TestFilterListings:
    SAMPLE_LISTINGS = [
        {"name": "A", "price": 3000, "bedrooms": 1, "facing": "S", "floor": "15", "area_sqft": 500},
        {"name": "B", "price": 4000, "bedrooms": 2, "facing": "N", "floor": "8", "area_sqft": 700},
        {"name": "C", "price": 3500, "bedrooms": 1, "facing": "SE", "floor": "20", "area_sqft": 550},
        {"name": "D", "price": 5000, "bedrooms": 3, "facing": "W", "floor": "3", "area_sqft": 1000},
    ]

    def test_filter_by_price(self):
        result = filter_listings(self.SAMPLE_LISTINGS, {"price_min": 3000, "price_max": 3600})
        names = [l["name"] for l in result]
        assert "A" in names
        assert "C" in names
        assert "B" not in names

    def test_filter_by_bedrooms(self):
        result = filter_listings(self.SAMPLE_LISTINGS, {"bedrooms": 1})
        names = [l["name"] for l in result]
        assert names == ["A", "C"]

    def test_filter_by_facing(self):
        result = filter_listings(self.SAMPLE_LISTINGS, {"facing": "S"})
        names = [l["name"] for l in result]
        assert "A" in names
        assert "C" in names  # SE contains S

    def test_filter_by_floor(self):
        result = filter_listings(self.SAMPLE_LISTINGS, {"min_floor": 10})
        names = [l["name"] for l in result]
        assert "A" in names  # floor 15
        assert "C" in names  # floor 20
        assert "B" not in names  # floor 8

    def test_filter_combined(self):
        result = filter_listings(self.SAMPLE_LISTINGS, {
            "bedrooms": 1, "price_min": 3000, "price_max": 4000, "min_floor": 10
        })
        names = [l["name"] for l in result]
        assert names == ["A", "C"]

    def test_empty_criteria(self):
        result = filter_listings(self.SAMPLE_LISTINGS, {})
        assert len(result) == 4


# ===================== DISPLAY =====================

class TestCriteriaDisplay:
    def test_full_display(self):
        d = criteria_to_display({
            "mrt_station": "Queenstown",
            "bedrooms": 1,
            "price_min": 3000,
            "price_max": 3500,
            "facing": "S",
            "min_floor": 15,
        })
        assert "Queenstown" in d
        assert "1 bedroom" in d
        assert "$3000" in d
        assert "$3500" in d
        assert "S" in d
        assert "15" in d

    def test_empty_display(self):
        assert criteria_to_display({}) == "No filters applied"


# ===================== GEO MODULE =====================

class TestGeoModule:
    def test_find_station(self):
        from geo import find_station
        s = find_station("Queenstown")
        assert s is not None
        assert s["name"] == "Queenstown"
        assert abs(s["lat"] - 1.2946) < 0.01

    def test_station_names_count(self):
        from geo import get_station_names
        names = get_station_names()
        assert len(names) >= 130

    def test_haversine(self):
        from geo import haversine
        # Queenstown to Commonwealth should be ~1-2km
        dist = haversine(1.2946, 103.7858, 1.3023, 103.7985)
        assert 500 < dist < 2000

    def test_geocode(self):
        from geo import geocode_address
        coords = geocode_address("QUEENS PEAK")
        assert coords is not None
        lat, lng = coords
        assert 1.29 < lat < 1.30
        assert 103.80 < lng < 103.82


# ===================== DATA MODULES =====================

class TestDataModules:
    def test_condo_data_loads(self):
        from scraper.data_gov import fetch_rental_data
        df = fetch_rental_data()
        assert len(df) > 500
        assert "project_name" in df.columns
        assert "median_psf" in df.columns
        assert "est_rent_1br" in df.columns

    def test_hdb_data_loads(self):
        from scraper.hdb import fetch_hdb_rental_data
        df = fetch_hdb_rental_data()
        assert len(df) > 10000
        assert "town" in df.columns
        assert "monthly_rent" in df.columns

    def test_district_mapping(self):
        from scraper.data_gov import get_districts_for_mrt
        districts = get_districts_for_mrt("Queenstown")
        assert 3 in districts

    def test_town_mapping(self):
        from scraper.hdb import get_towns_for_mrt
        towns = get_towns_for_mrt("Queenstown")
        assert "QUEENSTOWN" in towns

    def test_99co_url(self):
        from scraper.data_gov import build_99co_url
        url = build_99co_url(location="Queenstown", bedrooms=1, price_min=3000, price_max=3500)
        assert "99.co" in url
        assert "Queenstown" in url
        assert "bedroom_num=1" in url


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
