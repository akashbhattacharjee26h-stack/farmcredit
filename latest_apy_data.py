from __future__ import annotations

from io import StringIO
import re
from typing import Any

import pandas as pd
import requests
import streamlit as st


# Official DES pages / reports
DES_FORM_URL = "https://data.desagri.gov.in/website/crops-report-major-contributing-district-web"
DES_DISTRICT_REPORT_URL = "https://data.desagri.gov.in/report/crop/crops-printdraft-major-contributing-district"
DES_STATE_REPORT_URL = "https://data.desagri.gov.in/report/crop/crops-printdraft-major-contributing-state"

OFFICIAL_DES_APY_URL = "https://data.desagri.gov.in/website/apy-query-report-web"
OFFICIAL_ASAG_URL = "https://desagri.gov.in/document-report/agricultural-statistics-at-a-glance-2024/"

# 2024-25 All-India yield, kg/hectare, from Agricultural Statistics at a Glance 2024-25,
# Table 2.27 (3rd Advance Estimates where marked by DES).
# These are only a freshness fallback if current district/state DES APY cannot be read.
ALL_INDIA_2024_25_YIELD_KG_HA = {
    "Paddy (Common)": 2899.0,        # Rice, total
    "Wheat": 3587.0,
    "Maize": 3518.0,                # Maize, total
    "Tur / Arhar": 823.0,
    "Gram": 1180.0,
    "Urad": 697.0,                  # Urad, total
    "Moong": 685.0,                 # Moong, total
    "Lentil (Masur)": 1038.0,
    "Rapeseed & Mustard": 1461.0,
}

# Candidate DES form labels. IDs are discovered from the official form at runtime,
# so the code does not freeze hard-coded state/crop database IDs.
DES_CROP_LABELS = {
    "Paddy (Common)": ["Rice", "Paddy"],
    "Wheat": ["Wheat"],
    "Maize": ["Maize"],
    "Tur / Arhar": ["Arhar/Tur", "Tur (Arhar)", "Arhar", "Tur"],
    "Gram": ["Gram"],
    "Urad": ["Urad"],
    "Moong": ["Moong(Green Gram)", "Moong", "Green Gram"],
    "Lentil (Masur)": ["Masoor", "Masur", "Lentil (Masur)", "Lentil"],
    "Rapeseed & Mustard": ["Rapeseed &Mustard", "Rapeseed & Mustard", "Mustard"],
}

STATE_NAME_ALIASES = {
    "odisha": ["Odisha", "Orissa"],
    "uttarakhand": ["Uttarakhand", "Uttaranchal"],
    "jammu and kashmir": ["Jammu & Kashmir", "Jammu and Kashmir"],
    "andaman and nicobar islands": ["Andaman & Nicobar Islands", "Andaman and Nicobar Islands"],
}


def _norm(v: Any) -> str:
    s = "" if v is None else str(v)
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _to_num(v: Any) -> float | None:
    if v is None:
        return None
    s = str(v).strip().replace(",", "")
    if not s or s.lower() in {"na", "nan", "-", "none"}:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


@st.cache_resource
def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 FarmCredit/2.6",
        "Accept": "text/html,application/xhtml+xml",
    })
    return s


def _match_option_value(html_text: str, candidate_labels: list[str]) -> str | None:
    """
    Match an <option value="...">Label</option> anywhere in the DES form.
    We discover IDs dynamically because internal numeric IDs can change.
    """
    options = re.findall(
        r'<option[^>]*value=["\']([^"\']*)["\'][^>]*>(.*?)</option>',
        html_text,
        flags=re.I | re.S,
    )
    normalized_candidates = {_norm(x) for x in candidate_labels}

    # exact match first
    for value, label_html in options:
        label = re.sub(r"<[^>]+>", " ", label_html)
        if _norm(label) in normalized_candidates and str(value).strip():
            return str(value).strip()

    # cautious containment fallback
    for value, label_html in options:
        label = _norm(re.sub(r"<[^>]+>", " ", label_html))
        if not value or not label:
            continue
        for cand in normalized_candidates:
            if cand and (label == cand or label.startswith(cand) or cand.startswith(label)):
                return str(value).strip()

    return None


def _extract_year_options(html_text: str) -> list[int]:
    years = sorted({
        int(y)
        for y in re.findall(r'>\s*(20\d{2})(?:\s*-\s*\d{2,4})?\s*<', html_text)
        if 2000 <= int(y) <= 2030
    })
    return years


