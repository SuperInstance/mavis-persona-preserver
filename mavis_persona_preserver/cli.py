"""CLI for mavis-persona-preserver."""
import argparse
import json
import sys
from pathlib import Path

from .preserver import (
    build_snapshot, load_latest_snapshot, verify_canary,
    PRESERVE_DIR, hash_persona,
)


def cmd_snapshot(args):
    """Build a new snapshot."""
    snap = build_snapshot(
        memory_dir=Path(args.memory_dir) if args.memory_dir else None,
        repos_dir=Path(args.repos_dir) if args.repos_dir else None,
        save=not args.dry_run,
    )
    if args.json:
        print(json.dumps(snap, indent=1, default=str))
    else:
        print(f"✓ Snapshot built")
        print(f"  Timestamp: {snap.get('timestamp')}")
        print(f"  Doctrines: {len(snap['doctrines'])}")
        print(f"  Memory entries: {len(snap['memory_entries'])}")
        print(f"  Fleet size: {len(snap['fleet'])} repos")
        print(f"  Recent sandboxes: {snap['recent_sandboxes']}")
        print(f"  Canary: polyformal={snap['canary_status'].get('polyformal')}, "
              f"repos={snap['canary_status'].get('repos_count')}")
        print(f"  Hash: {snap['persona_hash']}")
        if "saved_to" in snap:
            print(f"  Saved: {snap['saved_to']}")


def cmd_load(args):
    """Load the latest snapshot."""
    snap = load_latest_snapshot()
    if snap is None:
        print("✗ No snapshots found")
        sys.exit(1)
    if args.json:
        print(json.dumps(snap, indent=1, default=str))
    else:
        print(f"=== Latest snapshot ===")
        print(f"  Timestamp: {snap.get('timestamp')}")
        print(f"  Doctrines: {', '.join(snap['doctrines'])}")
        print(f"  Persona hash: {snap['persona_hash']}")


def cmd_verify(args):
    """Verify a snapshot's canary matches the current fleet."""
    snap = load_latest_snapshot()
    if snap is None:
        print("✗ No snapshot to verify")
        sys.exit(1)
    matches = verify_canary(snap)
    if matches:
        print("✓ Snapshot canary matches current fleet")
    else:
        print("✗ Snapshot canary DRIFTED — fleet changed since snapshot")
        stored = snap.get("canary_status", {})
        print(f"  Stored fleet_hash: {stored.get('fleet_hash')}")
        sys.exit(1)


def cmd_list(args):
    """List all snapshots."""
    snaps = sorted(PRESERVE_DIR.glob("persona_*.json"), reverse=True)
    print(f"=== {len(snaps)} snapshots ===")
    for s in snaps:
        print(f"  {s.name}")


def main():
    p = argparse.ArgumentParser(description="mavis-persona-preserver — package Mavis's identity for survival")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_s = sub.add_parser("snapshot", help="Build a new snapshot")
    p_s.add_argument("--memory-dir")
    p_s.add_argument("--repos-dir")
    p_s.add_argument("--dry-run", action="store_true")
    p_s.add_argument("--json", action="store_true")
    p_s.set_defaults(func=cmd_snapshot)

    p_l = sub.add_parser("load", help="Load latest snapshot")
    p_l.add_argument("--json", action="store_true")
    p_l.set_defaults(func=cmd_load)

    sub.add_parser("verify", help="Verify latest snapshot's canary").set_defaults(func=cmd_verify)
    sub.add_parser("list", help="List snapshots").set_defaults(func=cmd_list)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
