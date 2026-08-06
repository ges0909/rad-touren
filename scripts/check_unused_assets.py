#!/usr/bin/env python3
"""Check for unused GPX and image assets in trip directories.

Used as pre-commit hook to prevent orphaned files from accumulating.
Exit code 0 = all assets referenced, exit code 1 = unused assets found.
"""

import re
import sys
from pathlib import Path

TRIPS_DIR = Path(__file__).parent.parent / "trips"
# Only check images - GPX files are intentionally not linked in markdown
ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
ASSET_DIRS = {"img", "maps"}


def find_assets(trip_dir: Path) -> set[Path]:
    """Find all asset files in a trip directory."""
    assets = set()
    for subdir in ASSET_DIRS:
        asset_path = trip_dir / subdir
        if asset_path.exists():
            for f in asset_path.iterdir():
                if f.suffix.lower() in ASSET_EXTENSIONS:
                    assets.add(f)
    return assets


def find_references(trip_dir: Path) -> set[str]:
    """Extract all asset references from markdown files."""
    refs = set()
    pattern = re.compile(r"\(((?:gpx|img|maps)/[^)]+)\)")

    for md_file in trip_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        for match in pattern.findall(content):
            refs.add(match)

    return refs


def check_trip(trip_dir: Path) -> list[Path]:
    """Check a single trip directory for unused assets."""
    assets = find_assets(trip_dir)
    refs = find_references(trip_dir)

    # Convert references to paths relative to trip_dir
    ref_paths = {trip_dir / ref for ref in refs}

    unused = assets - ref_paths
    return sorted(unused)


def main() -> int:
    """Check all trips for unused assets."""
    all_unused: dict[Path, list[Path]] = {}

    for trip_type in TRIPS_DIR.iterdir():
        if not trip_type.is_dir():
            continue
        for trip_dir in trip_type.iterdir():
            if not trip_dir.is_dir():
                continue
            if not (trip_dir / "index.md").exists():
                continue

            unused = check_trip(trip_dir)
            if unused:
                all_unused[trip_dir] = unused

    if not all_unused:
        return 0

    print("Unused assets found:\n", file=sys.stderr)
    for trip_dir, files in all_unused.items():
        rel_trip = trip_dir.relative_to(TRIPS_DIR.parent)
        print(f"  {rel_trip}/", file=sys.stderr)
        for f in files:
            rel_file = f.relative_to(trip_dir)
            print(f"    - {rel_file}", file=sys.stderr)
        print(file=sys.stderr)

    print(
        "Remove unused files or add references in index.md.",
        file=sys.stderr,
    )
    print(
        "To delete: python scripts/check_unused_assets.py --delete",
        file=sys.stderr,
    )

    return 1


def delete_unused() -> int:
    """Delete all unused assets."""
    deleted = 0
    for trip_type in TRIPS_DIR.iterdir():
        if not trip_type.is_dir():
            continue
        for trip_dir in trip_type.iterdir():
            if not trip_dir.is_dir():
                continue
            if not (trip_dir / "index.md").exists():
                continue

            for f in check_trip(trip_dir):
                print(f"Deleting: {f.relative_to(TRIPS_DIR.parent)}")
                f.unlink()
                deleted += 1

    print(f"\nDeleted {deleted} unused file(s).")
    return 0


if __name__ == "__main__":
    if "--delete" in sys.argv:
        sys.exit(delete_unused())
    sys.exit(main())
