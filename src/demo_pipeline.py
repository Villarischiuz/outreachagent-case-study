"""Runnable, privacy-safe demonstration of the OutreachAgent pipeline.

This module does not contain production scoring logic, credentials, contact data,
or sending functionality. It demonstrates deterministic filtering, explainable
scoring, state transitions, and JSON export using synthetic records.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


SOCIAL_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "tiktok.com",
    "wa.me",
}


@dataclass(frozen=True)
class Business:
    id: int
    name: str
    category: str
    city: str
    website: str | None
    has_https: bool = False
    mobile_ready: bool = False
    load_time_ms: int | None = None
    contact_available: bool = False


@dataclass
class Evaluation:
    business_id: int
    name: str
    state: str
    score: int
    reasons: list[str] = field(default_factory=list)


def normalize_domain(url: str | None) -> str | None:
    """Return a comparable hostname without common presentation differences."""
    if not url:
        return None
    candidate = url if "://" in url else f"https://{url}"
    hostname = (urlparse(candidate).hostname or "").lower()
    return hostname.removeprefix("www.") or None


def is_social_profile(url: str | None) -> bool:
    domain = normalize_domain(url)
    return bool(domain and any(domain == item or domain.endswith(f".{item}") for item in SOCIAL_DOMAINS))


def deduplicate(records: Iterable[Business]) -> list[Business]:
    """Keep the first record for each website domain, or ID when no site exists."""
    seen: set[str] = set()
    output: list[Business] = []
    for record in records:
        key = normalize_domain(record.website) or f"no-site:{record.id}"
        if key in seen:
            continue
        seen.add(key)
        output.append(record)
    return output


def evaluate(record: Business) -> Evaluation:
    """Calculate a simple, explainable demo score and next workflow state."""
    if is_social_profile(record.website):
        return Evaluation(record.id, record.name, "excluded", 0, ["social profile is not audited as a website"])

    score = 0
    reasons: list[str] = []

    if not record.website:
        score += 3
        reasons.append("no independent website")
    else:
        if not record.has_https:
            score += 2
            reasons.append("HTTPS unavailable")
        if not record.mobile_ready:
            score += 2
            reasons.append("mobile readiness issue")
        if record.load_time_ms is not None and record.load_time_ms >= 3_000:
            score += 2
            reasons.append("slow measured load time")

    if record.contact_available:
        score += 1
        reasons.append("contact channel available")

    state = "ready_for_review" if score >= 4 else "not_prioritized"
    return Evaluation(record.id, record.name, state, score, reasons)


def run_pipeline(records: Iterable[Business]) -> list[Evaluation]:
    """Run the deterministic demo pipeline with no external side effects."""
    return [evaluate(record) for record in deduplicate(records)]


def load_businesses(path: Path) -> list[Business]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Input JSON must contain a list of business records")
    return [Business(**item) for item in payload]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the privacy-safe OutreachAgent demo")
    parser.add_argument("input", type=Path, help="JSON file containing synthetic business records")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_pipeline(load_businesses(args.input))
    rendered = json.dumps([asdict(item) for item in results], indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(f"{rendered}\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()

