"""Tests for commute-based smart search."""

import sys
sys.path.insert(0, ".")

import pytest
from commute import (
    Location, StationScore, geocode_location,
    analyze_commute, generate_queries, format_analysis_report,
)


# ===================== GEOCODING =====================

class TestGeocodeLocation:
    def test_geocode_smu(self):
        loc = Location(name="SMU", address="Singapore Management University")
        geocode_location(loc)
        assert loc.lat > 0
        assert loc.lng > 0
        assert len(loc.nearby_stations) > 0
        # Bras Basah should be the nearest
        assert loc.nearby_stations[0][0] == "Bras Basah"

    def test_geocode_oue(self):
        loc = Location(name="Office", address="OUE Downtown One")
        geocode_location(loc)
        assert loc.lat > 0
        assert len(loc.nearby_stations) > 0
        # Shenton Way or Tanjong Pagar should be nearest
        nearest_names = [s[0] for s in loc.nearby_stations[:3]]
        assert any(n in nearest_names for n in ["Shenton Way", "Tanjong Pagar", "Downtown"])

    def test_geocode_nus(self):
        loc = Location(name="NUS", address="National University of Singapore")
        geocode_location(loc)
        assert loc.lat > 0

    def test_geocode_changi_bp(self):
        loc = Location(name="Office", address="Changi Business Park")
        geocode_location(loc)
        assert loc.lat > 0


# ===================== COMMUTE ANALYSIS =====================

class TestAnalyzeCommute:
    @pytest.fixture
    def smu_oue_locations(self):
        return [
            Location(name="SMU", address="Singapore Management University"),
            Location(name="Office", address="OUE Downtown One"),
        ]

    def test_returns_scored_stations(self, smu_oue_locations):
        results = analyze_commute(smu_oue_locations)
        assert len(results) > 0
        # Should be sorted by score (ascending)
        for i in range(1, min(len(results), 10)):
            assert results[i].total_score >= results[i - 1].total_score

    def test_top_stations_are_central(self, smu_oue_locations):
        results = analyze_commute(smu_oue_locations)
        top_15_names = [r.name for r in results[:15]]
        # Stations near or between SMU and OUE should rank high
        central_stations = {"Raffles Place", "Tanjong Pagar", "City Hall",
                            "Chinatown", "Downtown", "Telok Ayer", "Shenton Way",
                            "Fort Canning", "Dhoby Ghaut", "Bras Basah", "Bencoolen",
                            "Clarke Quay", "Bayfront", "Marina Bay"}
        overlap = central_stations & set(top_15_names)
        assert len(overlap) >= 3, f"Expected central stations in top 15, got {top_15_names}"

    def test_commute_details_present(self, smu_oue_locations):
        results = analyze_commute(smu_oue_locations)
        top = results[0]
        assert "SMU" in top.commute_details
        assert "Office" in top.commute_details
        assert "distance_m" in top.commute_details["SMU"]
        assert "transfers" in top.commute_details["SMU"]

    def test_single_location(self):
        locations = [Location(name="SMU", address="Singapore Management University")]
        results = analyze_commute(locations)
        assert len(results) > 0

    def test_three_locations(self):
        locations = [
            Location(name="School", address="Singapore Management University"),
            Location(name="Office", address="OUE Downtown One"),
            Location(name="Gym", address="Orchard Road Singapore"),
        ]
        results = analyze_commute(locations)
        assert len(results) > 0
        top = results[0]
        assert "School" in top.commute_details
        assert "Office" in top.commute_details
        assert "Gym" in top.commute_details


# ===================== QUERY GENERATION =====================

class TestGenerateQueries:
    @pytest.fixture
    def scored_stations(self):
        locs = [
            Location(name="SMU", address="Singapore Management University"),
            Location(name="Office", address="OUE Downtown One"),
        ]
        return analyze_commute(locs)

    def test_generates_queries(self, scored_stations):
        queries = generate_queries(scored_stations, bedrooms=1, price_min=3000, price_max=3500)
        assert len(queries) > 0
        assert len(queries) <= 10

    def test_query_has_required_fields(self, scored_stations):
        queries = generate_queries(scored_stations, bedrooms=1, price_max=3500)
        for q in queries:
            assert "station" in q
            assert "query_text" in q
            assert "criteria" in q
            assert "reason" in q
            assert q["station"]  # not empty

    def test_query_criteria_parsed(self, scored_stations):
        queries = generate_queries(scored_stations, bedrooms=1, price_min=3000, price_max=3500)
        for q in queries:
            c = q["criteria"]
            assert c.get("mrt_station") == q["station"]
            assert c.get("bedrooms") == 1

    def test_different_bedrooms(self, scored_stations):
        q1 = generate_queries(scored_stations, bedrooms=1)
        q2 = generate_queries(scored_stations, bedrooms=2)
        assert q1[0]["criteria"].get("bedrooms") == 1
        assert q2[0]["criteria"].get("bedrooms") == 2

    def test_extra_criteria(self, scored_stations):
        queries = generate_queries(scored_stations, bedrooms=1, price_max=3500, extra_criteria="south facing")
        assert "south facing" in queries[0]["query_text"]

    def test_max_queries_limit(self, scored_stations):
        queries = generate_queries(scored_stations, bedrooms=1, max_queries=5)
        assert len(queries) <= 5

    def test_no_duplicate_stations(self, scored_stations):
        queries = generate_queries(scored_stations, bedrooms=1)
        stations = [q["station"] for q in queries]
        assert len(stations) == len(set(stations))


# ===================== REPORT =====================

class TestFormatReport:
    def test_report_content(self):
        locs = [
            Location(name="SMU", address="Singapore Management University"),
            Location(name="Office", address="OUE Downtown One"),
        ]
        scored = analyze_commute(locs)
        queries = generate_queries(scored, bedrooms=1, price_min=3000, price_max=3500)
        report = format_analysis_report(locs, queries)

        assert "SMU" in report
        assert "Office" in report
        assert "Recommended Areas" in report
        assert len(report) > 100


# ===================== REAL-WORLD SCENARIOS =====================

class TestRealScenarios:
    def test_smu_student_oue_worker(self):
        """Core use case: study at SMU, work at OUE Downtown One."""
        locs = [
            Location(name="SMU", address="Singapore Management University"),
            Location(name="Office", address="OUE Downtown One"),
        ]
        scored = analyze_commute(locs)
        assert len(scored) >= 5, "Should find multiple candidate stations"
        queries = generate_queries(scored, bedrooms=1, price_min=3000, price_max=3500)
        assert len(queries) >= 3
        for q in queries:
            assert q["criteria"].get("mrt_station")

    def test_ntu_student_cbd_worker(self):
        """Study at NTU, work in CBD."""
        locs = [
            Location(name="NTU", address="Nanyang Technological University"),
            Location(name="Office", address="Raffles Place Singapore"),
        ]
        scored = analyze_commute(locs)
        queries = generate_queries(scored, bedrooms=1, price_max=2500)
        assert len(queries) >= 1

    def test_nus_student_one_north_worker(self):
        """Study at NUS, work at one-north."""
        locs = [
            Location(name="NUS", address="National University of Singapore"),
            Location(name="Office", address="one-north Singapore"),
        ]
        scored = analyze_commute(locs)
        queries = generate_queries(scored, bedrooms=1, price_max=3000)
        assert len(queries) >= 3
        # Buona Vista / Kent Ridge should rank high
        top_names = [q["station"] for q in queries[:5]]
        nearby = {"Buona Vista", "Kent Ridge", "one-north", "Dover", "Clementi"}
        assert any(n in top_names for n in nearby)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
