from pathlib import Path

from critics.run_session import run_session
from critics.session import SessionBundle


def test_run_session_returns_bundle_with_expected_shape():
    queries = ["Queenstown 1b1b 3300", "OUE Downtown 2b2b 4500"]
    bundle = run_session(persona_id="P001", queries=queries)
    assert isinstance(bundle, SessionBundle)
    assert bundle.persona_id == "P001"
    assert len(bundle.query_results) == 2
    assert bundle.query_results[0].query_text == queries[0]
    assert "bedrooms" in bundle.query_results[0].parsed_criteria


def test_run_session_landmark_query_has_smart_output():
    bundle = run_session(persona_id="P001", queries=["OUE Downtown 2b2b 4500"])
    qr = bundle.query_results[0]
    assert qr.smart_search_output is not None
    assert "strategies_count" in qr.smart_search_output
    assert "results_count" in qr.smart_search_output


def test_run_session_non_landmark_query_has_smart_or_none():
    # "Queenstown" alone is an MRT station, not a landmark;
    # expand_query may return a SmartSearchResult using the station as center
    # or return None. Either is valid — we just check it doesn't crash.
    bundle = run_session(persona_id="P001", queries=["Queenstown 1b1b 3300"])
    qr = bundle.query_results[0]
    assert qr.smart_search_output is None or isinstance(qr.smart_search_output, dict)


def test_run_session_ranking_notes_present():
    bundle = run_session(persona_id="P001", queries=["Queenstown 1b1b 3300"])
    qr = bundle.query_results[0]
    assert "count" in qr.ranking_notes
    assert "price_range" in qr.ranking_notes
