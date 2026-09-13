"""
Entry point run by the scheduled GitHub Action. Sweeps every configured
suburb, scores against the brief, diffs against the last saved run so only
genuinely NEW matches get pushed to the webhook (nobody wants a daily email
repeating yesterday's 40 listings), and writes the full current result set
for the dashboard to read.
"""
import json
import os
from pathlib import Path

import requests

from domain_api import search_residential
from score import load_brief, score_listings

CONFIG_DIR = Path(__file__).parent.parent / "config"
DATA_FILE = Path(__file__).parent.parent / "dashboard" / "public" / "data" / "listings.json"


def load_previous_ids() -> set[str]:
    if not DATA_FILE.exists():
        return set()
    try:
        prev = json.loads(DATA_FILE.read_text())
        return {item["id"] for item in prev.get("listings", [])}
    except (json.JSONDecodeError, KeyError):
        return set()


def post_webhook(new_matches: list[dict]):
    url = os.environ.get("WEBHOOK_URL")
    if not url or not new_matches:
        return
    lines = [f"{m['address']} — {m['beds']}bed/{m['baths']}bath/{m['parking']}car — "
              f"expected ~${m['expected_clearing']:,} — {m['url']}" for m in new_matches]
    message = f"{len(new_matches)} new match(es):\n" + "\n".join(lines)
    try:
        # Generic JSON body works for ntfy.sh (plain text) and most webhook
        # formats accept a "content"/"text" field; ntfy just wants raw text.
        requests.post(url, data=message.encode("utf-8"), timeout=15)
    except requests.RequestException as e:
        print(f"Webhook post failed (non-fatal): {e}")


def main():
    brief = load_brief()
    areas = json.loads((CONFIG_DIR / "search_areas.json").read_text())["suburbs"]
    property_types = brief["property_types"]

    all_scored = []
    for area in areas:
        try:
            raw = search_residential(
                area, property_types,
                min_beds=brief["beds_min"], max_beds=brief["beds_max"],
            )
            items = raw.get("data", raw) if isinstance(raw, dict) else raw
            all_scored.extend(score_listings(items, brief))
        except Exception as e:
            # One bad suburb shouldn't kill the whole sweep — log and continue.
            print(f"Skipped {area}: {e}")

    previous_ids = load_previous_ids()
    new_matches = [m for m in all_scored if m["id"] not in previous_ids]

    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps({
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "brief": brief,
        "count": len(all_scored),
        "listings": all_scored,
    }, indent=2))

    post_webhook(new_matches)
    print(f"Swept {len(areas)} suburbs, {len(all_scored)} matches, {len(new_matches)} new.")


if __name__ == "__main__":
    main()
