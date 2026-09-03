from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from calculations import calculate_case, resilience_label, run_scenarios
from market_data import fetch_mandi_records, fetch_state_district_map


st.set_page_config(
    page_title="FarmCredit",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATA_PATH = Path(__file__).parent / "data" / "crop_benchmarks.csv"
benchmarks = pd.read_csv(DATA_PATH).set_index("crop")

GREEN = "#143E35"
GREEN_2 = "#2B6555"
CREAM = "#F7F4EC"
PAPER = "#FFFEFA"
INK = "#14211D"
MUTED = "#6B7872"
LINE = "#E6E0D2"
GOLD = "#C89B4A"
GOOD = "#2E7654"
WARN = "#B27624"
BAD = "#A34A40"


@st.cache_data(ttl=86400, show_spinner=False)
def location_map_cached():
    return fetch_state_district_map()


def money(x):
    x = float(x)
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 100000:
        return f"{sign}₹{x/100000:.2f}L"
    if x >= 1000:
        return f"{sign}₹{x/1000:.1f}K"
    return f"{sign}₹{x:,.0f}"


def metric_card(label, value, note="", accent=""):
    accent_style = f"border-top:3px solid {accent};" if accent else ""
    return f"""
    <div class="metric-card" style="{accent_style}">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      <div class="metric-note">{note}</div>
    </div>
    """


def load_crop_defaults():
    crop = st.session_state["crop"]
    row = benchmarks.loc[crop]
    st.session_state["yield_pa"] = float(row["default_yield_kg_acre"])
    st.session_state["price"] = float(row["msp_2026_27_rs_qtl"])
    st.session_state["loss"] = float(row["default_loss_pct"])
    st.session_state["months"] = int(row["default_cycle_months"])
    for key, col in [
        ("seed", "seed_rs_acre"),
        ("fertilizer", "fertilizer_rs_acre"),
        ("pesticides", "pesticides_rs_acre"),
        ("labour", "labour_rs_acre"),
        ("irrigation", "irrigation_rs_acre"),
        ("machinery", "machinery_rs_acre"),
        ("packaging", "packaging_rs_acre"),
        ("transport", "transport_rs_acre"),
        ("other", "other_rs_acre"),
    ]:
        st.session_state[key] = float(row[col])
    st.session_state.pop("market_result", None)


def on_state_change():
    st.session_state.pop("market_result", None)


def on_district_change():
    st.session_state.pop("market_result", None)


if "crop" not in st.session_state:
    st.session_state["crop"] = "Paddy (Common)"
    load_crop_defaults()

state_districts, location_source = location_map_cached()
states = sorted(state_districts.keys())

if "state" not in st.session_state:
    st.session_state["state"] = "Jharkhand" if "Jharkhand" in states else states[0]

district_options = state_districts.get(st.session_state["state"], ["Other / not listed"])
if "district" not in st.session_state or st.session_state["district"] not in district_options:
    preferred = "Ranchi" if "Ranchi" in district_options else district_options[0]
    st.session_state["district"] = preferred


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');

:root{
  --green:#143E35; --green2:#2B6555; --cream:#F7F4EC; --paper:#FFFEFA;
  --ink:#14211D; --muted:#6B7872; --line:#E6E0D2; --gold:#C89B4A;
}
html, body, [class*="css"] {font-family:"DM Sans",sans-serif;}
.stApp{
  background:
    radial-gradient(circle at 87% 3%, rgba(200,155,74,.10), transparent 25rem),
    linear-gradient(180deg,#FBF9F3 0%,#F5F1E7 100%);
  color:var(--ink);
}
.block-container{max-width:1320px;padding-top:1rem;padding-bottom:4rem;}
h1,h2,h3,h4{font-family:"Manrope",sans-serif!important;letter-spacing:-.03em;}
#MainMenu,footer{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent;}

.topbar{display:flex;justify-content:space-between;align-items:center;padding:.55rem 0 1rem;}
.brand{display:flex;align-items:center;gap:.72rem}
.brand-mark{
  width:44px;height:44px;border-radius:14px;background:linear-gradient(145deg,#12382F,#32705F);
  display:flex;align-items:center;justify-content:center;color:white;font-size:21px;
  box-shadow:0 12px 28px rgba(20,62,53,.18);
}
.brand-title{font-family:"Manrope",sans-serif;font-weight:800;color:var(--green);font-size:1.12rem}
.brand-sub{font-size:.76rem;color:var(--muted);margin-top:-2px}
.version{
  border:1px solid var(--line);background:rgba(255,255,255,.72);border-radius:999px;
  padding:.42rem .78rem;font-size:.76rem;color:var(--green);font-weight:700;
}
.hero{
  position:relative;overflow:hidden;border-radius:30px;padding:2.35rem 2.55rem;
  background:linear-gradient(118deg,#123B32 0%,#1A4C40 58%,#2A6353 100%);
  color:white;box-shadow:0 26px 70px rgba(20,62,53,.17);margin-bottom:1.2rem;
}
.hero:after{
  content:"";position:absolute;width:360px;height:360px;border-radius:50%;
  border:1px solid rgba(255,255,255,.13);right:-115px;top:-145px;
  box-shadow:0 0 0 46px rgba(255,255,255,.035),0 0 0 94px rgba(255,255,255,.022);
}
.eyebrow{font-size:.76rem;letter-spacing:.14em;text-transform:uppercase;font-weight:800;opacity:.70;margin-bottom:.7rem}
.hero h1{color:white!important;font-size:2.45rem;line-height:1.06;margin:0 0 .75rem;max-width:850px}
.hero p{font-size:1rem;line-height:1.65;color:rgba(255,255,255,.82);max-width:830px;margin:0}
.section-kicker{
  font-family:"Manrope",sans-serif;font-size:.76rem;font-weight:800;text-transform:uppercase;
  letter-spacing:.12em;color:var(--green);margin:.3rem 0 .55rem;
}
div[data-testid="stVerticalBlockBorderWrapper"]{
  background:rgba(255,254,250,.90)!important;border:1px solid var(--line)!important;
  border-radius:22px!important;box-shadow:0 12px 34px rgba(25,52,43,.05)!important;
}
div[data-testid="stWidgetLabel"] p{
  font-weight:700!important;color:#334640!important;font-size:.82rem!important;
}

/* Force all dropdowns to match the light dashboard instead of browser dark theme */
div[data-baseweb="select"] > div{
  background:#FFFFFF!important;
  border:1px solid #DDD7C9!important;
  color:#14211D!important;
  border-radius:12px!important;
}
div[data-baseweb="select"] span,
div[data-baseweb="select"] input{
  color:#14211D!important;
}
div[data-baseweb="popover"] ul{
  background:#FFFFFF!important;
}
div[data-baseweb="popover"] li{
  background:#FFFFFF!important;color:#14211D!important;
}
div[data-baseweb="popover"] li:hover{
  background:#EEF4F0!important;
}

div[data-testid="stNumberInput"]>div>div,
div[data-testid="stTextInput"]>div>div{
  border-radius:12px!important;background:#FFFFFF!important;color:#14211D!important;
  border-color:#DDD7C9!important;
}
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input{
  color:#14211D!important;background:#FFFFFF!important;
}
div[data-testid="stNumberInput"] button{background:#F2EFE6!important;color:#183D34!important;}

.metric-card{
  background:rgba(255,254,250,.97);border:1px solid var(--line);border-radius:19px;
  padding:1.03rem 1.1rem;min-height:126px;box-shadow:0 9px 28px rgba(25,52,43,.045);
}
.metric-label{font-size:.70rem;text-transform:uppercase;letter-spacing:.095em;color:var(--muted);font-weight:800}
.metric-value{font-family:"Manrope",sans-serif;font-size:1.64rem;font-weight:800;color:var(--green);margin:.36rem 0 .12rem;letter-spacing:-.04em}
.metric-note{font-size:.77rem;color:var(--muted);line-height:1.4}
.status-card{
  min-height:100%;border-radius:22px;padding:1.35rem 1.4rem;background:linear-gradient(145deg,#EDF5F0,#F9FBF8);
  border:1px solid #D6E7DC;
}
.status-label{font-size:.72rem;text-transform:uppercase;letter-spacing:.10em;color:#5B7168;font-weight:800}
.status-value{font-family:"Manrope",sans-serif;font-size:2.1rem;font-weight:800;color:#23573F;margin:.28rem 0 .45rem}
.status-copy{font-size:.86rem;line-height:1.58;color:#587067}
.stat-line{display:flex;justify-content:space-between;border-top:1px solid #DCE9E1;padding:.63rem 0;font-size:.83rem;color:#53675F}
.stat-line b{color:#193F34}
.note{
  border-left:3px solid var(--gold);background:#FFFDF6;padding:.82rem 1rem;
  border-radius:0 12px 12px 0;color:#53625D;font-size:.80rem;line-height:1.55;
}
.market-card{
  background:linear-gradient(145deg,#F5F9F6,#FFFEFA);border:1px solid #D7E5DC;
  border-radius:18px;padding:1rem 1.1rem;
}
.market-title{font-weight:800;font-family:"Manrope",sans-serif;color:#214F3D}
.market-big{font-family:"Manrope",sans-serif;font-weight:800;font-size:1.8rem;color:#173F35;margin:.2rem 0}
.market-meta{font-size:.78rem;color:#65736D;line-height:1.5}
.source-chip{
  display:inline-block;border:1px solid var(--line);background:#FFFDF8;border-radius:999px;
  padding:.3rem .58rem;font-size:.72rem;color:#53675F;margin:.1rem .25rem .1rem 0;
}
.light-table{
  width:100%;border-collapse:separate;border-spacing:0;border:1px solid #E5DFD1;
  border-radius:14px;overflow:hidden;background:#FFFEFA;font-size:.80rem;
}
.light-table th{background:#F0EEE6;color:#30463E;text-align:left;padding:.70rem .68rem;font-weight:800}
.light-table td{padding:.66rem .68rem;border-top:1px solid #ECE7DB;color:#293B35}
.light-table tr:nth-child(even) td{background:#FBF9F4}
.small-muted{font-size:.76rem;color:var(--muted);line-height:1.5}
div[data-testid="stTabs"] button p{font-weight:800!important;}
.stButton button, .stDownloadButton button{
  border-radius:12px!important;font-weight:800!important;
}

/* v0.3.1 — force closed dropdown controls and menus into light mode */
div[data-testid="stSelectbox"] div[role="combobox"]{
  background-color:#FFFFFF !important;
  color:#14211D !important;
  border:1px solid #D9D2C4 !important;
  box-shadow:none !important;
}
div[data-testid="stSelectbox"] div[role="combobox"] *{
  color:#14211D !important;
  fill:#36564B !important;
}
div[data-testid="stSelectbox"] div[role="combobox"]:focus-within{
  border-color:#6F9687 !important;
  box-shadow:0 0 0 2px rgba(43,101,85,.12) !important;
}
div[role="listbox"]{
  background:#FFFFFF !important;
  border:1px solid #D9D2C4 !important;
}
div[role="option"]{
  background:#FFFFFF !important;
  color:#14211D !important;
}
div[role="option"]:hover{
  background:#EEF4F0 !important;
  color:#14211D !important;
}
div[role="option"][aria-selected="true"]{
  background:#E4EFE9 !important;
  color:#143E35 !important;
}
div[data-testid="stButton"] > button{
  background:#173F35 !important;
  color:#FFFFFF !important;
  border:1px solid #173F35 !important;
}
div[data-testid="stButton"] > button:hover{
  background:#24594A !important;
  color:#FFFFFF !important;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="topbar">
  <div class="brand">
    <div class="brand-mark">🌾</div>
    <div>
      <div class="brand-title">FarmCredit</div>
      <div class="brand-sub">Agricultural financial intelligence</div>
    </div>
  </div>
  <div class="version">Accounting WAI · Prototype v0.3.1</div>
</div>
<div class="hero">
  <div class="eyebrow">Market-aware crop-cycle assessment</div>
  <h1>Turn farm economics and market context into a clearer lending conversation.</h1>
  <p>Use location-aware inputs, official MSP references, recent mandi observations, accounting break-even and stress testing in one explainable dashboard.</p>
</div>
""", unsafe_allow_html=True)

assessment_tab, method_tab = st.tabs(["Assessment dashboard", "Methodology & sources"])

with assessment_tab:
    st.markdown('<div class="section-kicker">01 · Farm location, crop & market</div>', unsafe_allow_html=True)

    top_left, top_right = st.columns([1.05, 1.15], gap="large")

    with top_left:
        with st.container(border=True):
            st.markdown("### Location & crop")

            state = st.selectbox(
                "State / UT",
                states,
                key="state",
                on_change=on_state_change,
            )

            district_options = state_districts.get(state, ["Other / not listed"])
            if st.session_state.get("district") not in district_options:
                st.session_state["district"] = district_options[0]

            district = st.selectbox(
                "District / market area",
                district_options,
                key="district",
                on_change=on_district_change,
            )

            crop = st.selectbox(
                "Crop",
                benchmarks.index.tolist(),
                key="crop",
                on_change=load_crop_defaults,
            )

            row = benchmarks.loc[crop]
            st.markdown(
                f'<span class="source-chip">{row["season"]} crop</span>'
                f'<span class="source-chip">2026–27 MSP: ₹{row["msp_2026_27_rs_qtl"]:,.0f}/qtl</span>'
                f'<span class="source-chip">{location_source}</span>',
                unsafe_allow_html=True,
            )

            st.caption("District choices are location lookups. Actual mandi coverage depends on the market-price dataset.")

    with top_right:
        with st.container(border=True):
            st.markdown("### Recent mandi market data")
            st.caption("Connect to the Government of India's AGMARKNET/data.gov.in feed using your own free API key.")

            api_key = st.text_input(
                "data.gov.in API key",
                type="password",
                placeholder="Paste API key here",
                help="The key is used for this session only and is not written to the repository by this app.",
            )

            fetch_clicked = st.button("Fetch recent mandi price", use_container_width=True)

            if fetch_clicked:
                with st.spinner("Checking recent mandi observations..."):
                    st.session_state["market_result"] = fetch_mandi_records(
                        api_key=api_key,
                        state=state,
                        district=district,
                        crop=crop,
                    )

            market_result = st.session_state.get("market_result")

            if market_result and market_result.get("ok"):
                latest = market_result["latest"]
                modal = float(latest.get("modal_price", 0) or 0)
                minp = float(latest.get("min_price", 0) or 0)
                maxp = float(latest.get("max_price", 0) or 0)
                market = latest.get("market", "—")
                arrival = latest.get("arrival_date", "—")
                commodity = latest.get("commodity", crop)

                st.markdown(
                    f"""
                    <div class="market-card">
                      <div class="market-title">Latest matched observation</div>
                      <div class="market-big">₹{modal:,.0f}/qtl</div>
                      <div class="market-meta">
                        {commodity} · {market}<br>
                        {district}, {state} · {arrival}<br>
                        Range: ₹{minp:,.0f}–₹{maxp:,.0f}/qtl
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("Use this modal price in the financial model", use_container_width=True):
                    st.session_state["price"] = modal
                    st.rerun()

            elif market_result:
                kind = market_result.get("kind", "")
                message = market_result.get("message", "No market data loaded.")
                if kind == "timeout":
                    st.warning(message)
                elif kind in {"no_records", "no_crop_match"}:
                    st.info(message)
                else:
                    st.error(message)
            else:
                st.markdown(
                    '<div class="note">Until an API key is connected, the financial model uses the editable MSP benchmark as the starting selling-price assumption.</div>',
                    unsafe_allow_html=True,
                )

    st.markdown('<div class="section-kicker" style="margin-top:1rem">02 · Farm assumptions & financing</div>', unsafe_allow_html=True)

    left, right = st.columns([0.9, 1.35], gap="large")

    with left:
        with st.container(border=True):
            st.markdown("### Production & financing")

            x1, x2 = st.columns(2)
            with x1:
                area = st.number_input("Land area (acres)", min_value=0.1, value=3.0, step=0.5)
            with x2:
                yield_pa = st.number_input("Expected yield (kg/acre)", min_value=1.0, step=50.0, key="yield_pa")

            x3, x4 = st.columns(2)
            with x3:
                price = st.number_input("Expected selling price (₹/quintal)", min_value=1.0, step=10.0, key="price")
            with x4:
                loss = st.number_input("Post-harvest loss (%)", min_value=0.0, max_value=50.0, step=0.5, key="loss")

            st.caption("Expected selling price remains editable even when market data is available.")

            f1, f2 = st.columns(2)
            with f1:
                loan = st.number_input("Loan requested (₹)", min_value=0.0, value=45000.0, step=5000.0)
            with f2:
                rate = st.number_input("Annual interest rate (%)", min_value=0.0, value=7.0, step=0.25)

            months = st.number_input("Crop cycle (months)", min_value=1, max_value=24, step=1, key="months")

    with right:
        with st.container(border=True):
            st.markdown("### Cultivation cost model")
            st.caption("Starter figures are illustrative and editable; use farmer-specific or locally validated costs wherever available.")

            a, b, c = st.columns(3)
            with a:
                seed = st.number_input("Seed (₹/acre)", min_value=0.0, step=100.0, key="seed")
                fertilizer = st.number_input("Fertilizer (₹/acre)", min_value=0.0, step=100.0, key="fertilizer")
                pesticides = st.number_input("Pesticides (₹/acre)", min_value=0.0, step=100.0, key="pesticides")
            with b:
                labour = st.number_input("Labour (₹/acre)", min_value=0.0, step=100.0, key="labour")
                irrigation = st.number_input("Irrigation (₹/acre)", min_value=0.0, step=100.0, key="irrigation")
                machinery = st.number_input("Machinery (₹/acre)", min_value=0.0, step=100.0, key="machinery")
            with c:
                packaging = st.number_input("Packaging (₹/acre)", min_value=0.0, step=100.0, key="packaging")
                transport = st.number_input("Transport (₹/acre)", min_value=0.0, step=100.0, key="transport")
                other = st.number_input("Other costs (₹/acre)", min_value=0.0, step=100.0, key="other")

            with st.expander("Advanced accounting assumptions"):
                depreciation = st.number_input(
                    "Depreciation allocated to this crop cycle (₹)",
                    min_value=0.0,
                    value=3000.0,
                    step=500.0,
                )

            cost_items = {
                "Seed": seed, "Fertilizer": fertilizer, "Pesticides": pesticides,
                "Labour": labour, "Irrigation": irrigation, "Machinery": machinery,
                "Packaging": packaging, "Transport": transport, "Other": other,
            }
            preview_total = sum(cost_items.values())
            st.markdown(
                f'<div class="note">Cash cultivation budget: <b>₹{preview_total:,.0f}/acre</b> · '
                f'<b>₹{preview_total*area:,.0f}</b> for {area:.1f} acres before interest and depreciation.</div>',
                unsafe_allow_html=True,
            )

    base_inputs = {
        "area": area,
        "yield_per_acre": yield_pa,
        "loss_pct": loss,
        "price_qtl": price,
        "cost_items_per_acre": cost_items,
        "loan": loan,
        "annual_rate_pct": rate,
        "months": months,
        "depreciation": depreciation,
    }
    r = calculate_case(**base_inputs)
    scenario_rows = run_scenarios(base_inputs)
    status, status_copy = resilience_label(r, scenario_rows)

    st.markdown('<div class="section-kicker" style="margin-top:1.4rem">03 · Financial overview</div>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4, gap="medium")
    with m1:
        st.markdown(metric_card("Expected revenue", money(r["revenue"]), f'{r["saleable_qtl"]:.1f} qtl saleable output', GREEN_2), unsafe_allow_html=True)
    with m2:
        st.markdown(metric_card("Accounting cost", money(r["total_accounting_cost"]), f'{money(r["cash_cost_per_acre"])}/acre cash cost', GOLD), unsafe_allow_html=True)
    with m3:
        st.markdown(metric_card("Accounting profit", money(r["accounting_profit"]), f'{r["margin"]:.1f}% profit margin', GOOD if r["accounting_profit"] >= 0 else BAD), unsafe_allow_html=True)
    with m4:
        st.markdown(metric_card("Harvest coverage", f'{r["harvest_coverage"]:.2f}×', "Revenue ÷ principal + interest", GREEN_2), unsafe_allow_html=True)

    m5, m6, m7, m8 = st.columns(4, gap="medium")
    with m5:
        st.markdown(metric_card("Break-even price", f'₹{r["break_even_price"]:,.0f}/qtl', f'{r["price_cushion"]:.1f}% modeled price cushion'), unsafe_allow_html=True)
    with m6:
        st.markdown(metric_card("Break-even yield", f'{r["break_even_yield"]:,.0f} kg/ac', f'{r["yield_cushion"]:.1f}% modeled yield cushion'), unsafe_allow_html=True)
    with m7:
        st.markdown(metric_card("Cash profit", money(r["cash_profit"]), "Before depreciation"), unsafe_allow_html=True)
    with m8:
        st.markdown(metric_card("Indicative supportable loan", money(r["indicative_max_supportable_loan"]), "Capped by modeled cash cost at 1.25× target coverage"), unsafe_allow_html=True)

    if market_result and market_result.get("ok"):
        latest_modal = float(market_result["latest"].get("modal_price", 0) or 0)
        msp = float(row["msp_2026_27_rs_qtl"])
        delta_msp = (latest_modal - msp) / msp * 100 if msp else 0
        delta_be = (latest_modal - r["break_even_price"]) / latest_modal * 100 if latest_modal else 0
        st.markdown(
            f'<div class="note" style="margin-top:.65rem"><b>Market context:</b> Latest matched modal price is '
            f'<b>{delta_msp:+.1f}% vs MSP</b> and provides a modeled <b>{delta_be:.1f}% cushion vs accounting break-even</b>.</div>',
            unsafe_allow_html=True,
        )

    if r["excess_financing"] > 0:
        st.warning(
            f"Requested loan exceeds modeled cash cultivation cost by {money(r['excess_financing'])}. "
            "Confirm the purpose of the additional crop-cycle borrowing."
        )

    st.markdown('<div class="section-kicker" style="margin-top:1.4rem">04 · Resilience & market structure</div>', unsafe_allow_html=True)

    c_left, c_mid, c_right = st.columns([0.9, 1.05, 1.05], gap="large")

    with c_left:
        st.markdown(
            f"""
            <div class="status-card">
              <div class="status-label">Indicative financial resilience</div>
              <div class="status-value">{status}</div>
              <div class="status-copy">{status_copy}</div>
              <div class="stat-line"><span>Price cushion</span><b>{r["price_cushion"]:.1f}%</b></div>
              <div class="stat-line"><span>Yield cushion</span><b>{r["yield_cushion"]:.1f}%</b></div>
              <div class="stat-line"><span>Own contribution</span><b>{money(r["own_contribution"])}</b></div>
              <div class="stat-line"><span>Repayment obligation</span><b>{money(r["repayment_obligation"])}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_mid:
        labels, values = list(cost_items.keys()), list(cost_items.values())
        fig_cost = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.66, textinfo="none",
            hovertemplate="%{label}<br>₹%{value:,.0f}/acre<extra></extra>",
            marker=dict(colors=["#173F35","#2C6555","#4C806F","#78A08F","#A7B9A8","#C89B4A","#D8B96E","#B7A88F","#8D8A7D"]),
        ))
        fig_cost.add_annotation(text=f"<b>₹{sum(values):,.0f}</b><br><span style='font-size:11px'>per acre</span>", showarrow=False, font=dict(size=17, color=INK))
        fig_cost.update_layout(title=dict(text="Cost composition", x=.02, xanchor="left", font=dict(size=17,color=INK)),
                               margin=dict(l=10,r=10,t=55,b=10),height=320,paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)",legend=dict(font=dict(size=10,color=MUTED),orientation="h",y=-.05))
        st.plotly_chart(fig_cost, use_container_width=True, config={"displayModeBar":False})

    with c_right:
        fig_be = go.Figure(go.Bar(
            y=["Selling price","Break-even"],
            x=[price,r["break_even_price"]],
            orientation="h",
            marker_color=[GREEN_2,GOLD],
            text=[f"₹{price:,.0f}",f"₹{r['break_even_price']:,.0f}"],
            textposition="outside",
            hovertemplate="%{y}: ₹%{x:,.0f}/qtl<extra></extra>",
        ))
        fig_be.update_layout(title=dict(text="Price vs accounting break-even",x=.02,xanchor="left",font=dict(size=17,color=INK)),
                             xaxis=dict(title="₹ per quintal",gridcolor="#ECE7DA",zeroline=False),
                             yaxis=dict(title=""),margin=dict(l=10,r=35,t=55,b=35),height=320,
                             paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED))
        st.plotly_chart(fig_be,use_container_width=True,config={"displayModeBar":False})

    if market_result and market_result.get("ok") and market_result.get("history"):
        history = pd.DataFrame(market_result["history"])
        if "_date" in history.columns and "modal_price" in history.columns:
            history["_date"] = pd.to_datetime(history["_date"], errors="coerce")
            history["modal_price"] = pd.to_numeric(history["modal_price"], errors="coerce")
            history = history.dropna(subset=["_date","modal_price"])
            if len(history) >= 2:
                fig_market = go.Figure()
                fig_market.add_trace(go.Scatter(
                    x=history["_date"],y=history["modal_price"],mode="lines+markers",
                    line=dict(color=GREEN_2,width=3),marker=dict(size=6),
                    hovertemplate="%{x|%d %b %Y}<br>Modal ₹%{y:,.0f}/qtl<extra></extra>"
                ))
                fig_market.add_hline(y=float(row["msp_2026_27_rs_qtl"]),line_dash="dash",line_color=GOLD,
                                     annotation_text="MSP reference")
                fig_market.update_layout(title=dict(text="Recent matched mandi observations",x=.01,xanchor="left",font=dict(size=18,color=INK)),
                                         yaxis=dict(title="₹ per quintal",gridcolor="#ECE7DA"),xaxis=dict(title=""),
                                         height=340,margin=dict(l=10,r=10,t=55,b=25),
                                         paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED))
                st.plotly_chart(fig_market,use_container_width=True,config={"displayModeBar":False})

    st.markdown('<div class="section-kicker" style="margin-top:1.2rem">05 · Scenario stress test</div>', unsafe_allow_html=True)

    scenario_df = pd.DataFrame(scenario_rows)
    fig_stress = go.Figure(go.Bar(
        x=scenario_df["Scenario"],y=scenario_df["Accounting profit"],
        marker_color=[GREEN_2 if v>=0 else BAD for v in scenario_df["Accounting profit"]],
        text=[money(v) for v in scenario_df["Accounting profit"]],textposition="outside",
        hovertemplate="%{x}<br>Accounting profit: ₹%{y:,.0f}<extra></extra>",
    ))
    fig_stress.add_hline(y=0,line_width=1,line_color="#8D8A7D")
    fig_stress.update_layout(title=dict(text="Profit resilience across price and yield shocks",x=.01,xanchor="left",font=dict(size=18,color=INK)),
                             yaxis=dict(title="Accounting profit (₹)",gridcolor="#ECE7DA"),xaxis=dict(title=""),
                             margin=dict(l=10,r=10,t=55,b=20),height=350,paper_bgcolor="rgba(0,0,0,0)",
                             plot_bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED))
    st.plotly_chart(fig_stress,use_container_width=True,config={"displayModeBar":False})

    table_rows = []
    for rr in scenario_rows:
        ychg = "Base" if rr["Yield change"] == 0 else "{:+.0%}".format(rr["Yield change"])
        pchg = "Base" if rr["Price change"] == 0 else "{:+.0%}".format(rr["Price change"])
        table_rows.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{:.1f}%</td><td>{:.2f}×</td></tr>".format(
                rr["Scenario"], ychg, pchg, money(rr["Revenue"]), money(rr["Accounting profit"]),
                rr["Margin"], rr["Harvest coverage"]
            )
        )
    st.markdown(
        "<table class='light-table'><thead><tr>"
        "<th>Scenario</th><th>Yield</th><th>Price</th><th>Revenue</th>"
        "<th>Accounting profit</th><th>Margin</th><th>Coverage</th>"
        "</tr></thead><tbody>" + "".join(table_rows) + "</tbody></table>",
        unsafe_allow_html=True,
    )

    export_df = scenario_df.copy()
    st.download_button("Download scenario analysis (CSV)",
                       data=export_df.to_csv(index=False).encode("utf-8"),
                       file_name="farmcredit_scenario_analysis.csv",
                       mime="text/csv")

    st.markdown(
        "<div class='note' style='margin-top:.7rem'><b>Academic-use notice.</b> "
        "FarmCredit is an explainable accounting and scenario-analysis prototype. "
        "It does not approve or reject credit, predict future crop prices, or replace lender underwriting, "
        "KYC, bureau, collateral, field-verification, policy or regulatory checks.</div>",
        unsafe_allow_html=True,
    )

with method_tab:
    st.markdown("## Methodology & sources")
    st.write(
        "FarmCredit separates farmer-entered assumptions from external reference data. "
        "The accounting engine remains transparent and editable; market observations supplement rather than replace the farmer's own expected selling-price assumption."
    )

    st.markdown("### Accounting flow")
    st.code(
        "Gross production → Saleable output → Revenue\n"
        "Cash cultivation cost + Finance cost + Depreciation → Accounting cost\n"
        "Revenue − Accounting cost → Accounting profit\n"
        "Accounting cost ÷ Saleable output → Break-even price\n"
        "Revenue ÷ (Loan principal + crop-cycle interest) → Harvest repayment coverage",
        language=None,
    )

    st.markdown("### External data")
    st.markdown(
        "- **Mandi prices:** Government of India Open Government Data / AGMARKNET resource "
        "`9ef84268-d588-465a-a308-a864a43d0070`.\n"
        "- **Location taxonomy:** state/district dropdowns use an LGD-derived district index; "
        "the Government's Local Government Directory remains the authoritative administrative reference.\n"
        "- **MSP reference values:** Government of India Press Information Bureau, Kharif and Rabi 2026–27 announcements."
    )

    st.info(
        "A mandi modal price is an observed wholesale-market price, not a guaranteed farmer realization. "
        "The app always keeps the expected selling price editable."
    )
