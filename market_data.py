from __future__ import annotations

import re
from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


MANDI_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
MANDI_ENDPOINT = f"https://api.data.gov.in/resource/{MANDI_RESOURCE_ID}"

DISTRICT_INDEX_URL = (
    "https://raw.githubusercontent.com/bilal-webdev/"
    "india-postal-pincode-dataset/main/json/india-district-index.json"
)

FALLBACK_DISTRICTS = {
    "Jharkhand": ["Bokaro", "Dhanbad", "East Singhbhum", "Hazaribagh", "Ramgarh", "Ranchi"],
    "West Bengal": ["Alipurduar", "Bankura", "Birbhum", "Darjeeling", "Hooghly", "Howrah",
                    "Jalpaiguri", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas",
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

CROP_API_TERMS = {
    "Paddy (Common)": ["Paddy(Dhan)(Common)", "Paddy(Dhan)", "Paddy", "Dhan"],
    "Maize": ["Maize"],
    "Tur / Arhar": ["Arhar (Tur/Red Gram)(Whole)", "Arhar (Tur)", "Tur", "Arhar"],
    "Moong": ["Green Gram (Moong)(Whole)", "Moong", "Green Gram"],
    "Urad": ["Black Gram (Urd Beans)(Whole)", "Urad", "Urd", "Black Gram"],
    "Wheat": ["Wheat"],
    "Gram": ["Bengal Gram(Gram)(Whole)", "Gram", "Bengal Gram"],
    "Lentil (Masur)": ["Lentil (Masur)(Whole)", "Lentil", "Masur"],
    "Rapeseed & Mustard": ["Mustard", "Rapeseed & Mustard", "Rapeseed"],
}


def _pretty_name(s: str) -> str:
    return " ".join(w if len(w) <= 3 and "." in w else w.title() for w in s.split())


def fetch_state_district_map() -> tuple[dict[str, list[str]], str]:
    try:
        r = requests.get(DISTRICT_INDEX_URL, timeout=(5, 15))
        r.raise_for_status()
        payload = r.json()
        states_raw = payload.get("states", {})
        out: dict[str, list[str]] = {}
        for raw_state, districts in states_raw.items():
            state = STATE_CANONICAL.get(raw_state.upper(), _pretty_name(raw_state))
            names = [_pretty_name(d) for d in districts.keys()]
            out[state] = sorted(set(names))
        if out:
            return dict(sorted(out.items())), "LGD-derived district index"
    except Exception:
        pass

    all_states = sorted(STATE_CANONICAL.values())
    out = {s: FALLBACK_DISTRICTS.get(s, ["Other / not listed"]) for s in all_states}
    return out, "Fallback location list"


def _norm(s: Any) -> str:
    s = "" if s is None else str(s)
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _local_crop_match(commodity: str, crop: str) -> bool:
    c = _norm(commodity)
    terms = [_norm(x) for x in CROP_API_TERMS.get(crop, [crop])]
    return any(t and (t in c or c in t) for t in terms)


def _session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=0.7,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def _request_once(session: requests.Session, params: dict[str, Any]) -> dict[str, Any]:
    resp = session.get(MANDI_ENDPOINT, params=params, timeout=(6, 28))
    resp.raise_for_status()
    return resp.json()


def fetch_mandi_records(api_key: str, state: str, district: str, crop: str, limit: int = 50) -> dict[str, Any]:
    if not api_key:
        return {"ok": False, "kind": "missing_key",
                "message": "Add your data.gov.in API key to fetch recent mandi data.", "records": []}

    session = _session()
    base = {
        "api-key": api_key.strip(),
        "format": "json",
        "offset": 0,
        "limit": limit,
        "filters[state.keyword]": state,
        "filters[district]": district,
    }

    timed_out = False
    last_error = None

    for term in CROP_API_TERMS.get(crop, [crop]):
        params = dict(base)
        params["filters[commodity]"] = term
        try:
            payload = _request_once(session, params)
            raw = payload.get("records", []) or []
            if raw:
                return _shape_result(raw, exact_term=term)
        except requests.exceptions.Timeout:
            timed_out = True
        except Exception as e:
            last_error = type(e).__name__

    fallback_params = dict(base)
    fallback_params["limit"] = 120
    try:
        payload = _request_once(session, fallback_params)
        raw = payload.get("records", []) or []
        matches = [r for r in raw if _local_crop_match(r.get("commodity", ""), crop)]
        if matches:
            return _shape_result(matches, exact_term=None)
        if raw:
            examples = sorted({str(r.get("commodity", "")).strip() for r in raw if r.get("commodity")})[:8]
            return {
                "ok": False, "kind": "no_crop_match",
                "message": (
                    f"No recent {crop} observation matched for {district}, {state}. "
                    + (f"Commodities returned for this district include: {', '.join(examples)}." if examples else "")
                ),
                "records": [],
            }
        return {"ok": False, "kind": "no_records",
                "message": f"No recent mandi records were returned for {district}, {state}.", "records": []}
    except requests.exceptions.Timeout:
        timed_out = True
    except Exception as e:
        last_error = type(e).__name__

    if timed_out:
        return {
            "ok": False, "kind": "timeout",
            "message": (
                "The government mandi API is responding slowly and timed out after retries. "
                "Your API key may still be valid. Try again in a minute or choose another district/crop."
            ),
            "records": [],
        }

    return {"ok": False, "kind": "request_error",
            "message": f"Market data request failed ({last_error or 'unknown error'}).", "records": []}


def _shape_result(raw: list[dict[str, Any]], exact_term: str | None) -> dict[str, Any]:
    df = pd.DataFrame(raw)
    for col in ["min_price", "max_price", "modal_price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "arrival_date" in df.columns:
        df["_date"] = pd.to_datetime(df["arrival_date"], errors="coerce", dayfirst=True)
        df = df.sort_values("_date", ascending=False, na_position="last")

    if "modal_price" not in df.columns:
        return {"ok": False, "kind": "bad_schema",
                "message": "Records were returned, but no modal-price field was available.", "records": []}

    df = df.dropna(subset=["modal_price"])
    if df.empty:
        return {"ok": False, "kind": "bad_prices",
                "message": "Records were returned, but no usable modal prices were found.", "records": []}

    latest = df.iloc[0].to_dict()
    history = df.head(30).copy()
    if "_date" in history.columns:
        history = history.sort_values("_date")

    return {
        "ok": True, "kind": "success",
        "message": "Recent mandi observations loaded.",
        "latest": latest,
        "history": history.to_dict(orient="records"),
        "record_count": int(len(df)),
        "query_term": exact_term,
    }