@st.cache_data(ttl=21600, show_spinner=False)
def _load_des_lookup() -> dict[str, Any]:
    try:
        r = _session().get(DES_FORM_URL, timeout=(4, 8))
        r.raise_for_status()
        years = _extract_year_options(r.text)
        return {
            "ok": True,
            "html": r.text,
            "years": years,
            "message": "Official DES lookup loaded.",
        }
    except Exception as exc:
        return {
            "ok": False,
            "html": "",
            "years": [],
            "message": f"DES lookup unavailable ({type(exc).__name__}).",
        }


def _flatten_cols(df: pd.DataFrame) -> list[str]:
    cols = []
    for c in df.columns:
        if isinstance(c, tuple):
            text = " ".join(str(x) for x in c if str(x) != "nan")
        else:
            text = str(c)
        cols.append(re.sub(r"\s+", " ", text).strip())
    return cols


def _find_target_row(table: pd.DataFrame, target: str) -> tuple[pd.Series | None, list[str]]:
    df = table.copy()
    flat = _flatten_cols(df)
    df.columns = flat
    target_n = _norm(target)

    for _, row in df.iterrows():
        row_text = " ".join(str(x) for x in row.tolist())
        if target_n and target_n in _norm(row_text):
            return row, flat
    return None, flat


def _year_from_col(col: str) -> int | None:
    yrs = re.findall(r"(20\d{2})", str(col))
    if not yrs:
        return None
    return max(int(y) for y in yrs)


def _parse_yield_from_html(html_text: str, target_name: str) -> dict[str, Any] | None:
    """
    DES report tables may have multi-level columns.
    Prefer columns explicitly containing 'Yield'. If unavailable, use a conservative
    row scan only when the report text itself says Yield.
    """
    try:
        tables = pd.read_html(StringIO(html_text))
    except Exception:
        return None

    best = None

    for table in tables:
        row, cols = _find_target_row(table, target_name)
        if row is None:
            continue

        candidates = []

        for col in cols:
            if "yield" not in _norm(col):
                continue
            value = _to_num(row.get(col))
            if value is None:
                continue
            year = _year_from_col(col)
            candidates.append((year or 0, value, col))

        if candidates:
            candidates.sort(key=lambda x: x[0])
            year, value, col = candidates[-1]
            if 50 <= value <= 15000:
                item = {
                    "year_start": year if year else None,
                    "yield_kg_ha": value,
                    "column": col,
                }
                if best is None or (item["year_start"] or 0) > (best["year_start"] or 0):
                    best = item

    if best:
        return best

    return None


def _state_candidates(state: str) -> list[str]:
    base = [state]
    base += STATE_NAME_ALIASES.get(_norm(state), [])
    return list(dict.fromkeys(base))


def _discover_ids(state: str, crop: str) -> dict[str, Any]:
    lookup = _load_des_lookup()
    if not lookup["ok"]:
        return {"ok": False, "message": lookup["message"]}

    html_text = lookup["html"]
    state_value = _match_option_value(html_text, _state_candidates(state))
    crop_value = _match_option_value(html_text, DES_CROP_LABELS.get(crop, [crop]))

    if not state_value or not crop_value:
        return {
            "ok": False,
            "message": (
                "The current DES form loaded, but FarmCredit could not resolve "
                f"the internal ID for {state if not state_value else crop}."
            ),
        }

    years = lookup.get("years") or []
    if years:
        end_year = max(years)
        start_year = max(min(years), end_year - 4)
    else:
        # Current DES public reports are known to contain at least recent 2022-23 series;
        # use a wider window and let the report parser select the newest populated year.
        start_year, end_year = 2021, 2025

    return {
        "ok": True,
        "state_value": state_value,
        "crop_value": crop_value,
        "start_year": start_year,
        "end_year": end_year,
    }


def _request_report(url: str, params: dict[str, Any]) -> str | None:
    try:
        r = _session().get(url, params=params, timeout=(4, 10))
        r.raise_for_status()
        if len(r.text) < 200:
            return None
        return r.text
    except Exception:
        return None


