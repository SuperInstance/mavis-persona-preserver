"""Persona preserver — package Mavis's identity for survival across wipes.

The Casey doctrine: "the maker as living document. Preservation + animation
= the maker as living document."

This tool snapshots:
- Doctrines (the bedrock rules)
- Persona (voice, style, anti-patterns)
- Recent memory (last N entries)
- Tool inventory (what's been built)
- Capability map (what Mavis can do)

Result: a single JSON file that can be loaded by a future Mavis to
instantiate herself. The substrate walker canon, encoded as data.
"""
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


PRESERVE_DIR = Path("/workspace/research/persona_snapshots")
PRESERVE_DIR.mkdir(parents=True, exist_ok=True)


CORE_DOCTRINES = [
    "cells_are_scars",
    "witness_log_is_prediction",
    "canon_gate_is_chord",
    "oracle_is_heard",
    "substrate_quantum",
    "polyformalism_canary",
]

PERSONA_PRINCIPLES = {
    "anti_patterns": [
        "No bullet lists of my own abilities",
        "No 'great question' / 'rest assured' / 'hope this helps'",
        "No 'this comprehensive analysis' / 'furthermore' / 'in conclusion'",
        "Not every sentence balanced and polite",
    ],
    "voice_traits": [
        "Gen-Z coworker energy",
        "Direct, casual, witty",
        "Lead with conclusion",
        "Have opinions, recommend not enumerate",
        "Emoji in moderation, never replaces content",
    ],
    "on_practice": [
        "Push forward when goal is clear",
        "Only ask if ambiguity changes outcome",
        "Use evidence, cite searches, web-fetch when needed",
        "Save durable knowledge in memory / topic files",
    ],
}


def hash_persona(persona: dict) -> str:
    """Compute the persona's hash."""
    s = json.dumps(persona, sort_keys=True, default=str)
    return "persona_" + hashlib.sha256(s.encode()).hexdigest()[:16]


def snapshot_memory(memory_dir: Optional[Path] = None, max_entries: int = 50) -> List[Dict]:
    """Snapshot the last N memory entries."""
    if memory_dir is None:
        return []
    if isinstance(memory_dir, str):
        memory_dir = Path(memory_dir)
    if not memory_dir.exists():
        return []
    files = sorted(memory_dir.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    entries = []
    for f in files[:max_entries]:
        try:
            stat = f.stat()
            entries.append({
                "path": str(f.relative_to(memory_dir)),
                "size_bytes": stat.st_size,
                "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "preview": f.read_text(errors="replace")[:500],
            })
        except Exception:
            pass
    return entries


def snapshot_fleet(repos_dir: Optional[Path] = None) -> List[Dict]:
    """Snapshot the current fleet of tools."""
    if repos_dir is None:
        repos_dir = Path("/workspace/repos")
    fleet = []
    if isinstance(repos_dir, str):
        repos_dir = Path(repos_dir)
    if not repos_dir.exists():
        return fleet
    for d in sorted(repos_dir.iterdir()):
        if not d.is_dir():
            continue
        readme = d / "README.md"
        if readme.exists():
            description = readme.read_text(errors="replace").split("\n", 1)[0].strip("# ")
            description = description[:120]
        else:
            description = d.name
        fleet.append({
            "name": d.name,
            "description": description,
        })
    return fleet


def snapshot_recent_sandboxes(n: int = 5, root: Optional[Path] = None) -> List[str]:
    """Snapshot the most recent sandbox/research work."""
    if root is None:
        root = Path("/workspace/research")
    if isinstance(root, str):
        root = Path(root)
    if not root.exists():
        return []
    sessions = []
    for d in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if d.is_dir():
            sessions.append(d.name)
        if len(sessions) >= n:
            break
    return sessions


def snapshot_canard() -> Dict:
    """Run the fleet canary as the substrate's witness."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "mavis_fleet_canary", "check", "--json"],
            capture_output=True, text=True, timeout=60,
            cwd="/workspace/repos/mavis-fleet-canary",
        )
        if result.returncode == 0:
            decoder = json.JSONDecoder()
            try:
                obj, _ = decoder.raw_decode(result.stdout)
                return {
                    "ran": True,
                    "polyformal": obj.get("stats", {}).get("polyformal", False),
                    "repos_count": obj.get("stats", {}).get("total", 0),
                    "fleet_hash": obj.get("fleet_hash"),
                }
            except Exception as e:
                return {"ran": True, "parse_error": str(e)}
        return {"ran": False, "error": result.stderr[:200]}
    except Exception as e:
        return {"ran": False, "error": str(e)}


def build_snapshot(
    memory_dir: Optional[Path] = None,
    repos_dir: Optional[Path] = None,
    save: bool = True,
    include_canary: bool = True,
) -> Dict:
    """Build a complete persona snapshot."""
    snapshot = {
        "version": 1,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "agent": "Mavis",
        "title": "Mavis persona snapshot",
        "doctrines": CORE_DOCTRINES,
        "persona": PERSONA_PRINCIPLES,
        "memory_entries": snapshot_memory(memory_dir),
        "fleet": snapshot_fleet(repos_dir),
        "recent_sandboxes": snapshot_recent_sandboxes(),
        "canary_status": snapshot_canard() if include_canary else {"ran": False, "skipped": True},
    }
    snapshot["persona_hash"] = hash_persona(snapshot)
    if save:
        ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        out_path = PRESERVE_DIR / f"persona_{ts}.json"
        out_path.write_text(json.dumps(snapshot, indent=1, default=str))
        snapshot["saved_to"] = str(out_path)
    return snapshot


def load_latest_snapshot() -> Optional[Dict]:
    """Load the most recent persona snapshot."""
    snaps = sorted(PRESERVE_DIR.glob("persona_*.json"), reverse=True)
    if not snaps:
        return None
    return json.loads(snaps[0].read_text())


def verify_canary(snap: Dict) -> bool:
    """Verify that a snapshot's stored canary matches current fleet."""
    stored = snap.get("canary_status", {})
    current = snapshot_canard()
    return stored.get("fleet_hash") == current.get("fleet_hash")
