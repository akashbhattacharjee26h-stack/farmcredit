from __future__ import annotations

from typing import Any

import requests
import streamlit as st


# Fast, public district index used for the web UI.
# The app explicitly labels LGD as the authoritative formal reference.
DISTRICT_INDEX_URL = (
    "https://raw.githubusercontent.com/bilal-webdev/"
    "india-postal-pincode-dataset/main/json/india-district-index.json"
)

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


def _pretty(value: Any) -> str:
    s = str(value or "").strip()
    return " ".join(part.capitalize() for part in s.split())


@st.cache_data(ttl=86400, show_spinner=False)
def load_online_location_master() -> tuple[dict[str, list[str]] | None, str]:
    """
    Fetch once and cache for 24h. This avoids maintaining a tiny hardcoded
    district list and makes the dropdown much more complete.
    """
    try:
        r = requests.get(DISTRICT_INDEX_URL, timeout=(3, 5))
        r.raise_for_status()
        payload = r.json()
        states_raw = payload.get("states", {})

        location_map: dict[str, list[str]] = {}

        for raw_state, raw_districts in states_raw.items():
            state = STATE_CANONICAL.get(
                str(raw_state).upper(),
                _pretty(raw_state),
            )

            if isinstance(raw_districts, dict):
                district_names = list(raw_districts.keys())
            elif isinstance(raw_districts, list):
                district_names = raw_districts
            else:
                continue

            districts = sorted(
                {
                    _pretty(d)
                    for d in district_names
                    if str(d).strip()
                }
            )

            if districts:
                location_map[state] = districts + ["Other / Not listed"]

        if location_map:
            return dict(sorted(location_map.items())), "Online district master"

    except Exception:
        pass

    return None, "Built-in fallback list"
