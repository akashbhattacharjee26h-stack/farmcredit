from __future__ import annotations

from datetime import datetime
import re
from typing import Any

import pandas as pd
import requests


MANDI_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
MANDI_ENDPOINT = f"https://api.data.gov.in/resource/{MANDI_RESOURCE_ID}"

# Public, LGD-derived district index used only to populate dropdowns.
DISTRICT_INDEX_URL = (
    "https://raw.githubusercontent.com/bilal-webdev/"
    "india-postal-pincode-dataset/main/json/india-district-index.json"
)

# Fallback allows the app to remain usable if the location-index download fails.
FALLBACK_DISTRICTS = {
    "Jharkhand": ["Bokaro", "Dhanbad", "East Singhbhum", "Hazaribagh", "Ramgarh", "Ranchi"],
    "West Bengal": ["Bankura", "Birbhum", "Burdwan", "Hooghly", "Howrah", "Jalpaiguri",
                    "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas",
                    "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman",
                    "Purba Medinipur", "South 24 Parganas"],
    "Bihar": ["Bhojpur", "Buxar", "Gaya", "Muzaffarpur", "Patna", "Rohtas"],
    "Uttar Pradesh": ["Agra", "Ballia", "Bareilly", "Gorakhpur", "Kanpur Nagar", "Lucknow",
                      "Prayagraj", "Saharanpur", "Varanasi"],
    "Punjab": ["Amritsar", "Bathinda", "Jalandhar", "Ludhiana", "Patiala"],
    "Haryana": ["Ambala", "Hisar", "Karnal", "Panipat", "Rohtak"],
    "Maharashtra": ["Ahmednagar", "Mumbai", "Nagpur", "Nashik", "Pune"],
    "Madhya Pradesh": ["Bhopal", "Gwalior", "Indore", "Jabalpur", "Ujjain"],
    "Rajasthan": ["Ajmer", "Jaipur", "Jodhpur", "Kota", "Udaipur"],
}

STATE_CANONICAL = {
    "ANDAMAN AND NICOBAR ISLANDS": "Andaman and Nicobar Islands",
    "ANDHRA PRADESH": "Andhra Pradesh",
    "ARUNACHAL PRADESH": "Arunachal Pradesh",
    "ASSAM": "Assam",
    "BIHAR": "Bihar",
    "CHANDIGARH": "Chandigarh",
    "CHHATTISGARH": "Chhattisgarh",
    "DADRA AND NAGAR HAVELI AND DAMAN AND DIU": "Dadra and Nagar Haveli and Daman and Diu",
    "DELHI": "Delhi",
    "GOA": "Goa",
    "GUJARAT": "Gujarat",
    "HARYANA": "Haryana",
    "HIMACHAL PRADESH": "Himachal Pradesh",
    "JAMMU AND KASHMIR": "Jammu and Kashmir",
    "JHARKHAND": "Jharkhand",
    "KARNATAKA": "Karnataka",
    "KERALA": "Kerala",
    "LADAKH": "Ladakh",
    "LAKSHADWEEP": "Lakshadweep",
    "MADHYA PRADESH": "Madhya Pradesh",
    "MAHARASHTRA": "Maharashtra",
    "MANIPUR": "Manipur",
    "MEGHALAYA": "Meghalaya",
    "MIZORAM": "Mizoram",
    "NAGALAND": "Nagaland",
    "ODISHA": "Odisha",
    "PUDUCHERRY": "Puducherry",
    "PUNJAB": "Punjab",
    "RAJASTHAN": "Rajasthan",
    "SIKKIM": "Sikkim",
    "TAMIL NADU": "Tamil Nadu",
    "TELANGANA": "Telangana",
    "TRIPURA": "Tripura",
    "UTTAR PRADESH": "Uttar Pradesh",
    "UTTARAKHAND": "Uttarakhand",
    "WEST BENGAL": "West Bengal",
}

