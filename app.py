import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="FarmCredit",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------
# Design system / CSS
# ---------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');

:root {
    --fc-green: #173F35;
    --fc-green-2: #24594A;
    --fc-cream: #F6F3EA;
    --fc-paper: #FCFBF7;
    --fc-ink: #17221E;
    --fc-muted: #68756F;
    --fc-line: #E6E1D4;
    --fc-gold: #C59542;
    --fc-good: #2D7A55;
    --fc-warn: #A97524;
    --fc-bad: #A8483C;
}

html, body, [class*="css"] {
    font-family: "DM Sans", sans-serif;
}
.stApp {
    background:
        radial-gradient(circle at 92% 4%, rgba(197,149,66,0.10), transparent 24rem),
        linear-gradient(180deg, #F9F7F0 0%, #F5F2E8 100%);
    color: var(--fc-ink);
}
.block-container {
    max-width: 1240px;
    padding-top: 1.4rem;
    padding-bottom: 4rem;
}
h1, h2, h3, h4 {
    font-family: "Manrope", sans-serif !important;
    letter-spacing: -0.025em;
}
#MainMenu, footer {visibility: hidden;}
header[data-testid="stHeader"] {background: rgba(0,0,0,0);}

.fc-nav {
    display:flex; align-items:center; justify-content:space-between;
    padding: 0.65rem 0 1.25rem 0;
}
.fc-brand {
    display:flex; align-items:center; gap:0.75rem;
}
.fc-logo {
    width:42px; height:42px; border-radius:13px;
    background: linear-gradient(145deg, #173F35, #2D6B59);
    display:flex; align-items:center; justify-content:center;
    color:white; font-size:22px;
    box-shadow: 0 10px 28px rgba(23,63,53,.18);
}
.fc-brandname {
    font-family:"Manrope", sans-serif; font-weight:800; font-size:1.12rem;
    color:var(--fc-green);
}
.fc-tagline {font-size:.78rem; color:var(--fc-muted); margin-top:-2px;}
.fc-pill {
    border:1px solid var(--fc-line); background:rgba(255,255,255,.58);
    color:var(--fc-green); border-radius:999px;
    padding:.45rem .75rem; font-size:.79rem; font-weight:600;
}
.fc-hero {
    background:
      linear-gradient(120deg, rgba(23,63,53,.97), rgba(36,89,74,.94)),
      linear-gradient(120deg, #173F35, #24594A);
    color:#fff;
    border-radius:28px;
    padding:2.1rem 2.25rem;
    box-shadow:0 24px 70px rgba(23,63,53,.18);
    overflow:hidden;
    position:relative;
    margin-bottom:1.25rem;
}
.fc-hero:after {
    content:"";
    position:absolute;
    width:320px; height:320px; border-radius:50%;
    border:1px solid rgba(255,255,255,.14);
    right:-105px; top:-130px;
    box-shadow:0 0 0 42px rgba(255,255,255,.035), 0 0 0 86px rgba(255,255,255,.025);
}
.fc-eyebrow {
    font-size:.78rem; letter-spacing:.13em; text-transform:uppercase;
    opacity:.72; font-weight:700; margin-bottom:.55rem;
}
.fc-hero h1 {
    color:#fff !important;
    max-width:760px;
    font-size:2.28rem;
    line-height:1.08;
    margin:0 0 .65rem 0;
}
.fc-hero p {
    max-width:780px; font-size:1rem; line-height:1.65;
    color:rgba(255,255,255,.82); margin:0;
}
.fc-section-label {
    font-family:"Manrope", sans-serif; font-size:.82rem; font-weight:800;
    color:var(--fc-green); text-transform:uppercase; letter-spacing:.10em;
    margin: .35rem 0 .65rem 0;
}
div[data-testid="stForm"] {
    background:rgba(252,251,247,.90);
    border:1px solid var(--fc-line);
    border-radius:22px;
    padding:1.1rem 1.1rem .5rem 1.1rem;
    box-shadow:0 12px 34px rgba(29,50,43,.055);
}
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input {
    border-radius:12px !important;
}
div[data-baseweb="select"] > div {
    border-radius:12px !important;
}
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    width:100%;
    border:0;
    border-radius:13px;
    background:linear-gradient(135deg, #173F35, #24594A);
    color:white;
    font-weight:800;
    min-height:3.05rem;
    box-shadow:0 10px 22px rgba(23,63,53,.16);
}
div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
    color:white;
    border:0;
    transform: translateY(-1px);
}
.fc-card {
    background:rgba(252,251,247,.93);
    border:1px solid var(--fc-line);
    border-radius:20px;
    padding:1.15rem 1.2rem 1.05rem 1.2rem;
    box-shadow:0 11px 30px rgba(29,50,43,.05);
    min-height:132px;
}
.fc-card-label {
    color:var(--fc-muted); font-weight:700; font-size:.74rem;
    text-transform:uppercase; letter-spacing:.08em;
}
.fc-card-value {
    color:var(--fc-green); font-family:"Manrope", sans-serif;
    font-size:1.67rem; font-weight:800; margin:.42rem 0 .12rem 0;
    letter-spacing:-.04em;
}
.fc-card-note {
    color:var(--fc-muted); font-size:.78rem;
}
.fc-panel {
    background:rgba(252,251,247,.93);
    border:1px solid var(--fc-line);
    border-radius:22px;
    padding:1.25rem 1.35rem;
    box-shadow:0 11px 30px rgba(29,50,43,.05);
}
.fc-status {
    border-radius:18px;
    padding:1rem 1.15rem;
    background:#EEF5EF;
    border:1px solid #D8E8DD;
}
.fc-status-title {font-weight:800; color:#286446; font-family:"Manrope", sans-serif;}
.fc-status-big {font-size:1.55rem; font-weight:800; color:#22533E; margin-top:.15rem;}
.fc-mini {font-size:.82rem; color:var(--fc-muted); line-height:1.55;}
.fc-disclaimer {
    border-left:3px solid var(--fc-gold);
    background:rgba(255,255,255,.55);
    padding:.8rem 1rem;
    border-radius:0 12px 12px 0;
    font-size:.8rem; color:var(--fc-muted);
}
div[data-testid="stExpander"] {
    border:1px solid var(--fc-line);
    border-radius:16px;
    background:rgba(252,251,247,.74);
}
div[data-testid="stDataFrame"] {
    border:1px solid var(--fc-line);
    border-radius:16px;
    overflow:hidden;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Helpers
# ---------------------------
def inr(x):
    if abs(x) >= 100000:
        return f"₹{x/100000:.2f}L"
    if abs(x) >= 1000:
        return f"₹{x/1000:.1f}K"
    return f"₹{x:,.0f}"

def metric_card(label, value, note=""):
    return f"""
    <div class="fc-card">
      <div class="fc-card-label">{label}</div>
      <div class="fc-card-value">{value}</div>
      <div class="fc-card-note">{note}</div>
    </div>
    """

def calc(area, yield_per_acre, loss_pct, price_qtl, cash_cost_per_acre,
         loan, annual_rate_pct, months, depreciation):
    gross_kg = area * yield_per_acre
    saleable_kg = gross_kg * (1 - loss_pct/100)
    qtl = saleable_kg / 100
    revenue = qtl * price_qtl
    cash_cost = area * cash_cost_per_acre
    interest = loan * annual_rate_pct/100 * months/12
    total_cost = cash_cost + interest + depreciation
    profit = revenue - total_cost
    margin = (profit / revenue * 100) if revenue else 0
    break_even_price = (total_cost / qtl) if qtl else 0
    price_cushion = ((price_qtl - break_even_price) / price_qtl * 100) if price_qtl else 0
    repayment = loan + interest
    coverage = (revenue / repayment) if repayment else 0
    be_saleable_kg = total_cost / (price_qtl/100) if price_qtl else 0
    be_gross_kg = be_saleable_kg / (1 - loss_pct/100) if loss_pct < 100 else 0
    be_yield = be_gross_kg / area if area else 0
    yield_cushion = ((yield_per_acre - be_yield) / yield_per_acre * 100) if yield_per_acre else 0
    cash_profit = revenue - cash_cost - interest
    return {
        "gross_kg": gross_kg,
        "saleable_kg": saleable_kg,
        "qtl": qtl,
        "revenue": revenue,
        "cash_cost": cash_cost,
        "interest": interest,
        "total_cost": total_cost,
        "profit": profit,
        "margin": margin,
        "break_even_price": break_even_price,
        "price_cushion": price_cushion,
        "coverage": coverage,
        "be_yield": be_yield,
        "yield_cushion": yield_cushion,
        "cash_profit": cash_profit,
    }

# ---------------------------
# Top navigation + hero
# ---------------------------
st.markdown("""
<div class="fc-nav">
  <div class="fc-brand">
    <div class="fc-logo">🌾</div>
    <div>
      <div class="fc-brandname">FarmCredit</div>
      <div class="fc-tagline">Agricultural financial intelligence</div>
    </div>
  </div>
  <div class="fc-pill">Academic prototype · v0.1</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="fc-hero">
  <div class="fc-eyebrow">Crop-cycle decision support</div>
  <h1>Turn farm economics into a clear lending conversation.</h1>
  <p>
    Estimate profitability, accounting break-even, repayment coverage and downside resilience
    from a transparent set of farm assumptions.
  </p>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# Input form
# ---------------------------
st.markdown('<div class="fc-section-label">01 · Build the farm case</div>', unsafe_allow_html=True)

with st.form("farm_form"):
    c1, c2, c3 = st.columns(3, gap="large")

    with c1:
        st.markdown("#### Farm & crop")
        state = st.selectbox("State", ["Jharkhand"], index=0)
        district = st.selectbox("District", ["Ranchi"], index=0)
        crop = st.selectbox("Crop", ["Paddy (Common)"], index=0)
        area = st.number_input("Land area (acres)", min_value=0.1, value=3.0, step=0.5)

    with c2:
        st.markdown("#### Yield & market")
        yield_pa = st.number_input("Expected yield (kg/acre)", min_value=1.0, value=1200.0, step=50.0)
        price = st.number_input("Expected selling price (₹/quintal)", min_value=1.0, value=2441.0, step=10.0)
        loss = st.number_input("Post-harvest loss (%)", min_value=0.0, max_value=50.0, value=5.0, step=1.0)
        st.caption("₹2,441/qtl is the initial Paddy (Common) MSP benchmark used in this prototype.")

    with c3:
        st.markdown("#### Financing")
        loan = st.number_input("Loan requested (₹)", min_value=0.0, value=45000.0, step=5000.0)
        rate = st.number_input("Annual interest rate (%)", min_value=0.0, value=7.0, step=0.25)
        months = st.number_input("Crop cycle (months)", min_value=1, max_value=24, value=6, step=1)
        st.caption("The interest rate remains editable because actual lender terms may differ.")

    st.markdown("#### Cultivation costs")
    k1, k2, k3 = st.columns(3, gap="large")
    with k1:
        seed = st.number_input("Seed (₹/acre)", min_value=0.0, value=1200.0, step=100.0)
        fertilizer = st.number_input("Fertilizer (₹/acre)", min_value=0.0, value=3500.0, step=100.0)
        pesticide = st.number_input("Pesticides (₹/acre)", min_value=0.0, value=1000.0, step=100.0)
    with k2:
        labour = st.number_input("Labour (₹/acre)", min_value=0.0, value=5500.0, step=100.0)
        irrigation = st.number_input("Irrigation (₹/acre)", min_value=0.0, value=1500.0, step=100.0)
        machinery = st.number_input("Machinery (₹/acre)", min_value=0.0, value=3000.0, step=100.0)
    with k3:
        packaging = st.number_input("Packaging (₹/acre)", min_value=0.0, value=600.0, step=100.0)
        transport = st.number_input("Transport (₹/acre)", min_value=0.0, value=800.0, step=100.0)
        other = st.number_input("Other operating costs (₹/acre)", min_value=0.0, value=900.0, step=100.0)

    with st.expander("Advanced accounting assumptions"):
        depreciation = st.number_input(
            "Depreciation allocated to this crop cycle (₹)",
            min_value=0.0,
            value=3000.0,
            step=500.0,
            help="Non-cash accounting cost allocated to the crop cycle."
        )

    submitted = st.form_submit_button("Analyse farm finances  →")

cash_cost_pa = seed + fertilizer + pesticide + labour + irrigation + machinery + packaging + transport + other
r = calc(area, yield_pa, loss, price, cash_cost_pa, loan, rate, months, depreciation)

# ---------------------------
# Results
# ---------------------------
st.markdown('<div class="fc-section-label" style="margin-top:1.5rem;">02 · Financial overview</div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4, gap="medium")
with m1:
    st.markdown(metric_card("Expected revenue", inr(r["revenue"]), f"{r['qtl']:.1f} qtl saleable output"), unsafe_allow_html=True)
with m2:
    st.markdown(metric_card("Accounting cost", inr(r["total_cost"]), f"{inr(cash_cost_pa)}/acre cash cost"), unsafe_allow_html=True)
with m3:
    st.markdown(metric_card("Accounting profit", inr(r["profit"]), f"{r['margin']:.1f}% profit margin"), unsafe_allow_html=True)
with m4:
    st.markdown(metric_card("Harvest coverage", f"{r['coverage']:.2f}×", "Revenue ÷ principal + interest"), unsafe_allow_html=True)

m5, m6, m7 = st.columns(3, gap="medium")
with m5:
    st.markdown(metric_card("Break-even price", f"₹{r['break_even_price']:,.0f}/qtl", f"{r['price_cushion']:.1f}% modeled price cushion"), unsafe_allow_html=True)
with m6:
    st.markdown(metric_card("Break-even yield", f"{r['be_yield']:,.0f} kg/ac", f"{r['yield_cushion']:.1f}% modeled yield cushion"), unsafe_allow_html=True)
with m7:
    st.markdown(metric_card("Cash profit", inr(r["cash_profit"]), "Before depreciation"), unsafe_allow_html=True)

st.markdown('<div class="fc-section-label" style="margin-top:1.5rem;">03 · Resilience view</div>', unsafe_allow_html=True)

left, right = st.columns([1, 1.45], gap="large")

# Transparent academic status rules
if r["profit"] > 0 and r["coverage"] >= 1.25 and r["price_cushion"] >= 20:
    status = "Strong"
    status_note = "Positive accounting profit, coverage ≥ 1.25× and a price cushion of at least 20% in the base case."
elif r["profit"] > 0 and r["coverage"] >= 1.05:
    status = "Moderate"
    status_note = "The base case is positive, but one or more resilience measures are comparatively thin."
else:
    status = "Stressed"
    status_note = "The base case shows weak coverage and/or negative modeled profitability."

with left:
    st.markdown(f"""
    <div class="fc-panel">
      <div class="fc-card-label">Indicative financial resilience</div>
      <div class="fc-status" style="margin-top:.7rem;">
        <div class="fc-status-title">Current assessment</div>
        <div class="fc-status-big">{status}</div>
      </div>
      <div class="fc-mini" style="margin-top:.85rem;">{status_note}</div>
      <div class="fc-mini" style="margin-top:.65rem;">
        These are transparent academic rules, not a bank's lending policy or a credit decision.
      </div>
    </div>
    """, unsafe_allow_html=True)

with right:
    cost_df = pd.DataFrame({
        "Cost item": ["Seed","Fertilizer","Pesticides","Labour","Irrigation","Machinery","Packaging","Transport","Other"],
        "₹ per acre": [seed,fertilizer,pesticide,labour,irrigation,machinery,packaging,transport,other],
    })
    st.markdown("#### Cost composition")
    st.bar_chart(cost_df.set_index("Cost item"), horizontal=True)

# ---------------------------
# Stress test
# ---------------------------
st.markdown('<div class="fc-section-label" style="margin-top:1.5rem;">04 · Scenario stress test</div>', unsafe_allow_html=True)

scenarios = [
    ("Strong market", 0.10, 0.10),
    ("Base case", 0.00, 0.00),
    ("Price stress", 0.00, -0.10),
    ("Yield stress", -0.10, 0.00),
    ("Moderate stress", -0.10, -0.10),
    ("Severe stress", -0.20, -0.20),
]

rows = []
for name, ychg, pchg in scenarios:
    sr = calc(
        area,
        yield_pa * (1 + ychg),
        loss,
        price * (1 + pchg),
        cash_cost_pa,
        loan,
        rate,
        months,
        depreciation,
    )
    rows.append({
        "Scenario": name,
        "Yield change": f"{ychg:+.0%}" if ychg else "Base",
        "Price change": f"{pchg:+.0%}" if pchg else "Base",
        "Revenue": round(sr["revenue"]),
        "Accounting profit": round(sr["profit"]),
        "Margin": f"{sr['margin']:.1f}%",
        "Harvest coverage": f"{sr['coverage']:.2f}×",
    })

scenario_df = pd.DataFrame(rows)
st.dataframe(
    scenario_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Revenue": st.column_config.NumberColumn(format="₹%d"),
        "Accounting profit": st.column_config.NumberColumn(format="₹%d"),
    },
)

st.markdown("""
<div class="fc-disclaimer">
<b>Academic-use notice.</b> FarmCredit is a transparent accounting and scenario-analysis prototype.
It does not approve or reject credit, predict future crop prices, or replace a lender's underwriting,
field verification, KYC, collateral, bureau, policy or regulatory checks.
</div>
""", unsafe_allow_html=True)
