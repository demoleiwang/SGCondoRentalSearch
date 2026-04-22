"""Session orchestrator: persona + queries -> SessionBundle.

No LLM calls. All LLM work happens in slash-command prompts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from critics.session import QueryResult, SessionBundle
from engine import parse_query
from smart_search import expand_query


DATA_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"


def _cache_mtime() -> float:
    if not DATA_CACHE_DIR.exists():
        return 0.0
    latest = 0.0
    for p in DATA_CACHE_DIR.glob("*"):
        try:
            latest = max(latest, p.stat().st_mtime)
        except OSError:
            continue
    return latest


def _summarize_smart_search(result) -> dict | None:
    if result is None:
        return None
    return {
        "landmark_name": result.landmark_name,
        "landmark_address": result.landmark_address,
        "strategies_count": len(result.strategies),
        "results_count": len(result.results),
        "strategies": [
            {
                "station": s.station,
                "distance_m": s.distance_m,
                "reason": s.reason,
            }
            for s in result.strategies[:10]
        ],
    }


def _top_raw_results(result, limit: int = 20) -> list[dict]:
    if result is None:
        return []
    rows = []
    for r in result.results[:limit]:
        rows.append({
            "project_name": r.project_name,
            "district": r.district,
            "area_desc": r.area_desc,
            "est_rent": r.est_rent,
            "median_psf": r.median_psf,
            "contracts": r.contracts,
            "strategy": r.strategy_name,
            "url_propertyguru": r.url_propertyguru,
        })
    return rows


def _ranking_notes(result, criteria: dict) -> dict:
    if result is None or not result.results:
        return {"count": 0, "price_range": None, "median": None}
    prices = [r.est_rent for r in result.results]
    return {
        "count": len(prices),
        "price_range": [min(prices), max(prices)],
        "median": sorted(prices)[len(prices) // 2],
        "criteria_budget_max": criteria.get("price_max"),
        "in_budget_count": sum(
            1 for p in prices
            if criteria.get("price_max") is None or p <= criteria["price_max"]
        ),
    }


def run_session(
    persona_id: str,
    queries: list[str],
    with_screenshots: bool = False,
) -> SessionBundle:
    """Execute queries through the search pipeline for a given persona.

    Pure orchestration — no LLM calls, no markdown I/O.
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(
        timespec="seconds"
    )
    bundle_results: list[QueryResult] = []

    for q in queries:
        criteria = parse_query(q)
        smart = None
        try:
            smart = expand_query(q)
        except Exception:
            smart = None

        qr = QueryResult(
            query_text=q,
            parsed_criteria=dict(criteria),
            smart_search_output=_summarize_smart_search(smart),
            raw_results=_top_raw_results(smart),
            ranking_notes=_ranking_notes(smart, criteria),
        )
        bundle_results.append(qr)

    screenshots: list[Path] = []
    if with_screenshots:
        try:
            from take_screenshots import take_all  # type: ignore[attr-defined]
            screenshots = list(take_all())
        except Exception:
            screenshots = []

    return SessionBundle(
        persona_id=persona_id,
        timestamp=timestamp,
        data_cache_mtime=_cache_mtime(),
        query_results=bundle_results,
        screenshots=screenshots,
    )
