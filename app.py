from datetime import date
from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from calculations import calculate_case, resilience_label, run_scenarios


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

# Local lookup: no network call, so the app remains fast and reliable.
# "Other / Not listed" keeps the tool usable for any district not present here.
STATE_DISTRICTS = {
    "Andhra Pradesh": ["Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Nellore", "Prakasam", "Visakhapatnam", "Vizianagaram", "West Godavari", "Other / Not listed"],
    "Assam": ["Barpeta", "Cachar", "Darrang", "Dibrugarh", "Goalpara", "Jorhat", "Kamrup", "Kamrup Metropolitan", "Nagaon", "Sonitpur", "Tinsukia", "Other / Not listed"],
    "Bihar": ["Bhojpur", "Buxar", "Darbhanga", "Gaya", "Muzaffarpur", "Nalanda", "Patna", "Purnia", "Rohtas", "Samastipur", "Saran", "Vaishali", "Other / Not listed"],
    "Chhattisgarh": ["Bilaspur", "Dhamtari", "Durg", "Janjgir-Champa", "Korba", "Mahasamund", "Raigarh", "Raipur", "Rajnandgaon", "Other / Not listed"],
    "Gujarat": ["Ahmedabad", "Amreli", "Anand", "Banaskantha", "Bharuch", "Junagadh", "Kheda", "Mehsana", "Rajkot", "Surat", "Vadodara", "Other / Not listed"],
    "Haryana": ["Ambala", "Bhiwani", "Fatehabad", "Hisar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Panipat", "Rohtak", "Sirsa", "Sonipat", "Other / Not listed"],
    "Himachal Pradesh": ["Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kullu", "Mandi", "Shimla", "Sirmaur", "Solan", "Una", "Other / Not listed"],
    "Jharkhand": ["Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahibganj", "Seraikela-Kharsawan", "Simdega", "West Singhbhum", "Other / Not listed"],
    "Karnataka": ["Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bidar", "Chikkaballapur", "Davanagere", "Dharwad", "Hassan", "Haveri", "Kalaburagi", "Kolar", "Mandya", "Mysuru", "Raichur", "Shivamogga", "Tumakuru", "Vijayapura", "Other / Not listed"],
    "Kerala": ["Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad", "Other / Not listed"],
    "Madhya Pradesh": ["Bhopal", "Chhindwara", "Dewas", "Dhar", "Gwalior", "Hoshangabad", "Indore", "Jabalpur", "Mandsaur", "Morena", "Raisen", "Ratlam", "Rewa", "Sagar", "Sehore", "Shajapur", "Ujjain", "Vidisha", "Other / Not listed"],
    "Maharashtra": ["Ahmednagar", "Akola", "Amravati", "Aurangabad", "Jalgaon", "Kolhapur", "Latur", "Nagpur", "Nanded", "Nashik", "Pune", "Sangli", "Satara", "Solapur", "Yavatmal", "Other / Not listed"],
    "Odisha": ["Balasore", "Bargarh", "Bhadrak", "Bolangir", "Cuttack", "Dhenkanal", "Ganjam", "Jajpur", "Kalahandi", "Keonjhar", "Khurda", "Koraput", "Mayurbhanj", "Puri", "Sambalpur", "Other / Not listed"],
    "Punjab": ["Amritsar", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Mansa", "Moga", "Patiala", "Sangrur", "Sri Muktsar Sahib", "Other / Not listed"],
    "Rajasthan": ["Ajmer", "Alwar", "Barmer", "Bharatpur", "Bhilwara", "Bikaner", "Chittorgarh", "Hanumangarh", "Jaipur", "Jodhpur", "Kota", "Nagaur", "Sikar", "Sri Ganganagar", "Tonk", "Udaipur", "Other / Not listed"],
    "Tamil Nadu": ["Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kancheepuram", "Madurai", "Namakkal", "Salem", "Thanjavur", "Tiruchirappalli", "Tirunelveli", "Tiruppur", "Vellore", "Villupuram", "Other / Not listed"],
    "Telangana": ["Adilabad", "Jagtial", "Karimnagar", "Khammam", "Mahabubnagar", "Medak", "Nalgonda", "Nizamabad", "Sangareddy", "Siddipet", "Warangal", "Other / Not listed"],
    "Uttar Pradesh": ["Agra", "Aligarh", "Ayodhya", "Azamgarh", "Ballia", "Bareilly", "Basti", "Bulandshahr", "Deoria", "Etawah", "Ghazipur", "Gorakhpur", "Hardoi", "Jaunpur", "Kanpur Nagar", "Lakhimpur Kheri", "Lucknow", "Mathura", "Meerut", "Moradabad", "Prayagraj", "Raebareli", "Saharanpur", "Sitapur", "Sultanpur", "Unnao", "Varanasi", "Other / Not listed"],
    "Uttarakhand": ["Almora", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Udham Singh Nagar", "Other / Not listed"],
    "West Bengal": ["Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur", "Other / Not listed"],
}

ALL_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Lakshadweep", "Puducherry",
]

for state_name in ALL_STATES:
    STATE_DISTRICTS.setdefault(state_name, ["Other / Not listed"])


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


def build_pdf(case):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title2", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=20, textColor=colors.HexColor(GREEN), spaceAfter=8
    )
    sub_style = ParagraphStyle(
        "Sub", parent=styles["Normal"], fontSize=9,
        textColor=colors.HexColor("#5B6B65"), spaceAfter=10
    )
    h_style = ParagraphStyle(
        "H", parent=styles["Heading2"], fontSize=11,
        textColor=colors.HexColor(GREEN), spaceBefore=8, spaceAfter=5
    )
    story = [
        Paragraph("FarmCredit — Loan Assessment Summary", title_style),
        Paragraph(
            "Academic accounting-based decision-support report. "
            "This is not a credit sanction or underwriting decision.",
            sub_style,
        ),
        Paragraph("Applicant & Farm", h_style),
    ]
    farm_data = [
        ["Applicant", case["Applicant"]],
        ["Location", f'{case["District"]}, {case["State"]}'],
        ["Crop", case["Crop"]],
        ["Area", f'{case["Area"]:.1f} acres'],
        ["Loan requested", money(case["Loan"])],
        ["Expected selling price", f'₹{case["Selling Price"]:,.0f}/qtl'],
    ]
    t1 = Table(farm_data, colWidths=[46*mm, 118*mm])
    t1.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#EEF4F0")),
        ("TEXTCOLOR", (0,0), (-1,-1), colors.HexColor("#20332C")),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#D8E0DB")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story += [t1, Spacer(1, 7), Paragraph("Financial Assessment", h_style)]

    fin = [
        ["Expected revenue", money(case["Revenue"]), "Accounting profit", money(case["Profit"])],
        ["Accounting cost", money(case["Accounting Cost"]), "Profit margin", f'{case["Margin"]:.1f}%'],
        ["Break-even price", f'₹{case["Break-even Price"]:,.0f}/qtl', "Harvest coverage", f'{case["Coverage"]:.2f}×'],
        ["Price cushion", f'{case["Price Cushion"]:.1f}%', "Yield cushion", f'{case["Yield Cushion"]:.1f}%'],
        ["Indicative supportable loan", money(case["Supportable Loan"]), "Resilience", case["Resilience"]],
    ]
    t2 = Table(fin, colWidths=[42*mm, 40*mm, 42*mm, 40*mm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#F9F6ED")),
        ("TEXTCOLOR", (0,0), (-1,-1), colors.HexColor("#20332C")),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
        ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#DDD7C9")),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story += [
        t2,
        Spacer(1, 8),
        Paragraph("Interpretation", h_style),
        Paragraph(case["Status Note"], styles["BodyText"]),
        Spacer(1, 8),
        Paragraph(
            "Method note: expected selling price is entered manually or based on the MSP reference. "
            "FarmCredit deliberately avoids a live market API in the submission version to improve reliability. "
            "Actual lending decisions require independent verification, KYC, policy, bureau, collateral/security "
            "and any other lender-specific checks.",
            sub_style,
        ),
    ]
    doc.build(story)
    return buffer.getvalue()


def seed_demo_portfolio():
    if "portfolio" in st.session_state:
        return
    demos = [
        {
            "Applicant": "Demo Farmer 01", "State": "Jharkhand", "District": "Ranchi",
            "Crop": "Paddy (Common)", "Area": 3.0, "Loan": 45000.0,
            "Selling Price": 2441.0, "Revenue": 83482.2, "Accounting Cost": 58575.0,
            "Profit": 24907.2, "Margin": 29.8, "Coverage": 1.79,
            "Break-even Price": 1712.7, "Price Cushion": 29.8, "Yield Cushion": 29.8,
            "Supportable Loan": 54000.0, "Resilience": "Strong",
            "Status Note": "Base case remains profitable with comfortable modeled coverage."
        },
        {
            "Applicant": "Demo Farmer 02", "State": "West Bengal", "District": "Jalpaiguri",
            "Crop": "Wheat", "Area": 2.0, "Loan": 55000.0,
            "Selling Price": 2585.0, "Revenue": 69500.0, "Accounting Cost": 61200.0,
            "Profit": 8300.0, "Margin": 11.9, "Coverage": 1.22,
            "Break-even Price": 2277.0, "Price Cushion": 11.9, "Yield Cushion": 12.2,
            "Supportable Loan": 52000.0, "Resilience": "Moderate",
            "Status Note": "Base case is positive, but the downside cushion is comparatively thin."
        },
        {
            "Applicant": "Demo Farmer 03", "State": "Bihar", "District": "Patna",
            "Crop": "Maize", "Area": 2.5, "Loan": 70000.0,
            "Selling Price": 2250.0, "Revenue": 53400.0, "Accounting Cost": 59200.0,
            "Profit": -5800.0, "Margin": -10.9, "Coverage": 0.74,
            "Break-even Price": 2494.0, "Price Cushion": -10.8, "Yield Cushion": -10.5,
            "Supportable Loan": 41000.0, "Resilience": "Stressed",
            "Status Note": "The modeled base case is loss-making and coverage is weak."
        },
    ]
    st.session_state["portfolio"] = demos


seed_demo_portfolio()

if "crop" not in st.session_state:
    st.session_state["crop"] = "Paddy (Common)"
    load_crop_defaults()

if "state" not in st.session_state:
    st.session_state["state"] = "Jharkhand"

# Keep district valid when state changes.
current_districts = STATE_DISTRICTS.get(st.session_state["state"], ["Other / Not listed"])
if "district_select" not in st.session_state or st.session_state["district_select"] not in current_districts:
    st.session_state["district_select"] = "Ranchi" if "Ranchi" in current_districts else current_districts[0]


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
.hero p{font-size:1rem;line-height:1.65;color:rgba(255,255,255,.82);max-width:860px;margin:0}
.section-kicker{
  font-family:"Manrope",sans-serif;font-size:.76rem;font-weight:800;text-transform:uppercase;
  letter-spacing:.12em;color:var(--green);margin:.3rem 0 .55rem;
}
div[data-testid="stVerticalBlockBorderWrapper"]{
  background:rgba(255,254,250,.92)!important;border:1px solid var(--line)!important;
  border-radius:22px!important;box-shadow:0 12px 34px rgba(25,52,43,.05)!important;
}
div[data-testid="stWidgetLabel"] p{
  font-weight:700!important;color:#334640!important;font-size:.82rem!important;
}

/* Force all selectors to remain light, including closed crop/state/district controls. */
div[data-testid="stSelectbox"] div[role="combobox"],
div[data-baseweb="select"] > div {
  background:#FFFFFF!important;
  color:#14211D!important;
  border:1px solid #D9D2C4!important;
  border-radius:12px!important;
  box-shadow:none!important;
}
div[data-testid="stSelectbox"] div[role="combobox"] *,
div[data-baseweb="select"] span,
div[data-baseweb="select"] input{
  color:#14211D!important;
  -webkit-text-fill-color:#14211D!important;
  fill:#36564B!important;
}
div[role="listbox"], div[data-baseweb="popover"] ul{
  background:#FFFFFF!important;
  border:1px solid #D9D2C4!important;
}
div[role="option"], div[data-baseweb="popover"] li{
  background:#FFFFFF!important;color:#14211D!important;
}
div[role="option"]:hover, div[data-baseweb="popover"] li:hover{
  background:#EEF4F0!important;color:#14211D!important;
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
.stButton button, .stDownloadButton button{
  border-radius:12px!important;font-weight:800!important;
}
.stButton button{
  background:#173F35!important;color:#FFFFFF!important;border:1px solid #173F35!important;
}
.stButton button:hover{background:#24594A!important;color:#FFFFFF!important}
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
  <div class="version">Submission build · v1.0</div>
</div>
<div class="hero">
  <div class="eyebrow">Accounting-led farm credit assessment</div>
  <h1>Turn farm economics into a clearer lending conversation.</h1>
  <p>Assess profitability, accounting break-even, financing exposure and downside resilience using fast, transparent assumptions. Market price can be entered manually from a recent mandi source or retained at the official MSP reference.</p>
</div>
""", unsafe_allow_html=True)

assessment_tab, banker_tab, method_tab = st.tabs([
    "Farm assessment", "Banker view", "Methodology & sources"
])

with assessment_tab:
    st.markdown('<div class="section-kicker">01 · Applicant, location & crop</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([1.0, 1.15], gap="large")

    with col_a:
        with st.container(border=True):
            st.markdown("### Applicant & location")
            applicant = st.text_input("Applicant name / ID", value="Farmer A-001")

            state = st.selectbox(
                "State / UT",
                ALL_STATES,
                key="state",
            )

            districts = STATE_DISTRICTS.get(state, ["Other / Not listed"])
            if st.session_state.get("district_select") not in districts:
                st.session_state["district_select"] = districts[0]

            district_select = st.selectbox(
                "District",
                districts,
                key="district_select",
            )
            if district_select == "Other / Not listed":
                district = st.text_input("Enter district manually", value="")
                district = district.strip() or "Not specified"
            else:
                district = district_select

            crop = st.selectbox(
                "Crop",
                benchmarks.index.tolist(),
                key="crop",
                on_change=load_crop_defaults,
            )

            row = benchmarks.loc[crop]
            st.markdown(
                f'<span class="source-chip">{row["season"]} crop</span>'
                f'<span class="source-chip">2026–27 MSP: ₹{row["msp_2026_27_rs_qtl"]:,.0f}/qtl</span>',
                unsafe_allow_html=True,
            )

    with col_b:
        with st.container(border=True):
            st.markdown("### Market price assumption")
            price_basis = st.selectbox(
                "Price basis",
                ["MSP reference", "Recent mandi price entered manually", "Bank / farmer estimate"],
            )

            price = st.number_input(
                "Expected / observed selling price (₹/quintal)",
                min_value=1.0,
                step=10.0,
                key="price",
            )

            if price_basis == "Recent mandi price entered manually":
                market_name = st.text_input("Market / mandi name", value="")
                market_date = st.date_input("Price observation date", value=date.today())
                st.caption("Enter the recent modal/expected mandi price manually from your preferred market source.")
            else:
                market_name = ""
                market_date = None

            msp = float(row["msp_2026_27_rs_qtl"])
            delta_msp = (price - msp) / msp * 100 if msp else 0
            st.markdown(
                f"""
                <div class="note">
                  Current price assumption: <b>₹{price:,.0f}/qtl</b><br>
                  MSP reference: <b>₹{msp:,.0f}/qtl</b><br>
                  Difference vs MSP: <b>{delta_msp:+.1f}%</b>
                </div>
                """,
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
                loss = st.number_input("Post-harvest loss (%)", min_value=0.0, max_value=50.0, step=0.5, key="loss")
            with x4:
                months = st.number_input("Crop cycle (months)", min_value=1, max_value=24, step=1, key="months")

            f1, f2 = st.columns(2)
            with f1:
                loan = st.number_input("Loan requested (₹)", min_value=0.0, value=45000.0, step=5000.0)
            with f2:
                rate = st.number_input("Annual interest rate (%)", min_value=0.0, value=7.0, step=0.25)

    with right:
        with st.container(border=True):
            st.markdown("### Cultivation cost model")
            st.caption("Starter values are editable illustrative defaults. Replace them with farmer-specific or locally validated figures.")

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

    st.markdown('<div class="section-kicker" style="margin-top:1.4rem">04 · Resilience & cost structure</div>', unsafe_allow_html=True)
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
        fig_cost.update_layout(
            title=dict(text="Cost composition", x=.02, xanchor="left", font=dict(size=17,color=INK)),
            margin=dict(l=10,r=10,t=55,b=10), height=320,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(font=dict(size=10,color=MUTED),orientation="h",y=-.05)
        )
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
        fig_be.update_layout(
            title=dict(text="Price vs accounting break-even",x=.02,xanchor="left",font=dict(size=17,color=INK)),
            xaxis=dict(title="₹ per quintal",gridcolor="#ECE7DA",zeroline=False),
            yaxis=dict(title=""),margin=dict(l=10,r=35,t=55,b=35),height=320,
            paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED)
        )
        st.plotly_chart(fig_be,use_container_width=True,config={"displayModeBar":False})

    st.markdown('<div class="section-kicker" style="margin-top:1.2rem">05 · Scenario stress test</div>', unsafe_allow_html=True)
    scenario_df = pd.DataFrame(scenario_rows)

    fig_stress = go.Figure(go.Bar(
        x=scenario_df["Scenario"],y=scenario_df["Accounting profit"],
        marker_color=[GREEN_2 if v>=0 else BAD for v in scenario_df["Accounting profit"]],
        text=[money(v) for v in scenario_df["Accounting profit"]],textposition="outside",
        hovertemplate="%{x}<br>Accounting profit: ₹%{y:,.0f}<extra></extra>",
    ))
    fig_stress.add_hline(y=0,line_width=1,line_color="#8D8A7D")
    fig_stress.update_layout(
        title=dict(text="Profit resilience across price and yield shocks",x=.01,xanchor="left",font=dict(size=18,color=INK)),
        yaxis=dict(title="Accounting profit (₹)",gridcolor="#ECE7DA"),xaxis=dict(title=""),
        margin=dict(l=10,r=10,t=55,b=20),height=350,paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",font=dict(color=MUTED)
    )
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

    current_case = {
        "Applicant": applicant,
        "State": state,
        "District": district,
        "Crop": crop,
        "Area": area,
        "Loan": loan,
        "Selling Price": price,
        "Revenue": r["revenue"],
        "Accounting Cost": r["total_accounting_cost"],
        "Profit": r["accounting_profit"],
        "Margin": r["margin"],
        "Coverage": r["harvest_coverage"],
        "Break-even Price": r["break_even_price"],
        "Price Cushion": r["price_cushion"],
        "Yield Cushion": r["yield_cushion"],
        "Supportable Loan": r["indicative_max_supportable_loan"],
        "Resilience": status,
        "Status Note": status_copy,
    }

    a1, a2 = st.columns(2)
    with a1:
        if st.button("Add current case to Banker View", use_container_width=True):
            # Replace same applicant if it already exists.
            st.session_state["portfolio"] = [
                c for c in st.session_state["portfolio"]
                if c["Applicant"] != applicant
            ] + [current_case]
            st.success(f"{applicant} added to Banker View.")
    with a2:
        st.download_button(
            "Download loan assessment PDF",
            data=build_pdf(current_case),
            file_name=f"{applicant.replace(' ','_')}_farmcredit_assessment.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown(
        "<div class='note' style='margin-top:.8rem'><b>Submission-version market approach:</b> "
        "FarmCredit uses official MSP as a reference and allows a recent mandi price to be entered manually. "
        "The live market API was intentionally removed from the final build because it caused slow and unreliable responses during deployment.</div>",
        unsafe_allow_html=True,
    )

with banker_tab:
    st.markdown('<div class="section-kicker">Banker portfolio view</div>', unsafe_allow_html=True)
    portfolio = st.session_state["portfolio"]
    pf = pd.DataFrame(portfolio)

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        st.markdown(metric_card("Applicants", f"{len(pf)}", "Cases in current session", GREEN_2), unsafe_allow_html=True)
    with b2:
        st.markdown(metric_card("Requested exposure", money(pf["Loan"].sum()), "Total requested loan", GOLD), unsafe_allow_html=True)
    with b3:
        strong_count = int((pf["Resilience"] == "Strong").sum())
        st.markdown(metric_card("Strong cases", f"{strong_count}", "Modeled resilience", GOOD), unsafe_allow_html=True)
    with b4:
        stressed_count = int((pf["Resilience"] == "Stressed").sum())
        st.markdown(metric_card("Stressed cases", f"{stressed_count}", "Require closer review", BAD), unsafe_allow_html=True)

    filter_status = st.multiselect(
        "Filter by resilience",
        ["Strong", "Moderate", "Stressed"],
        default=["Strong", "Moderate", "Stressed"],
    )
    show_pf = pf[pf["Resilience"].isin(filter_status)].copy()

    rank_map = {"Strong": 1, "Moderate": 2, "Stressed": 3}
    show_pf["Risk rank"] = show_pf["Resilience"].map(rank_map)
    show_pf = show_pf.sort_values(["Risk rank", "Coverage"], ascending=[True, False])

    table_rows = []
    for _, rowp in show_pf.iterrows():
        table_rows.append(
            "<tr><td>{}</td><td>{}, {}</td><td>{}</td><td>{:.1f}</td><td>{}</td><td>{}</td><td>{:.2f}×</td><td>{}</td></tr>".format(
                rowp["Applicant"], rowp["District"], rowp["State"], rowp["Crop"], rowp["Area"],
                money(rowp["Loan"]), money(rowp["Profit"]), rowp["Coverage"], rowp["Resilience"]
            )
        )
    st.markdown(
        "<table class='light-table'><thead><tr>"
        "<th>Applicant</th><th>Location</th><th>Crop</th><th>Area</th><th>Loan</th>"
        "<th>Profit</th><th>Coverage</th><th>Resilience</th>"
        "</tr></thead><tbody>" + "".join(table_rows) + "</tbody></table>",
        unsafe_allow_html=True,
    )

    st.markdown("### Applicant drill-down")
    selected = st.selectbox("Select applicant", show_pf["Applicant"].tolist())
    case = next(c for c in portfolio if c["Applicant"] == selected)

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.metric("Accounting profit", money(case["Profit"]))
    with d2:
        st.metric("Harvest coverage", f'{case["Coverage"]:.2f}×')
    with d3:
        st.metric("Break-even price", f'₹{case["Break-even Price"]:,.0f}/qtl')
    with d4:
        st.metric("Supportable loan", money(case["Supportable Loan"]))

    st.info(case["Status Note"])

    csv_export = pf.drop(columns=["Status Note"], errors="ignore").to_csv(index=False).encode("utf-8")
    e1, e2 = st.columns(2)
    with e1:
        st.download_button(
            "Download banker portfolio (CSV)",
            data=csv_export,
            file_name="farmcredit_banker_portfolio.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with e2:
        if st.button("Reset to demo portfolio", use_container_width=True):
            st.session_state.pop("portfolio", None)
            seed_demo_portfolio()
            st.rerun()

with method_tab:
    st.markdown("## Methodology & sources")
    st.write(
        "FarmCredit is an accounting-based academic decision-support prototype. "
        "It separates farmer-entered assumptions from external reference benchmarks and keeps the decision logic transparent."
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

    st.markdown("### Market-price approach")
    st.write(
        "The final submission version does not call a live mandi API. "
        "Instead, it uses the 2026–27 MSP reference as a starting benchmark and allows the user to enter a recent mandi or lender/farmer price manually. "
        "This keeps the demonstration fast, transparent and reliable."
    )

    st.markdown("### Reference price sources")
    st.markdown(
        "- **Kharif 2026–27 MSP:** Government of India, Press Information Bureau.\n"
        "- **Rabi 2026–27 MSP:** Government of India, Press Information Bureau.\n"
        "- **Recent market price (optional):** user-entered from a preferred mandi/AGMARKNET/data.gov.in observation."
    )

    source_table = benchmarks[["season", "msp_2026_27_rs_qtl", "price_source"]].reset_index()
    source_table.columns = ["Crop", "Season", "MSP 2026–27 (₹/qtl)", "Source label"]
    st.dataframe(source_table, hide_index=True, use_container_width=True)

    st.warning(
        "The resilience labels and supportable-loan metric are illustrative analytical rules for this academic model. "
        "They are not a bank's sanction criteria and do not replace lender underwriting, KYC, policy, bureau, security/collateral or field verification."
    )
