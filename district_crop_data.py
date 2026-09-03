from __future__ import annotations

import re
from typing import Any

import pandas as pd
import streamlit as st


# Static mirror of the Government of India DES district-wise crop-production
# dataset schema. This is deliberately separate from the live mandi-price API:
# it is used only for historical district crop presence and yield benchmarks.
HISTORICAL_CROP_URL = (
    "https://raw.githubusercontent.com/dibyendubiswas1998/"
    "Crop-Production-Analysis/main/DATA/crop_production.csv"
)

OFFICIAL_SOURCE_TITLE = (
    "Government of India, Directorate of Economics & Statistics (DES) — "
    "District-wise, season-wise crop production statistics"
)
OFFICIAL_SOURCE_URL = (
    "https://www.data.gov.in/catalog/"
    "district-wise-season-wise-crop-production-statistics-0"
)

# FarmCredit crop names -> crop names used in the historical DES-style dataset.
CROP_ALIASES = {
    "Paddy (Common)": {
        "rice", "paddy", "paddy dhan", "paddy dhan common",
    },
    "Maize": {
        "maize",
    },
    "Tur / Arhar": {
        "arhar tur", "tur arhar", "arhar", "tur",
    },
    "Moong": {
        "moong green gram", "moong", "green gram",
    },
    "Urad": {
        "urad", "urd", "black gram",
    },
    "Wheat": {
        "wheat",
    },
    "Gram": {
        "gram", "bengal gram gram whole", "bengal gram",
    },
    "Lentil (Masur)": {
        "masoor", "masur", "lentil masur", "lentil",
    },
    "Rapeseed & Mustard": {
        "rapeseed mustard", "rapeseed and mustard", "mustard", "rapeseed",
    },
}

# Common administrative renamings. If the exact current district is not found,
# FarmCredit tries the historical name before falling back to state-level data.
DISTRICT_ALIASES = {
    ("Uttar Pradesh", "Prayagraj"): "Allahabad",
    ("Uttar Pradesh", "Ayodhya"): "Faizabad",
    ("Haryana", "Gurugram"): "Gurgaon",
    ("Haryana", "Nuh"): "Mewat",
    ("Karnataka", "Bengaluru Urban"): "Bangalore Urban",
    ("Karnataka", "Bengaluru Rural"): "Bangalore Rural",
    ("Maharashtra", "Chhatrapati Sambhajinagar"): "Aurangabad",
    ("Maharashtra", "Dharashiv"): "Osmanabad",
    ("Odisha", "Khordha"): "Khurda",
}

STATE_ALIASES = {
    "orissa": "odisha",
    "uttaranchal": "uttarakhand",
}


def _norm(value: Any) -> str:
    value = "" if value is None else str(value)
    value = value.lower().strip()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _canonical_state(value: Any) -> str:
    n = _norm(value)
    return STATE_ALIASES.get(n, n)


_CROP_ALIAS_LOOKUP = {}
for farmcredit_crop, aliases in CROP_ALIASES.items():
    for alias in aliases:
        _CROP_ALIAS_LOOKUP[_norm(alias)] = farmcredit_crop


def _map_crop(raw_crop: Any) -> str | None:
    n = _norm(raw_crop)

    if n in _CROP_ALIAS_LOOKUP:
        return _CROP_ALIAS_LOOKUP[n]

    # A few safe containment rules for punctuation/format differences.
    if n == "rice":
        return "Paddy (Common)"
    if "moong" in n or "green gram" in n:
        return "Moong"
    if n in {"urad", "urd"} or "black gram" in n:
        return "Urad"
    if "arhar" in n or n == "tur":
        return "Tur / Arhar"
    if "masoor" in n or "masur" in n or n == "lentil":
        return "Lentil (Masur)"
    if ("rapeseed" in n and "mustard" in n) or n == "mustard":
        return "Rapeseed & Mustard"
    if n == "gram":
        return "Gram"
    if n == "wheat":
        return "Wheat"
    if n == "maize":
        return "Maize"

    return None


@st.cache_data(ttl=86400, show_spinner=False)
def load_historical_crop_data() -> tuple[pd.DataFrame | None, str]:
    """
    Download once per day and keep only the fields/crops needed by FarmCredit.
    This dataset is historical, not a current crop forecast.
    """
    try:
        df = pd.read_csv(
            HISTORICAL_CROP_URL,
            usecols=[
                "State_Name",
                "District_Name",
                "Crop_Year",
                "Season",
                "Crop",
                "Area",
                "Production",
            ],
            low_memory=False,
        )

        df["farmcredit_crop"] = df["Crop"].map(_map_crop)
        df = df[df["farmcredit_crop"].notna()].copy()

        df["state_key"] = df["State_Name"].map(_canonical_state)
        df["district_key"] = df["District_Name"].map(_norm)

        df["Crop_Year"] = pd.to_numeric(df["Crop_Year"], errors="coerce")
        df["Area"] = pd.to_numeric(df["Area"], errors="coerce")
        df["Production"] = pd.to_numeric(df["Production"], errors="coerce")

        # Official DES catalog describes area in hectares and production in tonnes.
        # Invalid / zero-area rows cannot support a yield benchmark.
        df = df[
            df["Crop_Year"].notna()
            & df["Area"].notna()
            & df["Production"].notna()
            & (df["Area"] > 0)
            & (df["Production"] >= 0)
        ].copy()

        if df.empty:
            return None, "Historical crop dataset returned no usable records"

        return df, "DES historical district crop-production dataset (static mirror)"

    except Exception as exc:
        return None, f"Historical crop dataset unavailable ({type(exc).__name__})"