CROP_ALIASES = {
    "Paddy (Common)": ["paddy", "dhan"],
    "Maize": ["maize"],
    "Tur / Arhar": ["arhar", "tur", "red gram"],
    "Moong": ["moong", "green gram"],
    "Urad": ["urad", "urd", "black gram"],
    "Wheat": ["wheat"],
    "Gram": ["bengal gram", "gram"],
    "Lentil (Masur)": ["lentil", "masur"],
    "Rapeseed & Mustard": ["mustard", "rapeseed"],
}


def _pretty_name(s: str) -> str:
    # Preserve abbreviations reasonably while avoiding all-caps UI.
    return " ".join(w if len(w) <= 3 and "." in w else w.title() for w in s.split())


def fetch_state_district_map() -> tuple[dict[str, list[str]], str]:
    """
    Returns state -> districts and a source-status string.
    """
    try:
        r = requests.get(DISTRICT_INDEX_URL, timeout=10)
        r.raise_for_status()
        payload = r.json()
        states_raw = payload.get("states", {})
        out: dict[str, list[str]] = {}
        for raw_state, districts in states_raw.items():
            state = STATE_CANONICAL.get(raw_state.upper(), _pretty_name(raw_state))
            names = []
            for raw_district in districts.keys():
                names.append(_pretty_name(raw_district))
            out[state] = sorted(set(names))
        if out:
            return dict(sorted(out.items())), "LGD-derived district index"
    except Exception:
        pass

    # Make fallback state list broader even where district coverage is limited.
    all_states = sorted(STATE_CANONICAL.values())
    out = {s: FALLBACK_DISTRICTS.get(s, ["Other / not listed"]) for s in all_states}
    return out, "Fallback location list"


def _norm(s: Any) -> str:
    s = "" if s is None else str(s)
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _matches_crop(commodity: str, crop: str) -> bool:
    text = _norm(commodity)
    aliases = CROP_ALIASES.get(crop, [_norm(crop)])
    return any(_norm(alias) in text for alias in aliases)


def fetch_mandi_records(
    api_key: str,
    state: str,
    district: str,
    crop: str,
    limit: int = 1000,
) -> dict[str, Any]:
    """
    Fetch recent AGMARKNET/data.gov.in records for a state + district and
    filter locally to the selected accounting crop.
    """
    if not api_key:
        return {"ok": False, "message": "Add your data.gov.in API key to fetch live market data.", "records": []}

    params = {
        "api-key": api_key.strip(),
        "format": "json",
        "offset": 0,
        "limit": limit,
        "filters[state.keyword]": state,
        "filters[district]": district,
    }

    try:
        resp = requests.get(MANDI_ENDPOINT, params=params, timeout=18)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        return {
            "ok": False,
            "message": f"Market data request failed: {type(e).__name__}.",
            "records": [],
        }

    raw = payload.get("records", []) or []
    matches = [r for r in raw if _matches_crop(r.get("commodity", ""), crop)]

    if not matches:
        return {
            "ok": False,
            "message": (
                f"No matching {crop} records were returned for {district}, {state}. "
                "Try another district or keep using MSP / manual expected price."
            ),
            "records": [],
        }

    df = pd.DataFrame(matches)
    for col in ["min_price", "max_price", "modal_price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "arrival_date" in df.columns:
        df["_date"] = pd.to_datetime(df["arrival_date"], errors="coerce", dayfirst=True)
        df = df.sort_values("_date", ascending=False, na_position="last")

    df = df.dropna(subset=["modal_price"]) if "modal_price" in df.columns else df

    if df.empty:
        return {"ok": False, "message": "Records were returned, but no usable modal prices were found.", "records": []}

    latest = df.iloc[0].to_dict()

    # Compact history: recent latest observations, sorted oldest -> newest for charts.
    history = df.head(30).copy()
    if "_date" in history.columns:
        history = history.sort_values("_date")
    history_records = history.to_dict(orient="records")

    return {
        "ok": True,
        "message": "Recent mandi observations loaded.",
        "latest": latest,
        "history": history_records,
        "record_count": int(len(df)),
    }
