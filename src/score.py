"""
Applies config/brief.json to raw Domain listings: computes expected clearing
price (guide + underquote assumption), a scarcity heuristic from scheme lot
count where available, and flags matches. This mirrors the manual scoring
used throughout the chat-based sweeps — codified so it runs unattended.
"""
import json
import re
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_brief() -> dict:
    return json.loads((CONFIG_DIR / "brief.json").read_text())


def parse_guide_price(price_text: str) -> tuple[float | None, str]:
    """Extract a numeric guide from Domain's free-text price field and guess
    the sale method (auction vs private treaty) from the same text — this is
    the single biggest source of bad data in manual scraping, so keep it
    conservative: return None rather than guess wrong."""
    if not price_text:
        return None, "unknown"
    method = "auction" if re.search(r"auction", price_text, re.I) else "private_treaty"
    nums = re.findall(r"\$?([\d,]+(?:\.\d+)?)\s*[mM]?", price_text)
    cleaned = [n.replace(",", "") for n in nums if n]
    if not cleaned:
        return None, method
    val = float(cleaned[0])
    # Domain sometimes returns "1.45m" style already-expanded numbers, sometimes
    # full digits ("1450000") — disambiguate by magnitude.
    if val < 100:
        val *= 1_000_000
    return val, method


def expected_clearing(guide: float, method: str, brief: dict) -> float:
    uplift = brief["underquote_assumption"].get(method, 0.05)
    return guide * (1 + uplift)


def scarcity_score(listing: dict) -> int:
    """Heuristic until Strata Hub / lot-count integration lands (see build doc
    Stage 1.5): houses and torrens-title score high by default; strata schemes
    are scored down by apparent building size where Domain exposes it. This is
    a placeholder — replace with real unit-entitlement counts once the NSW
    Strata Hub feed is wired in."""
    prop_type = (listing.get("propertyDetails", {}).get("propertyType") or "").lower()
    if prop_type in ("house", "terrace", "duplex", "semi-detached"):
        return 90
    unit_number = listing.get("propertyDetails", {}).get("unitNumber", "")
    digits = re.findall(r"\d+", unit_number)
    if digits and int(digits[0]) > 50:
        return 40  # large-complex signal
    return 65  # unknown — mid-default, never claim false precision


def score_listings(raw_listings: list[dict], brief: dict) -> list[dict]:
    scored = []
    for item in raw_listings:
        listing = item.get("listing", item)
        price_text = listing.get("priceDetails", {}).get("displayPrice", "")
        guide, method = parse_guide_price(price_text)
        if guide is None:
            continue
        expected = expected_clearing(guide, method, brief)
        if expected > brief["expected_price_cap"]:
            continue
        scarcity = scarcity_score(listing)
        if scarcity < brief["scarcity_min"]:
            continue
        scored.append({
            "id": listing.get("id"),
            "address": listing.get("propertyDetails", {}).get("displayableAddress"),
            "beds": listing.get("propertyDetails", {}).get("bedrooms"),
            "baths": listing.get("propertyDetails", {}).get("bathrooms"),
            "parking": listing.get("propertyDetails", {}).get("carspaces"),
            "guide_price": guide,
            "expected_clearing": round(expected),
            "method": method,
            "scarcity": scarcity,
            "url": listing.get("seoUrl") or listing.get("url"),
        })
    return sorted(scored, key=lambda x: x["expected_clearing"])
