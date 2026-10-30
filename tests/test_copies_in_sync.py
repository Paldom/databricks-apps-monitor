"""The middleware ships as a wheel (src/) AND as copy-in files (sdk/, demo apps,
provisioning template). This guard keeps every copy byte-identical to the package."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "src" / "monitor_middleware" / "__init__.py"
COPIES = [
    ROOT / "sdk" / "monitor_middleware.py",
    ROOT / "templates" / "basic-app" / "monitor_middleware.py",
    *sorted((ROOT / "example-apps").glob("*/monitor_middleware.py")),
]


@pytest.mark.parametrize("copy", COPIES, ids=lambda p: str(p.relative_to(ROOT)))
def test_copy_matches_canonical(copy: Path) -> None:
    assert copy.exists(), f"expected middleware copy at {copy}"
    assert copy.read_bytes() == CANONICAL.read_bytes(), (
        f"{copy} drifted from src/monitor_middleware/__init__.py — "
        "re-copy it (example-apps/sync-demos.sh syncs the demo fleet)"
    )


def test_demo_fleet_has_all_six_copies() -> None:
    demo = [p for p in COPIES if "example-apps" in str(p)]
    assert len(demo) == 6, f"expected 6 demo-app copies, found {len(demo)}"


def test_sdk_stays_within_copy_in_line_budget() -> None:
    assert len(CANONICAL.read_text().splitlines()) <= 700
