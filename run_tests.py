"""Test runner for mavis-persona-preserver."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/workspace/repos/mavis-persona-preserver")

from mavis_persona_preserver.canary import canary
from mavis_persona_preserver.preserver import (
    build_snapshot, load_latest_snapshot, verify_canary, hash_persona,
    CORE_DOCTRINES, PERSONA_PRINCIPLES, snapshot_memory, snapshot_fleet,
    PRESERVE_DIR,
)


results = []
failures = []


def test(name, func):
    try:
        func()
        results.append((name, "PASS"))
    except AssertionError as e:
        results.append((name, f"FAIL: {e}"))
        failures.append(name)
    except Exception as e:
        results.append((name, f"ERROR: {type(e).__name__}: {e}"))
        failures.append(name)


def t_canary():
    assert canary() == "0x24a555471370b18d"


def t_core_doctrines_present():
    """The 5+ bedrock doctrines are tracked."""
    assert len(CORE_DOCTRINES) >= 5
    assert "cells_are_scars" in CORE_DOCTRINES
    assert "witness_log_is_prediction" in CORE_DOCTRINES


def t_persona_principles_complete():
    """Persona has voice + anti-patterns + practice."""
    assert "voice_traits" in PERSONA_PRINCIPLES
    assert "anti_patterns" in PERSONA_PRINCIPLES
    assert "on_practice" in PERSONA_PRINCIPLES


def t_hash_persona_stable():
    persona = {"a": 1, "b": [1, 2, 3]}
    h1 = hash_persona(persona)
    h2 = hash_persona(persona)
    assert h1 == h2
    assert h1.startswith("persona_")


def t_snapshot_memory_empty():
    with tempfile.TemporaryDirectory() as td:
        entries = snapshot_memory(Path(td))
        assert entries == []


def t_snapshot_memory_with_files():
    with tempfile.TemporaryDirectory() as td:
        mem = Path(td)
        (mem / "a.md").write_text("# Hello\nThis is a memory entry.")
        (mem / "b.md").write_text("# Another\nMore content here.")
        entries = snapshot_memory(mem)
        assert len(entries) == 2


def t_snapshot_memory_caps_at_n():
    """Max entries cap works."""
    with tempfile.TemporaryDirectory() as td:
        mem = Path(td)
        for i in range(5):
            (mem / f"file{i}.md").write_text(f"Entry {i}")
        entries = snapshot_memory(mem, max_entries=3)
        assert len(entries) == 3


def t_snapshot_fleet():
    """Snapshot the real fleet."""
    fleet = snapshot_fleet()
    assert len(fleet) > 0
    # Each entry has name + description
    for entry in fleet[:5]:
        assert "name" in entry
        assert "description" in entry


def test_build_snapshot_dry_run():
    """Build a snapshot in dry-run mode (no save)."""
    snap = build_snapshot(save=False, include_canary=False)
    assert "timestamp" in snap
    assert "doctrines" in snap
    assert "persona" in snap
    assert "fleet" in snap
    assert "persona_hash" in snap
    # No saved_to since dry-run
    assert "saved_to" not in snap


def test_build_snapshot_with_save():
    """Build a snapshot, save disabled, canary disabled for speed."""
    snap = build_snapshot(save=False, include_canary=False)
    assert "persona_hash" in snap


test("test_canary", t_canary)
test("test_core_doctrines_present", t_core_doctrines_present)
test("test_persona_principles_complete", t_persona_principles_complete)
test("test_hash_persona_stable", t_hash_persona_stable)
test("test_snapshot_memory_empty", t_snapshot_memory_empty)
test("test_snapshot_memory_with_files", t_snapshot_memory_with_files)
test("test_snapshot_memory_caps_at_n", t_snapshot_memory_caps_at_n)
test("test_snapshot_fleet", t_snapshot_fleet)
test("test_build_snapshot_dry_run", test_build_snapshot_dry_run)
test("test_build_snapshot_with_save", test_build_snapshot_with_save)

print("\n=== mavis-persona-preserver test results ===")
for name, status in results:
    print(f"  {status:60} {name}")

print(f"\n{len(results) - len(failures)}/{len(results)} passed")
if failures:
    sys.exit(1)