@st.cache_data(ttl=21600, show_spinner=False)
def _current_district_apy(state: str, district: str, crop: str) -> dict[str, Any] | None:
    ids = _discover_ids(state, crop)
    if not ids.get("ok"):
        return None

    # Try the value exactly as the official form exposes it, then without a leading comma
    # because DES report endpoints have used both forms historically.
    state_variants = [ids["state_value"]]
    stripped = str(ids["state_value"]).lstrip(",")
    if stripped not in state_variants:
        state_variants.append(stripped)

    for state_value in state_variants:
        params = {
            "fltrstates": state_value,
            "fltrcrops": ids["crop_value"],
            "fltrfromyear": ids["start_year"],
            "fltrtoyear": ids["end_year"],
            "fltrcontribut": "yield",
            "fltrtopdistrict": "all",
            "number_district": "",
        }
        html_text = _request_report(DES_DISTRICT_REPORT_URL, params)
        if not html_text:
            continue

        parsed = _parse_yield_from_html(html_text, district)
        if parsed:
            return {
                "scope": "district",
                "source": "Current DES APY portal",
                "year_start": parsed.get("year_start"),
                "yield_kg_ha": parsed["yield_kg_ha"],
            }

    return None


@st.cache_data(ttl=21600, show_spinner=False)
def _current_state_apy(state: str, crop: str) -> dict[str, Any] | None:
    ids = _discover_ids(state, crop)
    if not ids.get("ok"):
        return None

    params = {
        "fltrcontribut": "yield",
        "fltrcrops": ids["crop_value"],
        "fltrfromyear": ids["start_year"],
        "fltrtoyear": ids["end_year"],
        "fltrtopstate": "all",
        "number_state": "",
    }
    html_text = _request_report(DES_STATE_REPORT_URL, params)
    if not html_text:
        return None

    parsed = _parse_yield_from_html(html_text, state)
    if parsed:
        return {
            "scope": "state",
            "source": "Current DES APY portal",
            "year_start": parsed.get("year_start"),
            "yield_kg_ha": parsed["yield_kg_ha"],
        }

    return None


def _year_label(year_start: int | None, fallback: str) -> str:
    if year_start:
        return f"{year_start}-{str(year_start + 1)[-2:]}"
    return fallback


@st.cache_data(ttl=21600, show_spinner=False)
def get_latest_apy_benchmark(
    state: str,
    district: str,
    crop: str,
) -> dict[str, Any]:
    """
    Accuracy hierarchy:
    1) Current official DES district APY report (newest year exposed by DES form)
    2) Current official DES state APY report
    3) Official 2024-25 All-India yield (3rd Advance Estimates)
    The old historical district mirror is handled separately by FarmCredit and is
    only used if these newer layers do not provide a district/state value.
    """

    district_result = _current_district_apy(state, district, crop)
    if district_result:
        kg_ha = float(district_result["yield_kg_ha"])
        return {
            "ok": True,
            "scope": "district",
            "freshness_rank": 1,
            "year": _year_label(district_result.get("year_start"), "Latest DES"),
            "yield_kg_ha": kg_ha,
            "yield_kg_acre": kg_ha / 2.47105,
            "source": district_result["source"],
            "source_url": OFFICIAL_DES_APY_URL,
            "note": "Newest district-level APY value that FarmCredit could read from the current DES portal.",
        }

    state_result = _current_state_apy(state, crop)
    if state_result:
        kg_ha = float(state_result["yield_kg_ha"])
        return {
            "ok": True,
            "scope": "state",
            "freshness_rank": 2,
            "year": _year_label(state_result.get("year_start"), "Latest DES"),
            "yield_kg_ha": kg_ha,
            "yield_kg_acre": kg_ha / 2.47105,
            "source": state_result["source"],
            "source_url": OFFICIAL_DES_APY_URL,
            "note": "District-level current APY was unavailable; using the newest state-level DES APY value.",
        }

    national = ALL_INDIA_2024_25_YIELD_KG_HA.get(crop)
    if national:
        return {
            "ok": True,
            "scope": "all_india",
            "freshness_rank": 3,
            "year": "2024-25",
            "yield_kg_ha": float(national),
            "yield_kg_acre": float(national) / 2.47105,
            "source": "Agricultural Statistics at a Glance 2024-25",
            "source_url": OFFICIAL_ASAG_URL,
            "note": (
                "Current district/state APY could not be read. "
                "Using the official 2024-25 All-India yield as a freshness fallback."
            ),
        }

    return {
        "ok": False,
        "scope": "none",
        "message": "No newer official APY benchmark could be resolved.",
    }
