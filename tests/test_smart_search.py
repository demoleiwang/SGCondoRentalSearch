"""Tests for smart search (auto-expand queries by landmark)."""

import sys
sys.path.insert(0, ".")

import pytest
from smart_search import detect_landmark, expand_query, LANDMARKS


class TestDetectLandmark:
    def test_smu(self):
        result = detect_landmark("SMU附近 1br 3300")
        assert result is not None
        assert result[0] == "smu"

    def test_nus(self):
        result = detect_landmark("找NUS附近的1房")
        assert result is not None
        assert result[0] == "nus"

    def test_ntu(self):
        result = detect_landmark("NTU 2br 2000")
        assert result[0] == "ntu"

    def test_cbd(self):
        result = detect_landmark("CBD附近 1b1b 3500")
        assert result[0] == "cbd"

    def test_oue(self):
        result = detect_landmark("OUE Downtown 1br")
        assert result[0] == "oue downtown"

    def test_no_landmark(self):
        result = detect_landmark("Queenstown 1br 3300")
        assert result is None  # Queenstown is an MRT, not a landmark

    def test_case_insensitive(self):
        result = detect_landmark("smu附近")
        assert result is not None


class TestExpandQuery:
    def test_smu_basic(self):
        result = expand_query("SMU附近 1b1b 3300")
        assert result is not None
        assert result.landmark_name == "smu"
        assert result.landmark_coords is not None
        assert len(result.strategies) > 0

    def test_strategies_have_nearby_stations(self):
        result = expand_query("SMU附近 1br 3300")
        station_names = [s.station for s in result.strategies]
        # Bras Basah should be the closest
        assert "Bras Basah" in station_names
        # City Hall, Bencoolen should also be there
        assert any(n in station_names for n in ["City Hall", "Bencoolen", "Dhoby Ghaut"])

    def test_strategies_sorted_by_distance(self):
        result = expand_query("SMU附近 1br 3300")
        distances = [s.distance_m for s in result.strategies]
        assert distances == sorted(distances)

    def test_strategies_have_reasons(self):
        result = expand_query("SMU附近 1br 3300")
        for s in result.strategies:
            assert s.reason  # not empty
            assert s.station  # not empty
            assert s.query_text  # not empty

    def test_results_returned(self):
        result = expand_query("SMU附近 1b1b 3000-4000")
        assert len(result.results) > 0

    def test_results_deduplicated(self):
        result = expand_query("SMU附近 1br 3000-4000")
        project_names = [r.project_name for r in result.results]
        assert len(project_names) == len(set(project_names))

    def test_results_sorted_by_rent(self):
        result = expand_query("SMU附近 1br 3000-4000")
        rents = [r.est_rent for r in result.results]
        assert rents == sorted(rents)

    def test_summary_generated(self):
        result = expand_query("SMU附近 1br 3300")
        assert "SMU" in result.summary
        assert "搜索思路" in result.summary

    def test_nus_nearby(self):
        result = expand_query("NUS附近 1br 2500-3500")
        assert result is not None
        station_names = [s.station for s in result.strategies]
        assert any(n in station_names for n in ["Kent Ridge", "Buona Vista", "one-north"])

    def test_with_facing(self):
        result = expand_query("SMU附近 1br 3300 south facing")
        assert result is not None
        # Extra criteria should flow into query text
        assert any("south facing" in s.query_text or "facing" in s.query_text
                    for s in result.strategies)

    def test_mrt_station_also_expands(self):
        """Even a plain MRT station should expand to nearby stations."""
        result = expand_query("Queenstown 1br 3300")
        assert result is not None
        # Should find Queenstown itself + nearby stations
        station_names = [s.station for s in result.strategies]
        assert "Queenstown" in station_names

    def test_cbd_expands(self):
        result = expand_query("CBD附近 2br 5000")
        assert result is not None
        assert len(result.strategies) > 3

    def test_no_location_returns_none(self):
        result = expand_query("1 bedroom 3000")
        assert result is None


class TestRealScenarios:
    def test_smu_student(self):
        """Student looking near SMU."""
        result = expand_query("我想找SMU附近的1b1b，月租3300左右")
        assert result is not None
        assert len(result.strategies) >= 3
        assert len(result.results) > 0
        # Should include areas like Bras Basah, City Hall, Bugis, Dhoby Ghaut
        stations = {s.station for s in result.strategies}
        assert "Bras Basah" in stations

    def test_nus_student_cheap(self):
        """NUS student on a budget."""
        result = expand_query("NUS附近便宜的1房 2500以内")
        assert result is not None
        if result.results:
            assert all(r.est_rent <= 2750 for r in result.results)  # allow 10% margin

    def test_orchard_worker(self):
        """Someone working near Orchard."""
        result = expand_query("orchard附近 2br 4500")
        assert result is not None
        assert len(result.strategies) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
