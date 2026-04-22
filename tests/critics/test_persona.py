from datetime import date
from pathlib import Path

import pytest

from critics.persona import Persona, load_persona, list_active_personas, save_persona

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_load_persona_parses_frontmatter_and_body():
    p = load_persona(FIXTURE_DIR / "P999-fixture.md")
    assert p.id == "P999"
    assert p.name == "Test Fixture Persona"
    assert p.status == "active"
    assert p.created == date(2026, 1, 1)
    assert p.last_run == date(2026, 1, 10)
    assert p.runs == 2
    assert p.archetype_axes["language"] == "en-only"
    assert "Fixture persona for tests." in p.context
    assert "Plain English queries." in p.search_style
    assert p.lessons == [
        "2026-01-05: First lesson.",
        "2026-01-10: Second lesson.",
    ]


def test_load_persona_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_persona(tmp_path / "missing.md")


def test_load_persona_missing_required_field(tmp_path):
    p = tmp_path / "P800-broken.md"
    p.write_text(
        "---\nid: P800\nstatus: active\n---\n\n## Context\n- foo\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing required frontmatter: name"):
        load_persona(p)


def test_list_active_personas_skips_underscore_and_archive(tmp_path):
    (tmp_path / "_template.md").write_text("ignored", encoding="utf-8")
    (tmp_path / "_archive").mkdir()
    (tmp_path / "_archive" / "P000-old.md").write_text("ignored", encoding="utf-8")

    import shutil
    shutil.copy(FIXTURE_DIR / "P999-fixture.md", tmp_path / "P999-fixture.md")

    result = list_active_personas(tmp_path)
    assert [p.id for p in result] == ["P999"]


def test_save_persona_roundtrip(tmp_path):
    src = FIXTURE_DIR / "P999-fixture.md"
    dst = tmp_path / "P999-fixture.md"
    dst.write_bytes(src.read_bytes())
    p = load_persona(dst)
    p.runs += 1
    p.last_run = date(2026, 2, 1)
    p.lessons.append("2026-02-01: Third lesson.")
    save_persona(p, dst)

    reloaded = load_persona(dst)
    assert reloaded.runs == 3
    assert reloaded.last_run == date(2026, 2, 1)
    assert reloaded.lessons[-1] == "2026-02-01: Third lesson."
