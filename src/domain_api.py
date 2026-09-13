"""
Domain API client — client-credentials OAuth + residential listing search.
Docs: https://developer.domain.com.au/docs/latest/apis/

Requires env vars: DOMAIN_CLIENT_ID, DOMAIN_CLIENT_SECRET
"""
import os
import time
import requests

AUTH_URL = "https://auth.domain.com.au/v1/connect/token"
API_BASE = "https://api.domain.com.au"

_token_cache = {"token": None, "expires_at": 0}


def get_access_token() -> str:
    """Client-credentials grant. Domain API tokens are short-lived; cache and refresh."""
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - 30:
        return _token_cache["token"]

    client_id = os.environ["DOMAIN_CLIENT_ID"]
    client_secret = os.environ["DOMAIN_CLIENT_SECRET"]

    resp = requests.post(
        AUTH_URL,
        data={"grant_type": "client_credentials", "scope": "api_listings_read"},
        auth=(client_id, client_secret),
        timeout=20,
    )
    resp.raise_for_status()
    payload = resp.json()
    _token_cache["token"] = payload["access_token"]
    _token_cache["expires_at"] = now + payload.get("expires_in", 3600)
    return _token_cache["token"]


def search_residential(suburb_state_postcode: str, property_types: list[str],
                        min_beds: int = 2, max_beds: int = 3,
                        listing_type: str = "Sale", page_size: int = 100) -> list[dict]:
    """
    One search call against /v1/listings/residential/_search for a single
    'Suburb-STATE-Postcode' locality string (matches Domain's search_areas.json format).
    Returns raw listing dicts as Domain returns them — filtering/scoring happens
    downstream in score.py so this stays a thin, reusable fetch layer.
    """
    parts = suburb_state_postcode.rsplit("-", 2)
    suburb, state, postcode = parts[0], parts[1], parts[2]

    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {
        "listingType": listing_type,
        "propertyTypes": property_types,
        "minBedrooms": min_beds,
        "maxBedrooms": max_beds,
        "locations": [{
            "state": state,
            "suburb": suburb.replace("-", " "),
            "postCode": postcode,
            "includeSurroundingSuburbs": False,
        }],
        "pageSize": page_size,
    }
    resp = requests.post(f"{API_BASE}/v1/listings/residential/_search",
                          json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_price_estimate(property_id: str) -> dict | None:
    """Domain's AVM estimate for a property — useful as one input among several,
    never the sole valuation (see build doc: portal AVMs have repeatedly missed
    recent sales and mis-scored configuration in manual testing this search)."""
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_BASE}/v1/properties/{property_id}",
                         headers=headers, timeout=20)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()
