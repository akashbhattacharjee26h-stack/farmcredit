from __future__ import annotations

from typing import Any
import pandas as pd
import requests

RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
ENDPOINT = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

# First-choice AGMARKNET commodity names. We intentionally keep the live call light:
# one small request, short timeout, and no large fallback downloads.
CROP_TERMS = {
    "Paddy (Common)": "Paddy(Dhan)(Common)",
    "Maize": "Maize",
    "Tur / Arhar": "Arhar (Tur/Red Gram)(Whole)",
    "Moong": "Green Gram (Moong)(Whole)",
    "Urad": "Black Gram (Urd Beans)(Whole)",
    "Wheat": "Wheat",
    "Gram": "Bengal Gram(Gram)(Whole)",
    "Lentil (Masur)": "Lentil (Masur)(Whole)",
    "Rapeseed & Mustard": "Mustard",
}


def fetch_live_mandi_price(api_key: str, state: str, district: str, crop: str) -> dict[str, Any]:
    """
    Optional live fetch for the UI.
    Designed to fail fast so the main FarmCredit workflow never becomes slow.
    """
    api_key = (api_key or "").strip()
    if not api_key:
        return {
            "ok": False,
            "kind": "missing_key",
            "message": "Enter your data.gov.in API key before fetching live mandi data.",
        }

    commodity = CROP_TERMS.get(crop, crop)

    params = {
        "api-key": api_key,
        "format": "json",
        "offset": 0,
        "limit": 20,
        "filters[state.keyword]": state,
        "filters[district]": district,
        "filters[commodity]": commodity,
    }

    try:
        response = requests.get(
            ENDPOINT,
            params=params,
            timeout=(4, 8),  # fail fast; user can continue manually
        )
        response.raise_for_status()
        payload = response.json()
        records = payload.get("records", []) or []

        if not records:
            return {
                "ok": False,
                "kind": "no_records",
                "message": (
                    f"No recent live {crop} mandi record was returned for "
                    f"{district}, {state}. You can continue using the manual/MSP price."
                ),
            }

        df = pd.DataFrame(records)

        for col in ["min_price", "max_price", "modal_price"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "arrival_date" in df.columns:
            df["_date"] = pd.to_datetime(
                df["arrival_date"],
                errors="coerce",
                dayfirst=True,
            )
            df = df.sort_values("_date", ascending=False, na_position="last")

        if "modal_price" not in df.columns:
            return {
                "ok": False,
                "kind": "schema",
                "message": "Live records were returned, but modal price was unavailable.",
            }

        df = df.dropna(subset=["modal_price"])
        if df.empty:
            return {
                "ok": False,
                "kind": "price_missing",
                "message": "Live records were returned, but no usable modal price was found.",
            }

        latest = df.iloc[0].to_dict()

        return {
            "ok": True,
            "kind": "success",
            "latest": latest,
            "count": int(len(df)),
            "message": "Live mandi price fetched successfully.",
        }

    except requests.exceptions.Timeout:
        return {
            "ok": False,
            "kind": "timeout",
            "message": (
                "The Government market-data API did not respond within 8 seconds. "
                "FarmCredit stopped the request so the page stays fast. "
                "You can continue using the manual/MSP price."
            ),
        }
    except requests.exceptions.HTTPError as exc:
        status = getattr(exc.response, "status_code", None)
        if status in (401, 403):
            msg = (
                "The API rejected the request. Please re-check the data.gov.in API key."
            )
        else:
            msg = (
                f"The live market-data request returned HTTP {status or 'error'}. "
                "You can continue using the manual/MSP price."
            )
        return {"ok": False, "kind": "http_error", "message": msg}
    except Exception as exc:
        return {
            "ok": False,
            "kind": "error",
            "message": (
                f"Live market data could not be loaded ({type(exc).__name__}). "
                "You can continue using the manual/MSP price."
            ),
        }
