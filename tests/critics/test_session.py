from pathlib import Path

import pytest

from critics.session import (
    QueryResult,
    SessionBundle,
    load_session_log,
    write_session_log,
)


def _sample_bundle(persona_id="P999") -> SessionBundle:
    return SessionBundle(
        persona_id=persona_id,
        timestamp="2026-04-22T10:30:00",
        data_cache_mtime=1713783600.0,
        query_results=[
            QueryResult(
                query_text="2b2b near OUE Downtown 4500",
                parsed_criteria={"bedrooms": 2, "bathrooms": 2, "price_max": 4500},
                smart_search_output={
                    "landmark_name": "oue downtown",
                    "strategies_count": 8,
                    "results_count": 23,
                },
                raw_results=[
                    {"project_name": "Icon", "est_rent": 4300, "district": 2},
                ],
                ranking_notes={"count": 23, "median": 4200},
            ),
        ],
        screenshots=[],
    )


def test_write_and_load_session_log_roundtrip(tmp_path):
    bundle = _sample_bundle()
    path = tmp_path / "2026-04-22-P999.md"
    write_session_log(bundle, path)
    assert path.exists()

    loaded = load_session_log(path)
    assert loaded.persona_id == "P999"
    assert loaded.timestamp == "2026-04-22T10:30:00"
    assert len(loaded.query_results) == 1
    assert loaded.query_results[0].query_text == "2b2b near OUE Downtown 4500"
    assert loaded.query_results[0].parsed_criteria["bedrooms"] == 2
    assert loaded.query_results[0].smart_search_output["strategies_count"] == 8
    assert loaded.query_results[0].raw_results[0]["project_name"] == "Icon"


def test_write_session_log_contains_required_sections(tmp_path):
    path = tmp_path / "2026-04-22-P999.md"
    write_session_log(_sample_bundle(), path)
    text = path.read_text(encoding="utf-8")
    assert "# Session 2026-04-22 — P999" in text
    assert "## Queries" in text
    assert "## Results" in text
    assert "## Critique" in text
    assert "## Findings" in text


def test_load_session_log_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_session_log(tmp_path / "missing.md")