def _summarise(rows: pd.DataFrame, scope: str) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame()

    summaries = []

    for crop, grp in rows.groupby("farmcredit_crop"):
        grp = grp.sort_values("Crop_Year")
        latest_year = int(grp["Crop_Year"].max())

        # Use the five most recent distinct crop years available for this
        # district/crop to avoid letting very old observations dominate.
        recent_years = sorted(
            grp["Crop_Year"].dropna().astype(int).unique().tolist()
        )[-5:]
        recent = grp[grp["Crop_Year"].astype(int).isin(recent_years)].copy()

        total_area_ha = float(recent["Area"].sum())
        total_production_t = float(recent["Production"].sum())

        # DES catalog: Production tonnes / Area hectares.
        # kg/acre = (tonnes / ha * 1000 kg/t) / 2.47105 acres/ha.
        yield_kg_acre = None
        if total_area_ha > 0:
            yield_kg_acre = (
                (total_production_t / total_area_ha) * 1000.0 / 2.47105
            )

        # Guard against obviously unusable source records.
        if yield_kg_acre is not None and not (20 <= yield_kg_acre <= 10000):
            yield_kg_acre = None

        season_values = (
            recent["Season"]
            .dropna()
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
        )
        seasons = ", ".join(sorted(season_values.unique().tolist())[:4])

        summaries.append(
            {
                "Crop": crop,
                "Scope": scope,
                "Latest year": latest_year,
                "Recent years used": ", ".join(map(str, recent_years)),
                "Observations": int(len(recent)),
                "Recent area (ha)": total_area_ha,
                "Recent production (t)": total_production_t,
                "Historical yield kg/acre": yield_kg_acre,
                "Season evidence": seasons or "Not stated",
            }
        )

    result = pd.DataFrame(summaries)

    # Crops occupying more recorded area appear first in the dropdown.
    if not result.empty:
        result = result.sort_values(
            ["Recent area (ha)", "Latest year"],
            ascending=[False, False],
        ).reset_index(drop=True)

    return result


@st.cache_data(ttl=86400, show_spinner=False)
def get_crop_profile(
    state: str,
    district: str,
) -> dict[str, Any]:
    df, load_message = load_historical_crop_data()

    if df is None or df.empty:
        return {
            "ok": False,
            "scope": "generic",
            "message": load_message,
            "profile": pd.DataFrame(),
        }

    state_key = _canonical_state(state)
    district_key = _norm(district)

    state_rows = df[df["state_key"] == state_key].copy()

    if state_rows.empty:
        return {
            "ok": False,
            "scope": "generic",
            "message": f"No historical DES-style crop rows matched {state}.",
            "profile": pd.DataFrame(),
        }

    # First try exact current district name.
    district_rows = state_rows[
        state_rows["district_key"] == district_key
    ].copy()

    # Then try a known historical district name.
    alias = DISTRICT_ALIASES.get((state, district))
    alias_used = None
    if district_rows.empty and alias:
        alias_key = _norm(alias)
        district_rows = state_rows[
            state_rows["district_key"] == alias_key
        ].copy()
        if not district_rows.empty:
            alias_used = alias

    if not district_rows.empty:
        profile = _summarise(district_rows, "District")
        return {
            "ok": True,
            "scope": "district",
            "message": (
                f"Historical district crop evidence loaded for {district}"
                + (f" (matched historical name: {alias_used})" if alias_used else "")
                + "."
            ),
            "profile": profile,
        }

    # New/reorganised districts may not exist in older historical datasets.
    # Use state-level evidence rather than inventing a district value.
    profile = _summarise(state_rows, "State fallback")

    return {
        "ok": True,
        "scope": "state",
        "message": (
            f"No exact historical district series matched {district}. "
            f"FarmCredit is using {state}-level crop evidence as the fallback."
        ),
        "profile": profile,
    }


def profile_crop_options(profile_result: dict[str, Any]) -> list[str]:
    profile = profile_result.get("profile")
    if profile is None or profile.empty:
        return []

    return [
        str(x)
        for x in profile["Crop"].tolist()
        if str(x).strip()
    ]


def crop_benchmark(
    profile_result: dict[str, Any],
    crop: str,
) -> dict[str, Any] | None:
    profile = profile_result.get("profile")
    if profile is None or profile.empty:
        return None

    matched = profile[profile["Crop"] == crop]
    if matched.empty:
        return None

    row = matched.iloc[0]
    value = row.get("Historical yield kg/acre")

    return {
        "scope": profile_result.get("scope", "generic"),
        "yield_kg_acre": (
            float(value)
            if pd.notna(value)
            else None
        ),
        "latest_year": int(row["Latest year"]),
        "recent_years_used": str(row["Recent years used"]),
        "observations": int(row["Observations"]),
        "recent_area_ha": float(row["Recent area (ha)"]),
        "season_evidence": str(row["Season evidence"]),
        "message": profile_result.get("message", ""),
    }
