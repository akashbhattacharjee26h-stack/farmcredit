from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from calculations import calculate_case, resilience_label, run_scenarios


st.set_page_config(
    page_title="FarmCredit",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATA_PATH = Path(__file__).parent / "data" / "crop_benchmarks.csv"
benchmarks = pd.read_csv(DATA_PATH)
benchmarks = benchmarks.set_index("crop")

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
SOFT_GREEN = "#EAF2ED"


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
    st.session_state["seed"] = float(row["seed_rs_acre"])
    st.session_state["fertilizer"] = float(row["fertilizer_rs_acre"])
    st.session_state["pesticides"] = float(row["pesticides_rs_acre"])
    st.session_state["labour"] = float(row["labour_rs_acre"])
    st.session_state["irrigation"] = float(row["irrigation_rs_acre"])
    st.session_state["machinery"] = float(row["machinery_rs_acre"])
    st.session_state["packaging"] = float(row["packaging_rs_acre"])
    st.session_state["transport"] = float(row["transport_rs_acre"])
    st.session_state["other"] = float(row["other_rs_acre"])


if "crop" not in st.session_state:
    st.session_state["crop"] = "Paddy (Common)"
    load_crop_defaults()


st.markdown(
    """
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
  border:1px solid var(--line);background:rgba(255,255,255,.65);border-radius:999px;
  padding:.42rem .78rem;font-size:.76rem;color:var(--green);font-weight:700;
}
.hero{
  position:relative;overflow:hidden;border-radius:30px;padding:2.4rem 2.6rem;
  background:linear-gradient(118deg,#123B32 0%,#1A4C40 58%,#2A6353 100%);
  color:white;box-shadow:0 26px 70px rgba(20,62,53,.17);margin-bottom:1.2rem;
}
.hero:after{
  content:"";position:absolute;width:360px;height:360px;border-radius:50%;
  border:1px solid rgba(255,255,255,.13);right:-115px;top:-145px;
  box-shadow:0 0 0 46px rgba(255,255,255,.035),0 0 0 94px rgba(255,255,255,.022);
}
.eyebrow{font-size:.76rem;letter-spacing:.14em;text-transform:uppercase;font-weight:800;opacity:.70;margin-bottom:.7rem}
.hero h1{color:white!important;font-size:2.55rem;line-height:1.06;margin:0 0 .75rem;max-width:850px}
.hero p{font-size:1rem;line-height:1.65;color:rgba(255,255,255,.79);max-width:830px;margin:0}
.section-kicker{
  font-family:"Manrope",sans-serif;font-size:.76rem;font-weight:800;text-transform:uppercase;
  letter-spacing:.12em;color:var(--green);margin:.3rem 0 .55rem;
}
div[data-testid="stVerticalBlockBorderWrapper"]{
  background:rgba(255,254,250,.88)!important;border:1px solid var(--line)!important;
  border-radius:22px!important;box-shadow:0 12px 34px rgba(25,52,43,.05)!important;
}
div[data-testid="stWidgetLabel"] p{
  font-weight:700!important;color:#334640!important;font-size:.82rem!important;
}
div[data-baseweb="select"]>div,
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
  background:rgba(255,254,250,.96);border:1px solid var(--line);border-radius:19px;
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
  border-left:3px solid var(--gold);background:rgba(255,255,255,.6);padding:.82rem 1rem;
  border-radius:0 12px 12px 0;color:var(--muted);font-size:.80rem;line-height:1.55;
}
.source-chip{
  display:inline-block;border:1px solid var(--line);background:#FFFDF8;border-radius:999px;
  padding:.3rem .58rem;font-size:.72rem;color:#53675F;margin:.1rem .25rem .1rem 0;
}
div[data-testid="stTabs"] button p{font-weight:800!important;}
div[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:15px;overflow:hidden;}
.stDownloadButton button{
  border-radius:12px!important;border:1px solid #D8D2C4!important;color:#173F35!important;
  background:#FFFDF8!important;font-weight:800!important;
}
.small-muted{font-size:.76rem;color:var(--muted);line-height:1.5}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="topbar">
  <div class="brand">
    <div class="brand-mark">🌾</div>
    <div>
      <div class="brand-title">FarmCredit</div>
      <div class="brand-sub">Agricultural financial intelligence</div>
    </div>
  </div>
  <div class="version">Accounting WAI · Prototype v0.2</div>
</div>
<div class="hero">
  <div class="eyebrow">Transparent crop-cycle assessment</div>
  <h1>See whether farm economics can support the borrowing conversation.</h1>
  <p>Model crop profitability, accounting break-even, financing exposure and downside resilience with assumptions that remain visible and editable.</p>
</div>
""",
    unsafe_allow_html=True,
)

assessment_tab, method_tab = st.tabs(["Assessment dashboard", "Methodology & sources"])

with assessment_tab:
    st.markdown('<div class="section-kicker">01 · Configure the farm case</div>', unsafe_allow_html=True)

    left, right = st.columns([0.95, 1.35], gap="large")

    with left:
        with st.container(border=True):
            st.markdown("### Farm, crop & financing")
            l1, l2 = st.columns(2)
            with l1:
                state = st.text_input("State", value="Jharkhand")
            with l2:
                district = st.text_input("District / market area", value="Ranchi")

            crop = st.selectbox(
                "Crop",
                benchmarks.index.tolist(),
                key="crop",
                on_change=load_crop_defaults,
            )

            c1, c2 = st.columns(2)
            with c1:
                area = st.number_input("Land area (acres)", min_value=0.1, value=3.0, step=0.5)
            with c2:
                yield_pa = st.number_input("Expected yield (kg/acre)", min_value=1.0, step=50.0, key="yield_pa")

            c3, c4 = st.columns(2)
            with c3:
                price = st.number_input("Expected selling price (₹/quintal)", min_value=1.0, step=10.0, key="price")
            with c4:
                loss = st.number_input("Post-harvest loss (%)", min_value=0.0, max_value=50.0, step=0.5, key="loss")

            row = benchmarks.loc[crop]
            st.markdown(
                f'<span class="source-chip">{row["season"]} crop</span>'
                f'<span class="source-chip">2026–27 MSP: ₹{row["msp_2026_27_rs_qtl"]:,.0f}/qtl</span>',
                unsafe_allow_html=True,
            )
            st.caption("The MSP is a reference benchmark, not a guarantee of the farmer's realized market price.")

            st.markdown("#### Financing")
            f1, f2 = st.columns(2)
            with f1:
                loan = st.number_input("Loan requested (₹)", min_value=0.0, value=45000.0, step=5000.0)
            with f2:
                rate = st.number_input("Annual interest rate (%)", min_value=0.0, value=7.0, step=0.25)

            months = st.number_input("Crop cycle (months)", min_value=1, max_value=24, step=1, key="months")

    with right:
        with st.container(border=True):
            st.markdown("### Cultivation cost model")
            st.caption("Starter costs are illustrative defaults only. Replace them with the farmer's actual or locally validated figures.")

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
                    help="Non-cash accounting cost allocated to this crop cycle.",
                )

            cost_items = {
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

            preview_total = sum(cost_items.values())
            st.markdown(
                f"""
                <div class="note">
                  Current cash cultivation budget: <b>₹{preview_total:,.0f}/acre</b>.
                  For {area:.1f} acres, that is <b>₹{preview_total*area:,.0f}</b> before interest and depreciation.
                </div>
                """,
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

    st.markdown('<div class="section-kicker" style="margin-top:1.4rem">02 · Financial overview</div>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4, gap="medium")
    with m1:
        st.markdown(metric_card("Expected revenue", money(r["revenue"]), f'{r["saleable_qtl"]:.1f} qtl saleable output', GREEN_2), unsafe_allow_html=True)
    with m2:
        st.markdown(metric_card("Accounting cost", money(r["total_accounting_cost"]), f'{money(r["cash_cost_per_acre"])}/acre cash cost', GOLD), unsafe_allow_html=True)
    with m3:
        profit_accent = GOOD if r["accounting_profit"] >= 0 else BAD
        st.markdown(metric_card("Accounting profit", money(r["accounting_profit"]), f'{r["margin"]:.1f}% profit margin', profit_accent), unsafe_allow_html=True)
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

    if r["excess_financing"] > 0:
        st.warning(
            f"The requested loan exceeds the modeled cash cultivation cost by {money(r['excess_financing'])}. "
            "Check whether the extra borrowing has a defined crop-related use."
        )

    st.markdown('<div class="section-kicker" style="margin-top:1.4rem">03 · Resilience & cost structure</div>', unsafe_allow_html=True)

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
        labels = list(cost_items.keys())
        values = list(cost_items.values())
        fig_cost = go.Figure(
            go.Pie(
                labels=labels,
                values=values,
                hole=0.66,
                textinfo="none",
                hovertemplate="%{label}<br>₹%{value:,.0f}/acre<extra></extra>",
                marker=dict(
                    colors=[
                        "#173F35","#2C6555","#4C806F","#78A08F","#A7B9A8",
                        "#C89B4A","#D8B96E","#B7A88F","#8D8A7D"
                    ]
                ),
            )
        )
        fig_cost.add_annotation(
            text=f"<b>₹{sum(values):,.0f}</b><br><span style='font-size:11px'>per acre</span>",
            showarrow=False,
            font=dict(size=17, color=INK),
        )
        fig_cost.update_layout(
            title=dict(text="Cost composition", x=0.02, xanchor="left", font=dict(size=17, color=INK)),
            margin=dict(l=10, r=10, t=55, b=10),
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            legend=dict(font=dict(size=10, color=MUTED), orientation="h", y=-0.05),
        )
        st.plotly_chart(fig_cost, use_container_width=True, config={"displayModeBar": False})

    with c_right:
        fig_be = go.Figure()
        fig_be.add_trace(
            go.Bar(
                y=["Selling price", "Break-even"],
                x=[price, r["break_even_price"]],
                orientation="h",
                marker_color=[GREEN_2, GOLD],
                text=[f"₹{price:,.0f}", f"₹{r['break_even_price']:,.0f}"],
                textposition="outside",
                hovertemplate="%{y}: ₹%{x:,.0f}/qtl<extra></extra>",
            )
        )
        fig_be.update_layout(
            title=dict(text="Price vs accounting break-even", x=0.02, xanchor="left", font=dict(size=17, color=INK)),
            xaxis=dict(title="₹ per quintal", gridcolor="#ECE7DA", zeroline=False),
            yaxis=dict(title=""),
            margin=dict(l=10, r=35, t=55, b=35),
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=MUTED),
        )
        st.plotly_chart(fig_be, use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div class="section-kicker" style="margin-top:1.2rem">04 · Scenario stress test</div>', unsafe_allow_html=True)

    scenario_df = pd.DataFrame(scenario_rows)
    plot_df = scenario_df.copy()

    fig_stress = go.Figure(
        go.Bar(
            x=plot_df["Scenario"],
            y=plot_df["Accounting profit"],
            marker_color=[
                GREEN_2 if v >= 0 else BAD for v in plot_df["Accounting profit"]
            ],
            text=[money(v) for v in plot_df["Accounting profit"]],
            textposition="outside",
            hovertemplate="%{x}<br>Accounting profit: ₹%{y:,.0f}<extra></extra>",
        )
    )
    fig_stress.add_hline(y=0, line_width=1, line_color="#8D8A7D")
    fig_stress.update_layout(
        title=dict(text="Profit resilience across price and yield shocks", x=0.01, xanchor="left", font=dict(size=18, color=INK)),
        yaxis=dict(title="Accounting profit (₹)", gridcolor="#ECE7DA"),
        xaxis=dict(title=""),
        margin=dict(l=10, r=10, t=55, b=20),
        height=350,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=MUTED),
    )
    st.plotly_chart(fig_stress, use_container_width=True, config={"displayModeBar": False})

    display_df = scenario_df.copy()
    display_df["Yield change"] = display_df["Yield change"].map(lambda x: "Base" if x == 0 else f"{x:+.0%}")
    display_df["Price change"] = display_df["Price change"].map(lambda x: "Base" if x == 0 else f"{x:+.0%}")
    display_df["Revenue"] = display_df["Revenue"].round(0)
    display_df["Accounting profit"] = display_df["Accounting profit"].round(0)
    display_df["Margin"] = display_df["Margin"].map(lambda x: f"{x:.1f}%")
    display_df["Harvest coverage"] = display_df["Harvest coverage"].map(lambda x: f"{x:.2f}×")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Revenue": st.column_config.NumberColumn(format="₹%d"),
            "Accounting profit": st.column_config.NumberColumn(format="₹%d"),
        },
    )

    csv_bytes = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download scenario analysis (CSV)",
        data=csv_bytes,
        file_name="farmcredit_scenario_analysis.csv",
        mime="text/csv",
    )

    st.markdown(
        """
        <div class="note" style="margin-top:.7rem">
          <b>Academic-use notice.</b> FarmCredit is an explainable accounting and scenario-analysis prototype.
          It does not approve or reject credit, predict future crop prices, or replace lender underwriting,
          KYC, bureau, collateral, field-verification, policy or regulatory checks.
        </div>
        """,
        unsafe_allow_html=True,
    )

with method_tab:
    st.markdown("## How the model works")
    st.write(
        "FarmCredit separates farmer-entered assumptions from external reference benchmarks. "
        "The 2026–27 MSP values below are official reference prices; the starter yield and cost figures "
        "are deliberately editable illustrative defaults and are **not** presented as official district-level costs."
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

    st.markdown("### Reference price sources")
    st.markdown(
        "- **Kharif 2026–27 MSP:** Government of India, Press Information Bureau — "
        "[Cabinet approves MSP for Kharif Crops](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2260617&lang=1&reg=3)\n"
        "- **Rabi 2026–27 MSP:** Government of India, Press Information Bureau — "
        "[MSP for Six Rabi Crops](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2197694&lang=1&reg=3)"
    )

    source_table = benchmarks[
        ["season", "msp_2026_27_rs_qtl", "price_source"]
    ].reset_index()
    source_table.columns = ["Crop", "Season", "MSP 2026–27 (₹/qtl)", "Source label"]
    st.dataframe(source_table, hide_index=True, use_container_width=True)

    st.markdown("### Important limitation")
    st.info(
        "MSP is not the same as a farmer's realized mandi price. In the next build, the market module "
        "will fetch recent mandi observations and show the data date, market name and fallback status."
    )
