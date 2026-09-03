from pathlib import Path
from datetime import date
import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from calculations import calculate_case, run_scenarios, resilience_label
from market_data import fetch_live_mandi_price
from location_data import load_online_location_master
from district_crop_data import (
    OFFICIAL_SOURCE_TITLE,
    OFFICIAL_SOURCE_URL,
    get_crop_profile,
    profile_crop_options,
    crop_benchmark,
)


st.set_page_config(
    page_title="FarmCredit",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE = Path(__file__).parent
benchmarks = pd.read_csv(
    BASE / "data" / "crop_benchmarks.csv",
    encoding="utf-8-sig",
).set_index("crop")


# -------------------------------------------------------------------
# STYLE
# -------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root{
      --green:#173F35; --green2:#2E6857; --cream:#F7F4EC;
      --paper:#FFFEFA; --ink:#16231F; --muted:#68766F;
      --gold:#C49A52; --line:#E4DED1; --soft:#EEF4F0;
    }

    .stApp{background:#F7F4EC;color:#16231F}
    .block-container{max-width:1280px;padding-top:1.1rem;padding-bottom:3rem}
    #MainMenu,footer{visibility:hidden}
    header[data-testid="stHeader"]{background:transparent}
    h1,h2,h3{color:#173F35!important}

    .brandbar{
      display:flex;justify-content:space-between;align-items:center;
      margin-bottom:.8rem
    }
    .brand{
      font-size:1.25rem;font-weight:800;color:#173F35
    }
    .badge{
      padding:.36rem .72rem;border-radius:999px;background:#fff;
      border:1px solid #DED8CA;font-size:.75rem;font-weight:700;color:#173F35
    }
    .hero{
      background:linear-gradient(120deg,#173F35,#2E6857);
      color:#fff;padding:2rem 2.2rem;border-radius:26px;margin-bottom:1.1rem
    }
    .hero h1{
      color:#fff!important;margin:0;font-size:2.15rem
    }
    .hero p{
      color:rgba(255,255,255,.86);max-width:900px;line-height:1.6;
      margin:.65rem 0 0
    }

    .sectionlabel{
      font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;
      font-weight:800;color:#2E6857;margin:1rem 0 .5rem
    }

    div[data-testid="stVerticalBlockBorderWrapper"]{
      background:#FFFEFA!important;border:1px solid #E4DED1!important;
      border-radius:18px!important
    }

    /* Make ALL labels readable */
    div[data-testid="stWidgetLabel"] p,
    label[data-testid="stWidgetLabel"] p,
    .stNumberInput label p,
    .stTextInput label p,
    .stSelectbox label p{
      color:#243A32!important;font-weight:750!important;font-size:.86rem!important
    }

    /* Light controls */
    div[data-testid="stSelectbox"] div[role="combobox"],
    div[data-baseweb="select"]>div{
      background:#FFF!important;color:#16231F!important;
      border:1px solid #DAD3C5!important
    }
    div[data-testid="stSelectbox"] div[role="combobox"] *,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] input{
      color:#16231F!important;-webkit-text-fill-color:#16231F!important;
      fill:#173F35!important
    }
    div[role="listbox"],div[data-baseweb="popover"] ul{background:#fff!important}
    div[role="option"],div[data-baseweb="popover"] li{
      background:#fff!important;color:#16231F!important
    }
    div[role="option"]:hover,div[data-baseweb="popover"] li:hover{
      background:#EEF4F0!important
    }
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextInput"] input{
      background:#fff!important;color:#16231F!important;
      -webkit-text-fill-color:#16231F!important
    }

    .inputhelp{
      background:#F2F6F3;border:1px solid #DAE7DF;border-radius:14px;
      padding:.85rem 1rem;color:#51645D;font-size:.81rem;line-height:1.55;
      margin:.35rem 0 .6rem
    }
    .inputhelp b{color:#173F35}

    .metricbox{
      background:#FFFEFA;border:1px solid #E4DED1;border-radius:17px;
      padding:1rem;min-height:128px
    }
    .metriclabel{
      font-size:.69rem;text-transform:uppercase;letter-spacing:.085em;
      color:#68766F;font-weight:800
    }
    .metricvalue{
      font-size:1.52rem;font-weight:800;color:#173F35;margin:.35rem 0
    }
    .metricnote{
      font-size:.76rem;color:#68766F;line-height:1.42
    }

    .status{
      border-radius:18px;padding:1.2rem;background:#EEF4F0;
      border:1px solid #D5E4DC
    }
    .status strong{font-size:2rem;color:#173F35}
    .smallnote{font-size:.79rem;color:#596A63;line-height:1.5}

    .saved-banner{
      background:#EAF5EE;border:1px solid #C9E2D3;border-radius:14px;
      padding:.9rem 1rem;color:#24533E;font-size:.88rem;font-weight:650;
      margin:.55rem 0 1rem
    }

    .tablewrap{overflow-x:auto}
    table.fc{
      width:100%;border-collapse:collapse;background:#FFFEFA;
      border:1px solid #E4DED1;font-size:.8rem
    }
    table.fc th{
      background:#F0EEE7;color:#29433A;text-align:left;padding:.65rem
    }
    table.fc td{
      padding:.62rem;border-top:1px solid #EBE5D8;color:#253731
    }
    table.fc tr:nth-child(even) td{background:#FBF9F4}

    .stButton button{
      background:#173F35!important;color:#fff!important;border:none!important;
      border-radius:11px!important;font-weight:800!important;
      min-height:45px!important
    }
    .stButton button:hover{
      background:#2E6857!important;color:#fff!important
    }
    .stDownloadButton button{
      border-radius:11px!important;font-weight:800!important;min-height:43px!important
    }
    
    /* ---------- v2.3 visibility fix ---------- */
    div[data-testid="stTabs"] button[data-baseweb="tab"]{
      color:#53675F!important;
      opacity:1!important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"] p{
      color:#53675F!important;
      opacity:1!important;
      font-weight:800!important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p{
      color:#E25346!important;
    }
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"]{
      background-color:#E25346!important;
    }

    div[data-testid="stCaptionContainer"],
    div[data-testid="stCaptionContainer"] p{
      color:#5C6D66!important;
      opacity:1!important;
    }

    div[data-testid="stAlert"] p,
    div[data-testid="stAlert"] li,
    div[data-testid="stAlert"] span{
      color:#2B3F37!important;
      opacity:1!important;
    }

    div[data-testid="stMarkdownContainer"] p{
      opacity:1;
    }

    /* Help icons and secondary widget text should remain visible on cream */
    [data-testid="stTooltipIcon"] svg,
    button[data-testid="stBaseButton-headerNoPadding"] svg{
      color:#62746D!important;
      fill:#62746D!important;
    }

    
    /* ==========================================================
       v2.4.1 — FORCE TAB/NAVIGATION VISIBILITY
       ========================================================== */

    /* Entire tab row */
    div[data-testid="stTabs"] [data-baseweb="tab-list"]{
        gap: 0.25rem !important;
        border-bottom: 1px solid #D8D2C5 !important;
    }

    /* Inactive tabs */
    div[data-testid="stTabs"] button[data-baseweb="tab"]{
        background: transparent !important;
        color: #31483F !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }

    div[data-testid="stTabs"] button[data-baseweb="tab"] p,
    div[data-testid="stTabs"] button[data-baseweb="tab"] span,
    div[data-testid="stTabs"] button[data-baseweb="tab"] div{
        color: #31483F !important;
        -webkit-text-fill-color: #31483F !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }

    /* Selected tab */
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p,
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] span,
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] div{
        color: #D94E45 !important;
        -webkit-text-fill-color: #D94E45 !important;
        opacity: 1 !important;
    }

    /* Hover tab */
    div[data-testid="stTabs"] button[data-baseweb="tab"]:hover,
    div[data-testid="stTabs"] button[data-baseweb="tab"]:hover p,
    div[data-testid="stTabs"] button[data-baseweb="tab"]:hover span{
        color: #173F35 !important;
        -webkit-text-fill-color: #173F35 !important;
        opacity: 1 !important;
    }

    /* Red selected underline */
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"]{
        background-color: #D94E45 !important;
        height: 2px !important;
    }

    /* General secondary text contrast */
    div[data-testid="stCaptionContainer"],
    div[data-testid="stCaptionContainer"] p,
    .stCaption,
    small{
        color: #53655E !important;
        -webkit-text-fill-color: #53655E !important;
        opacity: 1 !important;
    }

    /* Ensure checkbox / radio labels stay readable */
    div[data-testid="stCheckbox"] label,
    div[data-testid="stCheckbox"] label p,
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label p{
        color: #243A32 !important;
        -webkit-text-fill-color: #243A32 !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }

    /* Information / warning / success boxes */
    div[data-testid="stAlert"] *,
    div[data-testid="stNotification"] *{
        opacity: 1 !important;
    }

</style>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------
def indian_number(value):
    """Indian digit grouping: 1234567 -> 12,34,567"""
    n = int(round(abs(float(value))))
    s = str(n)
    if len(s) <= 3:
        grouped = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        grouped = ",".join(parts + [last3])
    return grouped


def money(value):
    value = float(value)
    sign = "-" if value < 0 else ""
    return f"{sign}₹{indian_number(value)}"


def metric(label, value, note):
    return f"""
    <div class="metricbox">
      <div class="metriclabel">{html.escape(label)}</div>
      <div class="metricvalue">{html.escape(str(value))}</div>
      <div class="metricnote">{html.escape(note)}</div>
    </div>
    """


DISTRICTS = {
    "Jharkhand": ["Bokaro","Dhanbad","East Singhbhum","Hazaribagh","Ramgarh","Ranchi","Other / Not listed"],
    "West Bengal": ["Alipurduar","Bankura","Birbhum","Cooch Behar","Darjeeling","Hooghly","Howrah","Jalpaiguri",
                    "Malda","Murshidabad","Nadia","North 24 Parganas","Paschim Bardhaman","Paschim Medinipur",
                    "Purba Bardhaman","Purba Medinipur","Purulia","South 24 Parganas","Other / Not listed"],
    "Bihar": ["Bhojpur","Buxar","Darbhanga","Gaya","Muzaffarpur","Nalanda","Patna","Purnia","Rohtas","Other / Not listed"],
    "Uttar Pradesh": ["Agra","Aligarh","Ballia","Bareilly","Gorakhpur","Kanpur Nagar","Lucknow","Meerut",
                      "Prayagraj","Saharanpur","Varanasi","Other / Not listed"],
    "Punjab": ["Amritsar","Bathinda","Jalandhar","Ludhiana","Patiala","Sangrur","Other / Not listed"],
    "Haryana": ["Ambala","Hisar","Kaithal","Karnal","Kurukshetra","Panipat","Rohtak","Sirsa","Other / Not listed"],
    "Rajasthan": ["Ajmer","Bikaner","Jaipur","Jodhpur","Kota","Nagaur","Sikar","Sri Ganganagar","Udaipur","Other / Not listed"],
    "Madhya Pradesh": ["Bhopal","Dewas","Indore","Jabalpur","Raisen","Ratlam","Sehore","Ujjain","Vidisha","Other / Not listed"],
    "Maharashtra": ["Ahmednagar","Akola","Amravati","Jalgaon","Nagpur","Nashik","Pune","Sangli","Solapur","Other / Not listed"],
    "Gujarat": ["Ahmedabad","Anand","Banaskantha","Rajkot","Surat","Vadodara","Other / Not listed"],
    "Karnataka": ["Belagavi","Dharwad","Hassan","Kalaburagi","Mandya","Mysuru","Raichur","Vijayapura","Other / Not listed"],
    "Odisha": ["Balasore","Bargarh","Cuttack","Ganjam","Kalahandi","Khordha","Sambalpur","Other / Not listed"],
    "Telangana": ["Adilabad","Karimnagar","Khammam","Nalgonda","Nizamabad","Warangal","Other / Not listed"],
    "Tamil Nadu": ["Coimbatore","Erode","Madurai","Salem","Thanjavur","Tiruchirappalli","Tiruppur","Other / Not listed"],
    "Andhra Pradesh": ["Anantapur","Guntur","Krishna","Kurnool","Nellore","Prakasam","Other / Not listed"],
    "Chhattisgarh": ["Bilaspur","Dhamtari","Durg","Raipur","Rajnandgaon","Other / Not listed"],
    "Assam": ["Barpeta","Dibrugarh","Jorhat","Kamrup","Nagaon","Sonitpur","Other / Not listed"],
    "Kerala": ["Ernakulam","Kottayam","Kozhikode","Palakkad","Thrissur","Wayanad","Other / Not listed"],
}

STATES = [
    "Andhra Pradesh","Assam","Bihar","Chhattisgarh","Gujarat","Haryana",
    "Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra",
    "Odisha","Punjab","Rajasthan","Tamil Nadu","Telangana","Uttar Pradesh",
    "West Bengal","Other State / UT"
]


def crop_defaults(crop_name):
    row = benchmarks.loc[crop_name]
    return {
        "yield_input": float(row["default_yield_kg_acre"]),
        "loss_input": float(row["default_loss_pct"]),
        "months_input": int(row["default_cycle_months"]),
        "price_input": float(row["msp_2026_27_rs_qtl"]),
        "seed_input": float(row["seed_rs_acre"]),
        "fertilizer_input": float(row["fertilizer_rs_acre"]),
        "pesticides_input": float(row["pesticides_rs_acre"]),
        "labour_input": float(row["labour_rs_acre"]),
        "irrigation_input": float(row["irrigation_rs_acre"]),
        "machinery_input": float(row["machinery_rs_acre"]),
        "packaging_input": float(row["packaging_rs_acre"]),
        "transport_input": float(row["transport_rs_acre"]),
        "other_input": float(row["other_rs_acre"]),
    }


def load_selected_crop_defaults():
    values = crop_defaults(st.session_state.crop_input)

    district_yields = st.session_state.get("_district_yield_map", {})
    historical_yield = district_yields.get(st.session_state.crop_input)

    if historical_yield is not None:
        values["yield_input"] = float(round(historical_yield, 0))

    for key, value in values.items():
        st.session_state[key] = value


def calculate_submission(
    applicant, state, district, crop, price_basis, area, yield_pa, loss_pct,
    months, loan, rate, expected_price, depreciation, costs
):
    inputs = {
        "area": area,
        "yield_per_acre": yield_pa,
        "loss_pct": loss_pct,
        "price_qtl": expected_price,
        "cost_items_per_acre": costs,
        "loan": loan,
        "annual_rate_pct": rate,
        "months": months,
        "depreciation": depreciation,
    }
    result = calculate_case(**inputs)
    scenarios = run_scenarios(inputs)
    status, note = resilience_label(result, scenarios)

    case = {
        "Applicant": applicant.strip(),
        "State": state,
        "District": district,
        "Crop": crop,
        "Price Basis": price_basis,
        "Area": area,
        "Expected Yield": yield_pa,
        "Selling Price": expected_price,
        "Loan": loan,
        "Revenue": result["revenue"],
        "Accounting Cost": result["total_accounting_cost"],
        "Profit": result["accounting_profit"],
        "Margin": result["margin"],
        "Coverage": result["harvest_coverage"],
        "Break-even Price": result["break_even_price"],
        "Break-even Yield": result["break_even_yield"],
        "Supportable Loan": result["indicative_max_supportable_loan"],
        "Resilience": status,
        "Status Note": note,
    }
    return inputs, result, scenarios, case


def make_html_report(case):
    rows = [
        ("Applicant", case["Applicant"]),
        ("Location", f'{case["District"]}, {case["State"]}'),
        ("Crop", case["Crop"]),
        ("Area", f'{case["Area"]:.2f} acres'),
        ("Expected yield", f'{case["Expected Yield"]:,.0f} kg/acre'),
        ("Expected selling price", f'₹{indian_number(case["Selling Price"])}/qtl'),
        ("Loan requested", money(case["Loan"])),
        ("Expected revenue", money(case["Revenue"])),
        ("Accounting cost", money(case["Accounting Cost"])),
        ("Accounting profit", money(case["Profit"])),
        ("Profit margin", f'{case["Margin"]:.1f}%'),
        ("Break-even price", f'₹{indian_number(case["Break-even Price"])}/qtl'),
        ("Break-even yield", f'{case["Break-even Yield"]:,.0f} kg/acre'),
        ("Harvest coverage", f'{case["Coverage"]:.2f}×'),
        ("Indicative supportable loan", money(case["Supportable Loan"])),
        ("Financial resilience", case["Resilience"]),
    ]
    trs = "".join(
        f"<tr><th>{html.escape(k)}</th><td>{html.escape(str(v))}</td></tr>"
        for k, v in rows
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>FarmCredit Assessment</title>
<style>
body{{font-family:Arial,sans-serif;max-width:850px;margin:40px auto;color:#173F35}}
h1{{margin-bottom:4px}}p{{color:#5f6e68;line-height:1.5}}
table{{width:100%;border-collapse:collapse;margin-top:22px}}
th,td{{border:1px solid #ddd;padding:10px;text-align:left}}
th{{width:40%;background:#eef4f0}}
.note{{margin-top:24px;padding:14px;background:#fff8e9;border-left:4px solid #c49a52}}
</style></head><body>
<h1>FarmCredit — Farmer Loan Assessment</h1>
<p>Accounting-based academic decision-support report.</p>
<table>{trs}</table>
<div class="note"><b>Interpretation:</b> {html.escape(case["Status Note"])}<br><br>
This is not a credit sanction. Actual lending decisions require lender-specific
underwriting, KYC, credit history, field verification and other applicable checks.</div>
</body></html>"""


def demo_cases():
    return [
        {
            "Applicant":"Demo Farmer 01","State":"Jharkhand","District":"Ranchi",
            "Crop":"Paddy (Common)","Price Basis":"MSP reference","Area":3.0,
            "Expected Yield":1200.0,"Selling Price":2441.0,"Loan":45000.0,
            "Revenue":83500.0,"Accounting Cost":58600.0,"Profit":24900.0,
            "Margin":29.8,"Coverage":1.79,"Break-even Price":1713.0,
            "Break-even Yield":842.0,"Supportable Loan":54000.0,
            "Resilience":"Strong",
            "Status Note":"Profitable base case with comparatively comfortable modeled coverage."
        },
        {
            "Applicant":"Demo Farmer 02","State":"West Bengal","District":"Jalpaiguri",
            "Crop":"Wheat","Price Basis":"MSP reference","Area":2.0,
            "Expected Yield":1400.0,"Selling Price":2585.0,"Loan":55000.0,
            "Revenue":69500.0,"Accounting Cost":61200.0,"Profit":8300.0,
            "Margin":11.9,"Coverage":1.22,"Break-even Price":2277.0,
            "Break-even Yield":1235.0,"Supportable Loan":52000.0,
            "Resilience":"Moderate",
            "Status Note":"Positive base case but thinner downside cushion."
        },
        {
            "Applicant":"Demo Farmer 03","State":"Bihar","District":"Patna",
            "Crop":"Maize","Price Basis":"Farmer / lender estimate","Area":2.5,
            "Expected Yield":1000.0,"Selling Price":2250.0,"Loan":70000.0,
            "Revenue":53400.0,"Accounting Cost":59200.0,"Profit":-5800.0,
            "Margin":-10.9,"Coverage":0.74,"Break-even Price":2494.0,
            "Break-even Yield":1108.0,"Supportable Loan":41000.0,
            "Resilience":"Stressed",
            "Status Note":"Modeled base case is loss-making and repayment coverage is weak."
        },
    ]


# -------------------------------------------------------------------
# SESSION INITIALIZATION
# -------------------------------------------------------------------
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

if "crop_input" not in st.session_state:
    st.session_state.crop_input = "Paddy (Common)"

defaults = crop_defaults(st.session_state.crop_input)
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "last_result" not in st.session_state:
    st.session_state.last_result = None
    st.session_state.last_scenarios = None
    st.session_state.last_case = None
    st.session_state.last_inputs = None

if "live_market_result" not in st.session_state:
    st.session_state.live_market_result = None
if "live_modal_price" not in st.session_state:
    st.session_state.live_modal_price = None



# -------------------------------------------------------------------
# LOCATION MASTER
# -------------------------------------------------------------------
_online_locations, location_source = load_online_location_master()

if _online_locations:
    ACTIVE_DISTRICTS = _online_locations
    ACTIVE_STATES = list(_online_locations.keys()) + ["Other State / UT"]
else:
    ACTIVE_DISTRICTS = DISTRICTS
    ACTIVE_STATES = STATES

# -------------------------------------------------------------------
# HEADER
# -------------------------------------------------------------------
st.markdown(
    """
    <div class="brandbar">
      <div class="brand">🌾 FarmCredit</div>
      <div class="badge">Submission build · v2.4.1</div>
    </div>
    <div class="hero">
      <h1>Farmer profitability & loan viability, in one view.</h1>
      <p>
        Enter the farmer's crop-cycle assumptions and click <b>Submit & Save Assessment</b>.
        FarmCredit will calculate profitability, break-even, repayment coverage and stress resilience,
        and will automatically record the submitted farmer in the Banker View.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

farm_tab, banker_tab, method_tab = st.tabs(
    ["Farm Assessment", "Banker View", "Methodology"]
)


# -------------------------------------------------------------------
# FARM ASSESSMENT TAB
# -------------------------------------------------------------------
with farm_tab:

    st.markdown(
        '<div class="sectionlabel">01 · Farmer identity, location & crop</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2, gap="large")

    with c1:
        with st.container(border=True):
            st.subheader("Farmer details")

            applicant = st.text_input(
                "Farmer name / Applicant ID",
                placeholder="Example: Ramesh Kumar / F-001",
                help="This is the name/ID that will appear in Banker View after submission.",
            )

            state_choice = st.selectbox(
                "State / UT",
                ACTIVE_STATES,
                index=ACTIVE_STATES.index("Jharkhand") if "Jharkhand" in ACTIVE_STATES else 0,
                help="Select the state where the farm is located.",
            )

            if state_choice == "Other State / UT":
                state_final = st.text_input(
                    "Enter State / UT name",
                    placeholder="Example: Meghalaya",
                ).strip() or "Not specified"
                district_final = st.text_input(
                    "District",
                    placeholder="Example: East Khasi Hills",
                ).strip() or "Not specified"
            else:
                state_final = state_choice
                dlist = ACTIVE_DISTRICTS.get(state_choice, ["Other / Not listed"])
                district_choice = st.selectbox(
                    "District",
                    dlist,
                    help="Select the district. Use Other / Not listed if needed.",
                )
                if district_choice == "Other / Not listed":
                    district_final = st.text_input(
                        "Enter district name",
                        placeholder="Type the district name",
                    ).strip() or "Not specified"
                else:
                    district_final = district_choice

            # Historical district crop evidence is independent of the live mandi-price API.
            with st.spinner("Checking historical district crop evidence..."):
                crop_profile_result = get_crop_profile(
                    state=state_final,
                    district=district_final,
                )

            researched_crops = profile_crop_options(crop_profile_result)
            supported_all = benchmarks.index.tolist()

            # Keep only FarmCredit-supported crops that have historical evidence.
            researched_crops = [
                c for c in researched_crops if c in supported_all
            ]

            show_all_supported = st.checkbox(
                "Show all FarmCredit-supported crops",
                value=False,
                help=(
                    "By default, the crop list is filtered using historical district/state "
                    "production evidence. Turn this on if you need a crop that is not present "
                    "in the historical series."
                ),
            )

            if researched_crops and not show_all_supported:
                crop_options = researched_crops
            else:
                crop_options = supported_all

            if st.session_state.get("crop_input") not in crop_options:
                st.session_state.crop_input = crop_options[0]

            # Store historical district/state yields for the crop-change callback.
            district_yield_map = {}
            for crop_name in researched_crops:
                bench = crop_benchmark(crop_profile_result, crop_name)
                if bench and bench.get("yield_kg_acre"):
                    district_yield_map[crop_name] = bench["yield_kg_acre"]
            st.session_state["_district_yield_map"] = district_yield_map

            crop = st.selectbox(
                "Crop",
                crop_options,
                key="crop_input",
                on_change=load_selected_crop_defaults,
                help=(
                    "When historical evidence is available, FarmCredit shows district-established "
                    "crops first and uses the recent historical yield benchmark as the starter yield."
                ),
            )

            selected_crop_benchmark = crop_benchmark(
                crop_profile_result,
                crop,
            )

            # If location changed but crop stayed the same, update the starter yield once.
            context_key = f"{state_final}|{district_final}|{crop}"
            if st.session_state.get("_historical_yield_context") != context_key:
                st.session_state["_historical_yield_context"] = context_key
                if (
                    selected_crop_benchmark
                    and selected_crop_benchmark.get("yield_kg_acre")
                ):
                    st.session_state["yield_input"] = float(
                        round(selected_crop_benchmark["yield_kg_acre"], 0)
                    )

            row = benchmarks.loc[crop]
            st.caption(
                f'{row["season"]} crop · Official 2026–27 MSP reference: '
                f'₹{indian_number(row["msp_2026_27_rs_qtl"])}/quintal'
            )

            if selected_crop_benchmark and selected_crop_benchmark.get("yield_kg_acre"):
                scope_label = (
                    "district-level"
                    if selected_crop_benchmark["scope"] == "district"
                    else "state-level fallback"
                )
                st.markdown(
                    f"""
                    <div class="inputhelp">
                      <b>Historical crop benchmark ({scope_label})</b><br>
                      Crop: <b>{html.escape(crop)}</b><br>
                      Historical yield benchmark: <b>{selected_crop_benchmark["yield_kg_acre"]:,.0f} kg/acre</b><br>
                      Most recent year in the fallback series: <b>{selected_crop_benchmark["latest_year"]}</b><br>
                      Recent years used for yield benchmark: <b>{html.escape(selected_crop_benchmark["recent_years_used"])}</b><br>
                      Recorded season(s): <b>{html.escape(selected_crop_benchmark["season_evidence"])}</b><br>
                      <span style="font-size:.75rem">
                        This is a historical production benchmark, not a current-year yield forecast.
                      </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.warning(
                    "No usable historical yield benchmark was found for this crop/location. "
                    "FarmCredit is using the generic editable crop starter value."
                )

            if crop_profile_result.get("scope") == "state":
                st.info(crop_profile_result.get("message"))
            elif not crop_profile_result.get("ok"):
                st.warning(crop_profile_result.get("message"))

            st.caption(
                f"Administrative location source: {location_source}. "
                "LGD remains the formal Government of India geographic reference."
            )
            st.caption(
                "Crop/yield fallback source: Government of India DES district-wise, "
                "season-wise crop production statistics. FarmCredit uses a static historical "
                "mirror for speed and keeps the result clearly labelled as historical."
            )

    with c2:
        with st.container(border=True):
            st.subheader("Selling price")

            price_basis = st.selectbox(
                "What does the selling price represent?",
                [
                    "MSP reference",
                    "Recent mandi price entered manually",
                    "Farmer / lender estimate",
                    "Live mandi price from data.gov.in (optional)",
                ],
                help="Choose the source/basis of the price used for revenue calculation.",
            )

            # Clearly separated optional API section.
            if price_basis == "Live mandi price from data.gov.in (optional)":
                st.markdown(
                    """
                    <div class="inputhelp">
                      <b>LIVE MARKET DATA — API KEY REQUIRED</b><br>
                      To fetch a live mandi observation, enter your personal
                      <b>data.gov.in API key</b> below. The key is used only for this live request
                      and is not written into the FarmCredit code or Banker View.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                api_key = st.text_input(
                    "🔑 data.gov.in API KEY",
                    type="password",
                    placeholder="Paste your data.gov.in API key here",
                    help="Required only if you want FarmCredit to fetch live mandi data.",
                )

                st.caption(
                    "Live fetch is optional. Requests are server-filtered, limited to a few records and cached "
                    "for 10 minutes. If data.gov.in takes more than about 6 seconds, FarmCredit stops waiting "
                    "so the rest of the dashboard stays responsive."
                )

                if st.button(
                    "🌐 FETCH LIVE MANDI PRICE USING API KEY",
                    use_container_width=True,
                ):
                    with st.spinner("Fetching the latest matching mandi observation..."):
                        st.session_state.live_market_result = fetch_live_mandi_price(
                            api_key=api_key,
                            state=state_final,
                            district=district_final,
                            crop=crop,
                        )

                    if st.session_state.live_market_result.get("ok"):
                        latest = st.session_state.live_market_result["latest"]
                        st.session_state.live_modal_price = float(latest["modal_price"])
                        st.success(
                            f'Live mandi data loaded: ₹{indian_number(st.session_state.live_modal_price)}/quintal.'
                        )
                    else:
                        st.warning(st.session_state.live_market_result.get("message", "Live fetch failed."))

                live_result = st.session_state.live_market_result
                if live_result and live_result.get("ok"):
                    latest = live_result["latest"]
                    live_market = str(latest.get("market", "Not provided"))
                    live_date = str(latest.get("arrival_date", "Not provided"))
                    live_min = latest.get("min_price")
                    live_max = latest.get("max_price")
                    st.markdown(
                        f"""
                        <div class="inputhelp">
                          <b>Latest live observation</b><br>
                          Modal price: <b>₹{indian_number(latest["modal_price"])}/quintal</b><br>
                          Market: <b>{html.escape(live_market)}</b><br>
                          Date: <b>{html.escape(live_date)}</b><br>
                          Range: <b>₹{indian_number(live_min) if pd.notna(live_min) else "N/A"}
                          – ₹{indian_number(live_max) if pd.notna(live_max) else "N/A"}</b>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if st.button(
                        "USE LIVE MODAL PRICE IN THIS ASSESSMENT",
                        use_container_width=True,
                    ):
                        st.session_state.price_input = float(latest["modal_price"])
                        st.success("Live modal price copied into the Selling Price field.")
                        st.rerun()

            expected_price = st.number_input(
                "Selling price (₹ per quintal)",
                min_value=1.0,
                step=10.0,
                key="price_input",
                help="The price expected to be received for 1 quintal (100 kg) of saleable crop.",
            )

            if price_basis == "Recent mandi price entered manually":
                market_name = st.text_input(
                    "Mandi / market name",
                    placeholder="Example: Ranchi APMC",
                )
                market_date = st.date_input(
                    "Price observation date",
                    value=date.today(),
                )
            else:
                market_name = ""
                market_date = None

            msp = float(row["msp_2026_27_rs_qtl"])
            price_diff = (expected_price - msp) / msp * 100 if msp else 0

            st.markdown(
                f"""
                <div class="inputhelp">
                  <b>How to read this number</b><br>
                  ₹{indian_number(expected_price)} / quintal means the model assumes
                  the farmer receives ₹{indian_number(expected_price)} for every 100 kg sold.<br>
                  MSP reference for {html.escape(crop)}: <b>₹{indian_number(msp)} / quintal</b>
                  ({price_diff:+.1f}% difference).
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="sectionlabel">02 · Production & financing</div>',
        unsafe_allow_html=True,
    )

    p1, p2 = st.columns(2, gap="large")

    with p1:
        with st.container(border=True):
            st.subheader("Production numbers")

            area = st.number_input(
                "Farm area (acres)",
                min_value=0.1,
                value=3.0,
                step=0.5,
                help="Total cultivated land used for this crop.",
            )

            yield_pa = st.number_input(
                "Expected yield BEFORE loss (kg per acre) — editable",
                min_value=1.0,
                step=50.0,
                key="yield_input",
                help=("Starter value uses the historical district/state yield benchmark when available; "
      "otherwise the generic crop benchmark. You should edit it if farmer-specific evidence is available."),
            )

            loss_pct = st.number_input(
                "Post-harvest loss (% of production)",
                min_value=0.0,
                max_value=50.0,
                step=0.5,
                key="loss_input",
                help="Percentage of harvested crop expected to be unavailable for sale.",
            )

            months = st.number_input(
                "Crop cycle length (months)",
                min_value=1,
                max_value=24,
                step=1,
                key="months_input",
                help="Used to calculate interest only for the crop-cycle period.",
            )

            gross_preview = area * yield_pa
            saleable_preview = gross_preview * (1 - loss_pct / 100)

            st.markdown(
                f"""
                <div class="inputhelp">
                  <b>Production preview</b><br>
                  {area:.2f} acres × {yield_pa:,.0f} kg/acre =
                  <b>{gross_preview:,.0f} kg gross production</b>.<br>
                  After {loss_pct:.1f}% loss, estimated saleable output =
                  <b>{saleable_preview:,.0f} kg ({saleable_preview/100:,.1f} quintals)</b>.
                </div>
                """,
                unsafe_allow_html=True,
            )

    with p2:
        with st.container(border=True):
            st.subheader("Loan numbers")

            loan = st.number_input(
                "Loan principal requested (₹)",
                min_value=0.0,
                value=45000.0,
                step=5000.0,
                help="The amount the farmer proposes to borrow. This is principal, before interest.",
            )

            rate = st.number_input(
                "Annual interest rate (% p.a.)",
                min_value=0.0,
                value=7.0,
                step=0.25,
                help="Annual interest rate. FarmCredit applies it only for the selected crop-cycle months.",
            )

            cycle_interest_preview = loan * (rate / 100) * (months / 12)
            obligation_preview = loan + cycle_interest_preview

            st.markdown(
                f"""
                <div class="inputhelp">
                  <b>Financing preview</b><br>
                  Principal requested: <b>{money(loan)}</b><br>
                  Estimated interest for {months} month(s): <b>{money(cycle_interest_preview)}</b><br>
                  Principal + crop-cycle interest: <b>{money(obligation_preview)}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="sectionlabel">03 · Cultivation cost inputs</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.subheader("Cost per acre")
        st.caption(
            "Every value below is ₹ PER ACRE. FarmCredit multiplies the per-acre total by the farm area."
        )

        a, b, c = st.columns(3)

        with a:
            seed = st.number_input(
                "Seed cost (₹/acre)",
                min_value=0.0,
                step=100.0,
                key="seed_input",
            )
            fertilizer = st.number_input(
                "Fertilizer cost (₹/acre)",
                min_value=0.0,
                step=100.0,
                key="fertilizer_input",
            )
            pesticides = st.number_input(
                "Pesticide cost (₹/acre)",
                min_value=0.0,
                step=100.0,
                key="pesticides_input",
            )

        with b:
            labour = st.number_input(
                "Labour cost (₹/acre)",
                min_value=0.0,
                step=100.0,
                key="labour_input",
            )
            irrigation = st.number_input(
                "Irrigation cost (₹/acre)",
                min_value=0.0,
                step=100.0,
                key="irrigation_input",
            )
            machinery = st.number_input(
                "Machinery / field operation cost (₹/acre)",
                min_value=0.0,
                step=100.0,
                key="machinery_input",
            )

        with c:
            packaging = st.number_input(
                "Packaging cost (₹/acre)",
                min_value=0.0,
                step=100.0,
                key="packaging_input",
            )
            transport = st.number_input(
                "Transport cost (₹/acre)",
                min_value=0.0,
                step=100.0,
                key="transport_input",
            )
            other = st.number_input(
                "Other cultivation cost (₹/acre)",
                min_value=0.0,
                step=100.0,
                key="other_input",
            )

        depreciation = st.number_input(
            "Depreciation allocated to THIS crop cycle (₹ for entire farm)",
            min_value=0.0,
            value=3000.0,
            step=500.0,
            help="Unlike the cultivation fields above, this is the total depreciation allocated to this crop cycle for the entire farm.",
        )

        costs = {
            "Seed": seed,
            "Fertilizer": fertilizer,
            "Pesticides": pesticides,
            "Labour": labour,
            "Irrigation": irrigation,
            "Machinery": machinery,
            "Packaging": packaging,
            "Transport": transport,
            "Other": other,
        }

        cost_per_acre_preview = sum(costs.values())
        whole_farm_cost_preview = cost_per_acre_preview * area

        st.markdown(
            f"""
            <div class="inputhelp">
              <b>Cost preview</b><br>
              Total cultivation cost entered = <b>{money(cost_per_acre_preview)} per acre</b>.<br>
              For {area:.2f} acres, cash cultivation cost = <b>{money(whole_farm_cost_preview)}</b>
              before interest and depreciation.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="sectionlabel">04 · Submit assessment</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "Nothing is recorded in Banker View until you click the button below. "
        "Submitting a farmer with the same name/ID again will update that farmer instead of creating a duplicate."
    )

    submitted = st.button(
        "✅ SUBMIT & SAVE FARMER ASSESSMENT",
        use_container_width=True,
        type="primary",
    )

    if submitted:
        if not applicant.strip():
            st.error("Please enter the farmer name or Applicant ID before submitting.")
        else:
            inputs, result, scenarios, case = calculate_submission(
                applicant=applicant,
                state=state_final,
                district=district_final,
                crop=crop,
                price_basis=price_basis,
                area=area,
                yield_pa=yield_pa,
                loss_pct=loss_pct,
                months=months,
                loan=loan,
                rate=rate,
                expected_price=expected_price,
                depreciation=depreciation,
                costs=costs,
            )

            # Save/replace case in the current Streamlit session.
            st.session_state.portfolio = [
                x for x in st.session_state.portfolio
                if x["Applicant"].strip().lower() != applicant.strip().lower()
            ]
            st.session_state.portfolio.append(case)

            st.session_state.last_inputs = inputs
            st.session_state.last_result = result
            st.session_state.last_scenarios = scenarios
            st.session_state.last_case = case

            st.success(
                f"✅ {applicant.strip()} submitted successfully and saved to Banker View."
            )

    # ----------------------------------------------------------------
    # RESULTS = LAST SUBMITTED ASSESSMENT
    # ----------------------------------------------------------------
    if st.session_state.last_result is None:
        st.markdown(
            """
            <div class="saved-banner">
              Enter the farmer's data above and click
              <b>SUBMIT & SAVE FARMER ASSESSMENT</b>.
              The financial dashboard will appear here after submission.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        r = st.session_state.last_result
        scenarios = st.session_state.last_scenarios
        case = st.session_state.last_case

        st.markdown(
            f"""
            <div class="saved-banner">
              Showing the last submitted assessment for
              <b>{html.escape(case["Applicant"])}</b>.
              This farmer is saved in Banker View for the current session.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="sectionlabel">05 · Financial dashboard</div>',
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)

        cards1 = [
            (
                "Expected Revenue",
                money(r["revenue"]),
                "Expected money from saleable crop output at the submitted selling price.",
            ),
            (
                "Total Accounting Cost",
                money(r["total_accounting_cost"]),
                "Cash cultivation cost + crop-cycle interest + depreciation.",
            ),
            (
                "Accounting Profit",
                money(r["accounting_profit"]),
                f'Revenue minus total accounting cost. Margin: {r["margin"]:.1f}%.',
            ),
            (
                "Harvest Repayment Coverage",
                f'{r["harvest_coverage"]:.2f}×',
                "Expected revenue ÷ (loan principal + crop-cycle interest).",
            ),
        ]
        for col, card in zip([m1, m2, m3, m4], cards1):
            with col:
                st.markdown(metric(*card), unsafe_allow_html=True)

        n1, n2, n3, n4 = st.columns(4)

        cards2 = [
            (
                "Break-even Selling Price",
                f'₹{indian_number(r["break_even_price"])}/qtl',
                "Minimum modeled selling price required to cover accounting cost.",
            ),
            (
                "Break-even Yield",
                f'{r["break_even_yield"]:,.0f} kg/acre',
                "Minimum modeled yield required at the submitted selling price.",
            ),
            (
                "Cash Profit Before Depreciation",
                money(r["cash_profit"]),
                "Revenue minus cultivation cash cost and crop-cycle interest.",
            ),
            (
                "Indicative Supportable Loan",
                money(r["indicative_max_supportable_loan"]),
                "Illustrative borrowing level at 1.25× target coverage, capped by cash cost.",
            ),
        ]
        for col, card in zip([n1, n2, n3, n4], cards2):
            with col:
                st.markdown(metric(*card), unsafe_allow_html=True)

        st.markdown(
            '<div class="sectionlabel">06 · Financial resilience & visuals</div>',
            unsafe_allow_html=True,
        )

        s1, s2, s3 = st.columns([0.8, 1.0, 1.0], gap="large")

        with s1:
            st.markdown(
                f"""
                <div class="status">
                  <div class="smallnote">Indicative financial resilience</div>
                  <strong>{html.escape(case["Resilience"])}</strong>
                  <div class="smallnote" style="margin-top:.55rem">
                    {html.escape(case["Status Note"])}
                  </div>
                  <hr style="border:none;border-top:1px solid #D8E5DE;margin:.8rem 0">
                  <div class="smallnote">
                    Price cushion: <b>{r["price_cushion"]:.1f}%</b>
                  </div>
                  <div class="smallnote">
                    Yield cushion: <b>{r["yield_cushion"]:.1f}%</b>
                  </div>
                  <div class="smallnote">
                    Repayment obligation: <b>{money(r["repayment_obligation"])}</b>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        submitted_costs = st.session_state.last_inputs["cost_items_per_acre"]

        with s2:
            fig_cost = go.Figure(
                go.Pie(
                    labels=list(submitted_costs.keys()),
                    values=list(submitted_costs.values()),
                    hole=.62,
                    textinfo="none",
                )
            )
            fig_cost.update_layout(
                title="Cultivation cost composition (₹/acre)",
                height=320,
                margin=dict(l=10, r=10, t=50, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", y=-0.08),
            )
            st.plotly_chart(
                fig_cost,
                use_container_width=True,
                config={"displayModeBar": False},
            )

        with s3:
            fig_be = go.Figure(
                go.Bar(
                    y=["Submitted selling price", "Break-even selling price"],
                    x=[
                        case["Selling Price"],
                        r["break_even_price"],
                    ],
                    orientation="h",
                    text=[
                        f'₹{indian_number(case["Selling Price"])}/qtl',
                        f'₹{indian_number(r["break_even_price"])}/qtl',
                    ],
                    textposition="outside",
                )
            )
            fig_be.update_layout(
                title="Selling price vs break-even",
                height=320,
                margin=dict(l=10, r=55, t=50, b=30),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="₹ per quintal",
            )
            st.plotly_chart(
                fig_be,
                use_container_width=True,
                config={"displayModeBar": False},
            )

        st.markdown(
            '<div class="sectionlabel">07 · Stress test</div>',
            unsafe_allow_html=True,
        )

        sdf = pd.DataFrame(scenarios)

        fig_stress = go.Figure(
            go.Bar(
                x=sdf["Scenario"],
                y=sdf["Accounting profit"],
                text=[money(x) for x in sdf["Accounting profit"]],
                textposition="outside",
            )
        )
        fig_stress.add_hline(y=0, line_width=1)
        fig_stress.update_layout(
            title="Accounting profit under price and yield shocks",
            height=360,
            margin=dict(l=10, r=10, t=50, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title="Accounting profit (₹)",
        )
        st.plotly_chart(
            fig_stress,
            use_container_width=True,
            config={"displayModeBar": False},
        )

        table_rows = []
        for x in scenarios:
            y_text = "Base" if x["Yield change"] == 0 else f'{x["Yield change"]:+.0%}'
            p_text = "Base" if x["Price change"] == 0 else f'{x["Price change"]:+.0%}'
            table_rows.append(
                "<tr>"
                f"<td>{html.escape(x['Scenario'])}</td>"
                f"<td>{y_text}</td>"
                f"<td>{p_text}</td>"
                f"<td>{money(x['Revenue'])}</td>"
                f"<td>{money(x['Accounting profit'])}</td>"
                f"<td>{x['Margin']:.1f}%</td>"
                f"<td>{x['Harvest coverage']:.2f}×</td>"
                "</tr>"
            )

        st.markdown(
            "<div class='tablewrap'><table class='fc'><thead><tr>"
            "<th>Scenario</th><th>Yield change</th><th>Price change</th>"
            "<th>Revenue</th><th>Accounting profit</th><th>Margin</th>"
            "<th>Coverage</th></tr></thead><tbody>"
            + "".join(table_rows)
            + "</tbody></table></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="sectionlabel">08 · Download submitted assessment</div>',
            unsafe_allow_html=True,
        )

        st.download_button(
            "Download this farmer's assessment report",
            make_html_report(case),
            file_name=f'{case["Applicant"].replace(" ", "_")}_FarmCredit_Assessment.html',
            mime="text/html",
            use_container_width=True,
        )


# -------------------------------------------------------------------
# BANKER VIEW TAB
# -------------------------------------------------------------------
with banker_tab:

    st.markdown(
        '<div class="sectionlabel">Submitted farmer portfolio</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.portfolio:
        st.info(
            "No farmer has been submitted yet. Go to Farm Assessment, enter the farmer's data, "
            "and click SUBMIT & SAVE FARMER ASSESSMENT."
        )

        if st.button("Load 3 demo farmer cases", use_container_width=True):
            st.session_state.portfolio = demo_cases()
            st.rerun()

    else:
        pf = pd.DataFrame(st.session_state.portfolio)

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(
                metric(
                    "Submitted Farmers",
                    len(pf),
                    "Number of farmer assessments saved in this browser session.",
                ),
                unsafe_allow_html=True,
            )
        with k2:
            st.markdown(
                metric(
                    "Total Loan Requested",
                    money(pf["Loan"].sum()),
                    "Sum of loan principal requested by submitted farmers.",
                ),
                unsafe_allow_html=True,
            )
        with k3:
            st.markdown(
                metric(
                    "Strong Cases",
                    int((pf["Resilience"] == "Strong").sum()),
                    "Submitted cases classified as Strong by the academic model.",
                ),
                unsafe_allow_html=True,
            )
        with k4:
            st.markdown(
                metric(
                    "Stressed Cases",
                    int((pf["Resilience"] == "Stressed").sum()),
                    "Submitted cases requiring closer financial review.",
                ),
                unsafe_allow_html=True,
            )

        selected_statuses = st.multiselect(
            "Show financial resilience",
            ["Strong", "Moderate", "Stressed"],
            default=["Strong", "Moderate", "Stressed"],
        )

        filtered = pf[pf["Resilience"].isin(selected_statuses)].copy()

        if filtered.empty:
            st.warning("No submitted farmers match the selected filter.")
        else:
            rows = []
            for _, x in filtered.iterrows():
                rows.append(
                    "<tr>"
                    f"<td>{html.escape(str(x['Applicant']))}</td>"
                    f"<td>{html.escape(str(x['District']))}, {html.escape(str(x['State']))}</td>"
                    f"<td>{html.escape(str(x['Crop']))}</td>"
                    f"<td>{x['Area']:.2f} acres</td>"
                    f"<td>{money(x['Loan'])}</td>"
                    f"<td>{money(x['Profit'])}</td>"
                    f"<td>{x['Coverage']:.2f}×</td>"
                    f"<td>{html.escape(str(x['Resilience']))}</td>"
                    "</tr>"
                )

            st.markdown(
                "<div class='tablewrap'><table class='fc'><thead><tr>"
                "<th>Farmer / Applicant</th><th>Location</th><th>Crop</th>"
                "<th>Farm Area</th><th>Loan Requested</th><th>Accounting Profit</th>"
                "<th>Harvest Coverage</th><th>Resilience</th>"
                "</tr></thead><tbody>"
                + "".join(rows)
                + "</tbody></table></div>",
                unsafe_allow_html=True,
            )

            st.subheader("Farmer drill-down")
            selected_applicant = st.selectbox(
                "Select a submitted farmer",
                filtered["Applicant"].tolist(),
            )
            selected_case = next(
                x for x in st.session_state.portfolio
                if x["Applicant"] == selected_applicant
            )

            q1, q2, q3, q4 = st.columns(4)
            q1.metric(
                "Accounting Profit",
                money(selected_case["Profit"]),
                help="Revenue minus total accounting cost.",
            )
            q2.metric(
                "Harvest Coverage",
                f'{selected_case["Coverage"]:.2f}×',
                help="Expected revenue divided by loan principal plus crop-cycle interest.",
            )
            q3.metric(
                "Break-even Price",
                f'₹{indian_number(selected_case["Break-even Price"])}/qtl',
                help="Minimum modeled selling price required to recover accounting cost.",
            )
            q4.metric(
                "Indicative Supportable Loan",
                money(selected_case["Supportable Loan"]),
                help="Illustrative supportable borrowing based on modeled revenue and target coverage.",
            )

            st.info(selected_case["Status Note"])

        csv_bytes = pf.drop(
            columns=["Status Note"],
            errors="ignore",
        ).to_csv(index=False).encode("utf-8")

        b1, b2 = st.columns(2)
        with b1:
            st.download_button(
                "Download submitted farmer portfolio (CSV)",
                csv_bytes,
                file_name="FarmCredit_Submitted_Farmers.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with b2:
            if st.button("Clear all submitted farmers", use_container_width=True):
                st.session_state.portfolio = []
                st.session_state.last_result = None
                st.session_state.last_scenarios = None
                st.session_state.last_case = None
                st.session_state.last_inputs = None
                st.rerun()

        st.caption(
            "Submitted farmers are stored in the current Streamlit browser session. "
            "Use the CSV download if you need to retain the portfolio permanently."
        )


# -------------------------------------------------------------------
# METHODOLOGY TAB
# -------------------------------------------------------------------
with method_tab:

    st.markdown("## What each major number means")

    explanation = pd.DataFrame(
        [
            ["Expected Revenue", "Saleable crop quantity × selling price", "₹"],
            ["Accounting Cost", "Cultivation cash cost + interest + depreciation", "₹"],
            ["Accounting Profit", "Expected revenue − accounting cost", "₹"],
            ["Profit Margin", "Accounting profit ÷ revenue", "%"],
            ["Harvest Coverage", "Revenue ÷ (loan principal + crop-cycle interest)", "×"],
            ["Break-even Price", "Accounting cost ÷ saleable output", "₹/quintal"],
            ["Break-even Yield", "Minimum yield needed to cover accounting cost", "kg/acre"],
            ["Indicative Supportable Loan", "Illustrative loan capacity at 1.25× target coverage", "₹"],
        ],
        columns=["Dashboard number", "Meaning", "Unit"],
    )
    st.dataframe(explanation, hide_index=True, use_container_width=True)

    st.markdown("### Core accounting flow")
    st.code(
        "Gross production = Farm area × Yield per acre\n"
        "Saleable output = Gross production × (1 − post-harvest loss %)\n"
        "Revenue = Saleable output × Selling price\n"
        "Finance cost = Loan × Annual interest rate × Crop months / 12\n"
        "Accounting cost = Cultivation cash cost + Finance cost + Depreciation\n"
        "Accounting profit = Revenue − Accounting cost\n"
        "Break-even price = Accounting cost / Saleable output\n"
        "Harvest coverage = Revenue / (Loan principal + crop-cycle interest)",
        language=None,
    )

    st.markdown("### District crop and yield fallback")
    st.write(
        "FarmCredit no longer assumes that every supported crop is equally relevant in every district. "
        "It checks historical Government of India DES district-wise crop-production evidence and, when an exact "
        "district series is available, filters the crop list to crops historically recorded there. "
        "For a selected crop it calculates a recent historical yield benchmark from production and area. "
        "If a newer/reorganised district has no exact historical match, FarmCredit explicitly falls back to state-level evidence."
    )
    st.info(
        "Important: historical crop production tells us what has been recorded and gives a useful yield benchmark; "
        "it does not prove that the crop is suitable for every farm in that district, and it is not a current-year forecast. "
        "Farmer-specific yield evidence should override the starter benchmark."
    )

    st.markdown("### Location data approach")
    st.write(
        "FarmCredit loads a broad online State/District master and caches it for 24 hours so the dropdown "
        "is more complete than a small hardcoded list. The Government of India Local Government Directory (LGD) "
        "is treated as the formal reference for administrative geography."
    )

    st.markdown("### Market price approach")
    st.write(
        "Live mandi data is optional. "
        "The user can use the official MSP reference, manually enter a recent mandi / expected price, "
        "or provide a personal data.gov.in API key to request a live mandi observation. "
        "If the external API is slow or unavailable, the main accounting workflow still works normally."
    )

    st.markdown("### Reference prices")
    source_view = benchmarks[
        ["season", "msp_2026_27_rs_qtl", "price_source"]
    ].reset_index()
    source_view.columns = [
        "Crop",
        "Season",
        "MSP 2026–27 (₹/quintal)",
        "Source",
    ]
    st.dataframe(
        source_view,
        hide_index=True,
        use_container_width=True,
    )

    st.warning(
        "FarmCredit is an academic decision-support prototype. "
        "Strong / Moderate / Stressed classifications and the Indicative Supportable Loan "
        "are illustrative analytical rules, not formal bank sanction criteria."
    )
