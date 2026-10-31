#!/usr/bin/env python3
"""Cross-check discovered jobs against job_search_tracker.csv to prevent duplicate applications.

scrape_state.py's dedup keys on URL and exact company+title. That misses the common case
where the same role is found on a different portal than the one applied through: the URL
differs, and portal CLIs decorate the company name (LinkedIn returns "OakNorth in India"
for "OakNorth"). The result is a job already applied to being presented as new.

This normalizes both sides before comparing, so a role already in the tracker is caught
regardless of which portal surfaced it.

Usage:
  python tools/applied_check.py --results <discovered.json> [--tracker job_search_tracker.csv]
  python tools/applied_check.py --results <discovered.json> --json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# Legal-form and decoration noise stripped before comparing company names.
_SUFFIXES = (
    "private limited", "pvt ltd", "pvt. ltd.", "pvt limited", "limited", "ltd",
    "incorporated", "inc", "llc", "llp", "corporation", "corp", "gmbh", "bv", "nv",
    "plc", "sa", "ag", "co", "company", "technologies", "technology", "solutions",
    "software", "systems", "labs", "india",
)

# Title noise: seniority markers and level suffixes that do not change role identity.
_TITLE_NOISE = re.compile(
    r"\b(sr\.?|senior|jr\.?|junior|staff|principal|lead|i|ii|iii|iv|1|2|3|4)\b",
    re.I,
)


def norm_company(raw: str | None) -> str:
    """Normalize a company name for comparison."""
    if not raw:
        return ""
    s = raw.casefold().strip()
    # LinkedIn decorates with " in <location>" / " at <location>"
    s = re.sub(r"\s+(in|at)\s+[a-z .,'-]+$", "", s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # Strip trailing legal-form / filler tokens, repeatedly.
    changed = True
    while changed:
        changed = False
        for suf in _SUFFIXES:
            if s.endswith(" " + suf):
                s = s[: -(len(suf) + 1)].strip()
                changed = True
    return s


def norm_title(raw: str | None) -> str:
    """Normalize a job title for comparison."""
    if not raw:
        return ""
    s = raw.casefold()
    s = re.sub(r"[^\w\s]", " ", s)
    s = _TITLE_NOISE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_tracker(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", required=True,
                    help="JSON array of discovered jobs (title, company, url)")
    ap.add_argument("--tracker", default="job_search_tracker.csv")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a summary")
    args = ap.parse_args()

    try:
        jobs = json.loads(Path(args.results).read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"applied_check: cannot read --results: {exc}", file=sys.stderr)
        return 2
    if not isinstance(jobs, list):
        print("applied_check: --results must be a JSON array", file=sys.stderr)
        return 2

    rows = load_tracker(Path(args.tracker))

    # Statuses that mean "do not surface this again as new".
    blocking = {
        "applied", "approved", "acknowledged", "assessment", "interview",
        "interviewing", "interview_only", "offer", "hired", "rejected",
        "offer_declined", "offer declined", "withdrawn", "no_response",
        "no response",
    }
    seen_pairs: dict[tuple[str, str], dict] = {}
    seen_companies: dict[str, dict] = {}
    for r in rows:
        status = (r.get("status") or "").strip().casefold()
        if status not in blocking:
            continue
        c, t = norm_company(r.get("company")), norm_title(r.get("role"))
        if c:
            seen_pairs[(c, t)] = r
            seen_companies.setdefault(c, r)

    clear, collisions = [], []
    for j in jobs:
        c, t = norm_company(j.get("company")), norm_title(j.get("title"))
        hit = seen_pairs.get((c, t))
        kind = "company+title"
        if not hit and c in seen_companies:
            hit, kind = seen_companies[c], "company-only"
        if not hit and c:
            # "OakNorth Bank" vs "OakNorth", "Emerson Electric" vs "Emerson": one name
            # extends the other. Too weak to auto-exclude, strong enough to review.
            for known, row in seen_companies.items():
                if not known:
                    continue
                a, b = sorted((c, known), key=len)
                if b.startswith(a + " ") or b == a:
                    hit, kind = row, "company-prefix"
                    break
        if hit:
            collisions.append({
                "title": j.get("title"), "company": j.get("company"),
                "url": j.get("url"), "match_type": kind,
                "tracker_company": hit.get("company"), "tracker_role": hit.get("role"),
                "tracker_status": hit.get("status"), "tracker_date": hit.get("date"),
                "tracker_url": hit.get("source"),
            })
        else:
            clear.append(j)

    if args.json:
        print(json.dumps({"clear": clear, "collisions": collisions,
                          "clear_count": len(clear),
                          "collision_count": len(collisions)}, indent=1, ensure_ascii=False))
        return 0

    print(f"applied_check: {len(clear)} clear, {len(collisions)} collision(s) "
          f"against {len(seen_pairs)} tracked application(s)")
    for c in collisions:
        flag = "DUPLICATE" if c["match_type"] == "company+title" else "SAME COMPANY"
        print(f"  [{flag}] {c['company']} - {c['title']}")
        print(f"      tracker: {c['tracker_company']} / {c['tracker_role']} "
              f"/ {c['tracker_status']} / {c['tracker_date']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
