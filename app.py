import os
import io
import pandas as pd
import streamlit as st
import anthropic
import plotly.graph_objects as go
from datetime import datetime
from logos import GOFLEET_LOGO, ZENDUIT_LOGO

st.set_page_config(page_title="GoFleet Dashboard", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;1,14..32,400&family=IBM+Plex+Mono:wght@400;500&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #f4f6f9 !important;
    }

    /* ── HIDE STREAMLIT CHROME ── */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; max-width: 1100px !important; padding-left: 2.5rem !important; padding-right: 2.5rem !important; }

    /* ── NAV BAR ── */
    .bp-nav {
        display: flex; align-items: center; justify-content: space-between;
        background: #0f172a;
        border-radius: 14px;
        padding: 0.85rem 1.75rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 24px rgba(15,23,42,0.18);
    }
    .bp-nav-left { display: flex; align-items: center; gap: 1rem; }
    .bp-wordmark { font-size: 1.15rem; font-weight: 700; color: #ffffff !important; letter-spacing: -0.03em; }
    .bp-wordmark span { color: #38bdf8 !important; font-weight: 400; }
    .bp-tagline { font-size: 0.72rem; color: #94a3b8 !important; font-family: 'IBM Plex Mono', monospace; letter-spacing: 0.04em; }
    .bp-nav-logos { display: flex; align-items: center; gap: 1rem; }
    .bp-nav-divider { width: 1px; height: 22px; background: #1e293b; }

    /* ── UPLOAD ZONE ── */
    .bp-upload-zone {
        background: #ffffff;
        border: 2px dashed #cbd5e1;
        border-radius: 14px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        transition: border-color 0.2s;
    }
    .bp-upload-title { font-size: 0.85rem; font-weight: 600; color: #0f172a; margin-bottom: 0.25rem; }
    .bp-upload-hint { font-size: 0.75rem; color: #94a3b8; font-family: 'IBM Plex Mono', monospace; }

    /* ── METRIC CARDS ── */
    .bp-metrics {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 0.75rem;
        margin-bottom: 1.25rem;
    }
    .bp-metric {
        background: #ffffff;
        border-radius: 12px;
        padding: 1rem 1.1rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        border: 1px solid rgba(226,232,240,0.8);
        position: relative;
        overflow: hidden;
    }
    .bp-metric::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 3px;
    }
    .bp-m-total::before { background: #0f172a; }
    .bp-m-critical::before { background: #dc2626; }
    .bp-m-high::before { background: #f97316; }
    .bp-m-medium::before { background: #eab308; }
    .bp-m-low::before { background: #3b82f6; }
    .bp-m-accounts::before { background: #8b5cf6; }
    /* ── FORCE ALL CUSTOM HTML TEXT VISIBLE ── */
    .bp-metric-label { font-size:0.6rem; font-weight:600; color:#94a3b8 !important; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.4rem; font-family:'IBM Plex Mono',monospace; }
    .bp-metric-val { font-size:2rem; font-weight:700; line-height:1; }
    .bp-m-total .bp-metric-val { color:#0f172a !important; }
    .bp-m-critical .bp-metric-val { color:#dc2626 !important; }
    .bp-m-high .bp-metric-val { color:#f97316 !important; }
    .bp-m-medium .bp-metric-val { color:#eab308 !important; }
    .bp-m-low .bp-metric-val { color:#3b82f6 !important; }
    .bp-m-accounts .bp-metric-val { color:#8b5cf6 !important; }
    .bp-critical-title { font-size:0.85rem; font-weight:700; color:#dc2626 !important; margin-bottom:0.1rem; }
    .bp-critical-sub { font-size:0.8rem; color:#7f1d1d !important; }
    .bp-risk-label { font-size:0.62rem; font-weight:600; color:#94a3b8 !important; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.25rem; font-family:'IBM Plex Mono',monospace; }
    .bp-risk-val-red { font-size:1.5rem; font-weight:700; color:#dc2626 !important; line-height:1.1; }
    .bp-risk-val-amber { font-size:1.5rem; font-weight:700; color:#d97706 !important; line-height:1.1; }
    .bp-risk-sub { font-size:0.73rem; color:#94a3b8 !important; margin-top:0.1rem; }
    .bp-section-title { font-size:0.78rem; font-weight:700; color:#0f172a !important; white-space:nowrap; letter-spacing:0.02em; text-transform:uppercase; background:transparent !important; }

    /* ── CRITICAL BANNER ── */
    .bp-critical-banner {
        display: flex; align-items: center; gap: 1rem;
        background: linear-gradient(135deg, #fef2f2, #fff5f5);
        border: 1px solid #fecaca; border-left: 5px solid #dc2626;
        border-radius: 12px; padding: 1rem 1.5rem; margin-bottom: 1.25rem;
        box-shadow: 0 2px 8px rgba(220,38,38,0.08);
    }
    .bp-critical-icon { font-size: 1.4rem; flex-shrink: 0; }

    /* ── RISK CARDS ── */
    .bp-risk-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1.25rem; }
    .bp-risk-card {
        background: #ffffff; border-radius: 12px; padding: 1.1rem 1.4rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06); border: 1px solid rgba(226,232,240,0.8);
        display: flex; align-items: center; gap: 1.25rem;
    }
    .bp-risk-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0; }
    .bp-risk-icon-red { background: #fef2f2; }
    .bp-risk-icon-amber { background: #fffbeb; }

    /* ── SECTION HEADER ── */
    .bp-section { display: flex; align-items: center; gap: 0.75rem; margin: 1.4rem 0 0.75rem 0; }
    .bp-section-title { font-size: 0.78rem; font-weight: 700; color: #0f172a !important; white-space: nowrap; letter-spacing: 0.02em; text-transform: uppercase; background: transparent !important; }
    .bp-section-line { flex: 1; height: 1px; background: #e2e8f0; }

    /* ── FORCE ALL TEXT VISIBLE ── */
    .stApp, .stApp * { color: inherit; }
    .stCaption p, .stCaption { color: #64748b !important; font-size: 0.8rem !important; }
    [data-testid="stExpander"] summary { color: #0f172a !important; background: #ffffff !important; }
    [data-testid="stExpander"] summary p { color: #0f172a !important; }
    [data-testid="stExpander"] summary span { color: #0f172a !important; }
    [data-testid="stExpander"] { background: #ffffff !important; border: 1px solid #e2e8f0 !important; border-radius: 10px !important; }
    [data-testid="stFileUploadDropzone"] { background: #ffffff !important; }
    [data-testid="stFileUploadDropzone"] p, [data-testid="stFileUploadDropzone"] span { color: #64748b !important; }
    .stMultiSelect label, .stMultiSelect label p { color: #0f172a !important; font-weight: 600 !important; }
    .stMarkdown p { color: #334155; }
    .bp-section-line { flex: 1; height: 1px; background: #e2e8f0; }

    /* ── BADGES ── */
    .badge { padding: 3px 10px; border-radius: 20px; font-size: 0.65rem; font-weight: 700; font-family: 'IBM Plex Mono', monospace; white-space: nowrap; letter-spacing: 0.02em; }
    .badge-critical { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
    .badge-high { background: #fff7ed; color: #ea580c; border: 1px solid #fed7aa; }
    .badge-medium { background: #fefce8; color: #a16207; border: 1px solid #fde68a; }
    .badge-low { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }

    /* ── TABLES ── */
    .bp-table-wrap {
        background: #ffffff; border-radius: 12px;
        border: 1px solid rgba(226,232,240,0.8);
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        overflow: hidden;
    }
    .bp-table-inner { overflow-x: auto; max-height: 400px; overflow-y: auto; }

    /* ── SUMMARY ── */
    .bp-summary {
        background: #ffffff;
        border: 1px solid rgba(226,232,240,0.8);
        border-radius: 12px;
        padding: 1.5rem;
        font-size: 0.92rem; line-height: 1.85;
        color: #334155;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        margin-top: 0.75rem;
        border-left: 4px solid #38bdf8;
    }

    /* ── BUTTONS ── */
    .stButton > button {
        background: #0f172a !important; color: white !important;
        border: none !important; border-radius: 8px !important;
        font-weight: 600 !important; font-size: 0.85rem !important;
        padding: 0.5rem 1.25rem !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important;
        transition: background 0.15s !important;
    }
    .stButton > button:hover { background: #1e293b !important; }

    /* ── EXPANDERS ── */
    .streamlit-expanderHeader {
        font-size: 0.82rem !important; font-weight: 600 !important; color: #0f172a !important;
        background: #ffffff !important; border-radius: 8px !important;
        border: 1px solid #e2e8f0 !important;
    }
    .streamlit-expanderHeader p { color: #0f172a !important; }
    .streamlit-expanderContent { background: #ffffff !important; }

    /* ── FORCE LIGHT TEXT EVERYWHERE ── */
    p, span, div, label, .stMarkdown { color: inherit; }
    .stCaption, .stCaption p { color: #64748b !important; }
    [data-testid="stFileUploadDropzone"] { background: #ffffff !important; border-color: #cbd5e1 !important; }
    [data-testid="stFileUploadDropzone"] p { color: #64748b !important; }
    [data-testid="stMultiSelect"] label { color: #0f172a !important; font-weight: 600 !important; font-size: 0.82rem !important; }
    .stMultiSelect span { color: #0f172a !important; }

    /* ── RULES GRID ── */
    .rules-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; margin-top: 0.75rem; }
    .rule-item { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.65rem 0.85rem; font-size: 0.77rem; color: #374151 !important; }
    .rule-num { font-family: 'IBM Plex Mono', monospace; color: #3b82f6; font-weight: 600; font-size: 0.67rem; display: block; margin-bottom: 0.15rem; }

    /* ── EXTEND BOX ── */
    .extend-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1.1rem 1.25rem; font-size: 0.84rem; color: #334155 !important; line-height: 1.7; }
    .extend-box code { background: #e2e8f0; padding: 1px 6px; border-radius: 4px; font-family: 'IBM Plex Mono', monospace; font-size: 0.77rem; color: #0f172a; }

    [data-testid="stFileUploaderDropzone"] label,
    [data-testid="stFileUploader"] label { color: #0f172a !important; font-weight: 600 !important; font-size: 0.85rem !important; }
    .bp-upload-hint { font-size: 0.75rem; color: #475569 !important; margin-top: 0.2rem; font-family: 'IBM Plex Mono', monospace; display: block; }

    /* ── SPINNER ── */
    .stSpinner p, [data-testid="stSpinner"] p, .stSpinner > div { color: #0f172a !important; }
    [data-testid="stSpinner"] { color: #0f172a !important; }
    .js-plotly-plot .plotly .ytick text,
    .js-plotly-plot .plotly .xtick text,
    .js-plotly-plot .plotly .gtitle { fill: #0f172a !important; }
</style>
""", unsafe_allow_html=True)


# ── NAV ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="bp-nav">
    <div class="bp-nav-left">
        <div>
            <div class="bp-wordmark">GoFleet <span>Dashboard</span></div>
            <div class="bp-tagline">GoFleet | ZenduIT — Monthly Billing Audit Engine · 29 active rules · Finance & Customer Success</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── DATA LOADING ──────────────────────────────────────────────────────────────
REQUIRED_COLS = [
    "Customer", "Region", "Entity", "Product", "Account Status",
    "Contracted Price ($)", "Actual Invoice ($)", "Usage Qty",
    "Expected Usage Charge ($)", "Product Cost ($)", "Vendor Cost ($)",
    "Gross Margin %", "Prior Month Invoice ($)", "Payment Status",
    "Credit Issued ($)", "Sales Owner", "CS Owner",
    "Contract Start", "Contract End", "Billing Frequency"
]

def load_data(file):
    # Try to find the right sheet — use first sheet if Customer_Data not found
    xl = pd.ExcelFile(file)
    sheet_name = "Customer_Data" if "Customer_Data" in xl.sheet_names else xl.sheet_names[0]
    df = pd.read_excel(file, sheet_name=sheet_name)

    # Check for required columns
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(
            f"This file is missing {len(missing)} required column(s): {', '.join(missing[:5])}"
            + (f" and {len(missing)-5} more." if len(missing) > 5 else ".")
            + f"\n\nSheet used: '{sheet_name}'. Available sheets: {xl.sheet_names}."
        )

    for col in ["Contract Start", "Contract End"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["Contracted Price ($)", "Actual Invoice ($)", "Usage Qty",
                "Expected Usage Charge ($)", "Product Cost ($)", "Vendor Cost ($)",
                "Gross Margin %", "Prior Month Invoice ($)", "Credit Issued ($)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Fill text columns with empty string so string checks don't fail
    for col in ["Account Status", "Payment Status", "Product", "Billing Frequency",
                "Region", "Entity", "Sales Owner", "CS Owner"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    return df, sheet_name


# ── VALIDATION RULES ──────────────────────────────────────────────────────────
def run_validations(df):
    today = pd.Timestamp(datetime.today().date())
    flags = []
    def flag(customer, rule_num, rule_name, risk, description, action):
        flags.append({"Customer": customer, "Rule #": rule_num, "Rule": rule_name,
                      "Risk Level": risk, "Description": description, "Recommended Action": action})
    for _, row in df.iterrows():
        c = row["Customer"]; status = row["Account Status"]; invoice = row["Actual Invoice ($)"]
        contracted = row["Contracted Price ($)"]; prior = row["Prior Month Invoice ($)"]
        usage_qty = row["Usage Qty"]; expected_usage = row["Expected Usage Charge ($)"]
        product_cost = row["Product Cost ($)"]; vendor_cost = row["Vendor Cost ($)"]
        gm = row["Gross Margin %"]; payment = row["Payment Status"]; credit = row["Credit Issued ($)"]
        product = row["Product"]; billing_freq = row["Billing Frequency"]
        contract_end = row["Contract End"]; contract_start = row["Contract Start"]
        sales = row["Sales Owner"]; cs_owner = row["CS Owner"]; region = row["Region"]
        if status == "Active" and invoice == 0:
            flag(c,1,"Active Account - Zero Invoice","High","Active account with $0 invoice this month.","Investigate billing system. Confirm waiver or system error. Escalate to Sales Owner.")
        if status == "Inactive" and invoice > 0:
            flag(c,2,"Inactive Account - Still Billed","High",f"Inactive account invoiced ${invoice:,.0f}.","Stop billing immediately. Issue credit if charged. Audit duration.")
        if billing_freq == "Monthly" and invoice != contracted and invoice != 0 and status == "Active":
            flag(c,3,"Invoice/Contract Price Mismatch","Medium",f"Invoice ${invoice:,.0f} does not match contracted ${contracted:,.0f}.","Pull signed contract. Correct invoice or update contract if price changed.")
        if expected_usage > invoice and usage_qty > 0:
            flag(c,4,"Usage Underbilled","Medium",f"Expected usage ${expected_usage:,.0f} exceeds invoice ${invoice:,.0f}.","Confirm usage rate applied. Reissue corrected invoice.")
        if credit > invoice and invoice > 0:
            flag(c,5,"Credit Exceeds Invoice","High",f"Credit ${credit:,.0f} exceeds invoice ${invoice:,.0f}.","Finance Lead approval required. Verify credit reason.")
        if invoice == prior and usage_qty == 0 and product == "SaaS":
            flag(c,6,"Duplicate Invoice - No Usage Change","Medium",f"Invoice ${invoice:,.0f} identical to prior month with 0 usage.","Confirm intentional. Investigate potential billing freeze.")
        if billing_freq == "Annual" and invoice != contracted * 12:
            flag(c,7,"Annual Billing Amount Error","High",f"Annual invoice ${invoice:,.0f} != 12x contracted ${contracted*12:,.0f}.","Recalculate and issue corrected invoice or credit note.")
        if pd.notna(contract_start) and contract_start > today and invoice > 0:
            flag(c,8,"Pre-Contract Billing","High",f"Contract starts {contract_start.date()} but invoiced ${invoice:,.0f}.","Do not bill until contract start. Reverse invoice if sent.")
        if isinstance(gm, float) and gm < 0:
            flag(c,9,"Negative Gross Margin","Critical",f"Gross margin {gm:.1%} -- losing money on this account.","Immediate Finance and Sales review. Evaluate repricing or contract exit.")
        if isinstance(gm, float) and 0 < gm < 0.15:
            flag(c,10,"Low Gross Margin Warning","Medium",f"Gross margin {gm:.1%} is below 15% threshold.","Finance Lead review. Assess pricing adjustment at next renewal.")
        if status == "Active" and invoice > 0 and (product_cost == 0 or vendor_cost == 0):
            missing = []
            if product_cost == 0: missing.append("Product Cost")
            if vendor_cost == 0: missing.append("Vendor Cost")
            flag(c,11,"Missing Cost Data","Medium",f"Missing {' and '.join(missing)}.","Request from Finance/Procurement. Cannot calculate true margin.")
        if invoice > 0 and vendor_cost / invoice > 0.30:
            flag(c,12,"High Vendor Cost Ratio","Medium",f"Vendor cost ${vendor_cost:,.0f} = {vendor_cost/invoice:.0%} of invoice.","Review vendor contract for renegotiation.")
        if invoice > 0 and isinstance(gm, float):
            calc_gm = (invoice - product_cost - vendor_cost) / invoice
            if abs(calc_gm - gm) > 0.01:
                flag(c,13,"Gross Margin Calculation Mismatch","Medium",f"Stated GM {gm:.2%} vs calculated {calc_gm:.2%}.","Reconcile cost inputs against stated margin.")
        if isinstance(gm, float) and gm > 0.95:
            flag(c,14,"Suspiciously High Gross Margin","Medium",f"Gross margin {gm:.1%} above 95%.","Verify product and vendor costs are fully captured.")
        if pd.notna(contract_end) and contract_end < today and invoice > 0:
            flag(c,15,"Expired Contract - Active Billing","High",f"Contract expired {contract_end.date()} but invoiced ${invoice:,.0f}.","CS Owner to initiate renewal. No billing on expired contracts without approval.")
        if pd.isna(contract_end):
            flag(c,16,"Missing Contract End Date","Medium","No contract end date on file.","Retrieve signed contract and update system.")
        if pd.notna(contract_end):
            days_left = (contract_end - today).days
            if 0 <= days_left <= 60:
                flag(c,17,"Renewal Risk - Contract Expiring Soon","Medium",f"Contract expires in {days_left} days ({contract_end.date()}).","CS Owner to initiate renewal immediately.")
        if pd.notna(contract_start) and (today - contract_start).days > 730:
            flag(c,18,"Price Review Due","Low",f"Contract started {contract_start.date()} -- over 2 years old.","Flag for renewal cycle. Review pricing against current costs.")
        if payment == "Overdue":
            flag(c,19,"Overdue Payment","High","Payment is overdue.",f"CS Owner ({cs_owner}) to contact within 48 hours. Escalate in 5 days.")
        if payment == "Partial":
            flag(c,20,"Partial Payment","Medium","Only partial payment received.",f"CS Owner ({cs_owner}) to follow up and document payment plan.")
        if payment == "Paid" and credit > 0:
            flag(c,21,"Credit Issued on Paid Account","Medium",f"Credit ${credit:,.0f} issued same month as Paid status.","Verify credit applied correctly. Confirm next month invoice impact.")
        if prior > 0 and abs((invoice - prior) / prior) > 0.20:
            pct = (invoice - prior) / prior
            flag(c,22,"Large MoM Invoice Change","High",f"Invoice changed {pct:+.0%} vs prior month (${prior:,.0f} to ${invoice:,.0f}).","Investigate root cause before sending. Document reason.")
        if product == "Hardware" and usage_qty > 0:
            flag(c,23,"Hardware Product with Usage","Low",f"Hardware recorded {usage_qty:.0f} usage units.","Confirm usage billing applies. May indicate wrong product type.")
        if product == "SaaS" and usage_qty == 0:
            flag(c,24,"SaaS - Zero Usage (Churn Risk)","Medium","SaaS account has 0 usage this month.",f"CS Owner ({cs_owner}) to check adoption. Early churn signal.")
        if product == "Software Support" and usage_qty > 0:
            flag(c,25,"Software Support with Unexpected Usage","Low",f"Software Support recorded {usage_qty:.0f} usage units.","Verify billing model. Software Support is typically not usage-billed.")
        if pd.isna(sales) or str(sales).strip() == "":
            flag(c,26,"Missing Sales Owner","Medium","No Sales Owner assigned.","Assign Sales Owner in CRM immediately.")
        if pd.isna(cs_owner) or str(cs_owner).strip() == "":
            flag(c,27,"Missing CS Owner","Medium","No CS Owner assigned.","Assign CS Owner. Unowned accounts lack relationship management.")
        if region in ["Europe", "APAC"]:
            flag(c,29,"International Billing - Currency Verification","Low",f"Account in {region} -- billing currency not confirmed.","Verify correct currency per contract. Document FX exposure.")
    entity_counts = df.groupby("Customer")["Entity"].nunique()
    for customer in entity_counts[entity_counts > 1].index:
        entities = df[df["Customer"] == customer]["Entity"].unique().tolist()
        flag(customer,28,"Multi-Entity Billing","Medium",f"Customer appears under {' and '.join(entities)}.","Confirm intentional cross-entity billing or investigate data entry error.")
    return pd.DataFrame(flags)


def calc_revenue_at_risk(df):
    today = pd.Timestamp(datetime.today().date())
    inactive_billed = df[(df["Account Status"] == "Inactive") & (df["Actual Invoice ($)"] > 0)]["Actual Invoice ($)"].sum()
    annual_errors = df[df["Billing Frequency"] == "Annual"].apply(
        lambda r: abs(r["Actual Invoice ($)"] - r["Contracted Price ($)"] * 12)
        if r["Actual Invoice ($)"] != r["Contracted Price ($)"] * 12 else 0, axis=1).sum()
    overbilling = inactive_billed + annual_errors
    active_zero = df[(df["Account Status"] == "Active") & (df["Actual Invoice ($)"] == 0)]["Contracted Price ($)"].sum()
    underbilled = df[df["Expected Usage Charge ($)"] > df["Actual Invoice ($)"]].apply(
        lambda r: r["Expected Usage Charge ($)"] - r["Actual Invoice ($)"] if r["Usage Qty"] > 0 else 0, axis=1).sum()
    return overbilling, active_zero + underbilled


def generate_summary(flags_df, source_df):
    api_key = os.environ.get("ANTHROPIC_API_KEY") or st.session_state.get("api_key", "")
    if not api_key:
        return "API key not set."

    total_inv = source_df["Actual Invoice ($)"].sum()
    overbilling, unbilled = calc_revenue_at_risk(source_df)

    # Top-level overview lines
    overview_lines = []
    for _, r in pd.concat([flags_df[flags_df["Risk Level"] == s] for s in ["Critical","High","Medium"]]).head(10).iterrows():
        overview_lines.append(f"- [{r['Risk Level']}] {r['Customer']}: {r['Rule']} -- {r['Description']}")

    # Per-company breakdown
    company_lines = []
    for customer in flags_df["Customer"].unique():
        cust_flags = flags_df[flags_df["Customer"] == customer]
        cust_data = source_df[source_df["Customer"] == customer].iloc[0] if len(source_df[source_df["Customer"] == customer]) > 0 else None
        flag_summary = "; ".join([f"{r['Rule']} ({r['Risk Level']})" for _, r in cust_flags.iterrows()])
        if cust_data is not None:
            company_lines.append(
                f"{customer} | Invoice: ${cust_data['Actual Invoice ($)']:,.0f} | Status: {cust_data['Account Status']} | "
                f"GM: {cust_data['Gross Margin %']:.1%} | Flags: {flag_summary}"
            )

    prompt = (
        f"You are writing a billing exception summary for the Finance Lead.\n\n"
        f"OVERVIEW: {len(flags_df)} flags across {source_df['Customer'].nunique()} accounts. "
        f"Total invoiced: ${total_inv:,.0f}. Overbilling risk: ${overbilling:,.0f}. Unbilled revenue: ${unbilled:,.0f}.\n\n"
        f"Top issues:\n" + "\n".join(overview_lines) + "\n\n"
        f"COMPANY DATA:\n" + "\n".join(company_lines) + "\n\n"
        f"Write the summary in two parts:\n\n"
        f"PART 1 — OVERALL SUMMARY (3 sentences max): What is the main billing problem this month, what is the dollar impact, and what is the single most important next step.\n\n"
        f"PART 2 — COMPANY BREAKDOWN: For each company that has at least one High or Critical flag, write one short sentence describing their specific issue and what needs to happen. Format as: Company Name: [issue and action]. Do not use square brackets around the company name. Skip companies with only Low flags.\n\n"
        f"Keep everything factual and plain. No sign-off. No bullet points in Part 1. Use the [Company]: format exactly in Part 2."
    )
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(model="claude-opus-4-6", max_tokens=1200,
                                  messages=[{"role": "user", "content": prompt}])
    return msg.content[0].text


def to_excel(flags_df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        flags_df.to_excel(w, sheet_name="Exception Report", index=False)
    return out.getvalue()


# ── API KEY ───────────────────────────────────────────────────────────────────
if not os.environ.get("ANTHROPIC_API_KEY"):
    with st.expander("Set Anthropic API Key", expanded=False):
        key = st.text_input("API Key", type="password", placeholder="sk-ant-...")
        if key:
            st.session_state["api_key"] = key
            st.success("Key set.")

# ── UPLOAD ────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader("Upload Monthly Billing File (.xlsx)", type=["xlsx"])
st.markdown('<div class="bp-upload-hint">Standard GoFleet / ZenduIT monthly billing export</div>', unsafe_allow_html=True)

if uploaded:
    try:
        df, sheet_used = load_data(uploaded)
        flags = run_validations(df)
        counts = flags["Risk Level"].value_counts().to_dict()
        n_critical = counts.get("Critical",0); n_high = counts.get("High",0)
        n_medium = counts.get("Medium",0); n_low = counts.get("Low",0); n_total = len(flags)
        overbilling, unbilled = calc_revenue_at_risk(df)

        # ── METRICS ──
        st.markdown(f"""
        <div class="bp-metrics">
            <div class="bp-metric bp-m-total"><div class="bp-metric-label">Total Flags</div><div class="bp-metric-val">{n_total}</div></div>
            <div class="bp-metric bp-m-critical"><div class="bp-metric-label">Critical</div><div class="bp-metric-val">{n_critical}</div></div>
            <div class="bp-metric bp-m-high"><div class="bp-metric-label">High</div><div class="bp-metric-val">{n_high}</div></div>
            <div class="bp-metric bp-m-medium"><div class="bp-metric-label">Medium</div><div class="bp-metric-val">{n_medium}</div></div>
            <div class="bp-metric bp-m-low"><div class="bp-metric-label">Low</div><div class="bp-metric-val">{n_low}</div></div>
            <div class="bp-metric bp-m-accounts"><div class="bp-metric-label">Accounts</div><div class="bp-metric-val">{len(df)}</div></div>
        </div>""", unsafe_allow_html=True)

        # ── CRITICAL BANNER ──
        if n_critical > 0:
            crit_flags = flags[flags["Risk Level"] == "Critical"]
            crit_customers = ", ".join(crit_flags["Customer"].unique().tolist())
            crit_details = " · ".join([f"{r['Customer']}: {r['Description']}" for _, r in crit_flags.iterrows()])
            st.markdown(f"""
            <div class="bp-critical-banner">
                <div class="bp-critical-icon">🚨</div>
                <div>
                    <div class="bp-critical-title">{n_critical} Critical Flag{"s" if n_critical > 1 else ""} — Immediate Action Required</div>
                    <div class="bp-critical-sub" style="margin-bottom:0.25rem;">{crit_customers}</div>
                    <div style="font-size:0.78rem;color:#991b1b;margin-top:0.15rem;">{crit_details}</div>
                </div>
            </div>""", unsafe_allow_html=True)

        # ── REVENUE AT RISK ──
        st.markdown('<div class="bp-section"><div class="bp-section-title">Revenue at Risk</div><div class="bp-section-line"></div></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="bp-risk-row">
            <div class="bp-risk-card">
                <div class="bp-risk-icon bp-risk-icon-red">💸</div>
                <div>
                    <div class="bp-risk-label">Potential Overbilling</div>
                    <div class="bp-risk-val-red">${overbilling:,.0f}</div>
                    <div class="bp-risk-sub">Inactive accounts still billed + annual errors</div>
                </div>
            </div>
            <div class="bp-risk-card">
                <div class="bp-risk-icon bp-risk-icon-amber">📉</div>
                <div>
                    <div class="bp-risk-label">Unbilled / Lost Revenue</div>
                    <div class="bp-risk-val-amber">${unbilled:,.0f}</div>
                    <div class="bp-risk-sub">Active $0 invoices + usage underbilling</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        # ── CHARTS ──
        st.markdown('<div class="bp-section"><div class="bp-section-title">Analytics</div><div class="bp-section-line"></div></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)

        chart_layout = dict(
            margin=dict(t=40,b=20,l=10,r=10),
            height=230,
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(family="Inter", color="#0f172a"),
        )

        with col1:
            sev_order = ["High","Medium","Low"]
            fig_donut = go.Figure(go.Pie(
                labels=sev_order,
                values=[counts.get(s,0) for s in sev_order],
                hole=0.6,
                marker_colors=["#f97316","#eab308","#3b82f6"],
                marker_line=dict(color="#ffffff", width=2),
                textinfo="label+value",
                textposition="inside",
                insidetextfont=dict(size=11, color="#ffffff"),
                hovertemplate="%{label}: %{value}<extra></extra>"
            ))
            fig_donut.add_annotation(
                text=f"<b>{n_high+n_medium+n_low}</b>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=24, color="#0f172a"), align="center")
            fig_donut.update_layout(
                title=dict(text="Flags by Severity", font=dict(size=12, color="#0f172a"), x=0.02),
                showlegend=True,
                legend=dict(orientation="h", x=0.05, y=-0.08, font=dict(size=11, color="#0f172a")),
                margin=dict(t=40,b=50,l=10,r=10),
                height=260, paper_bgcolor="white", plot_bgcolor="white")
            st.plotly_chart(fig_donut, use_container_width=True)

        with col2:
            rule_cats = {
                "Billing": list(range(1,9)),
                "Margin": list(range(9,15)),
                "Contract": list(range(15,19)),
                "Payment": list(range(19,22)),
                "Product": [22,23,24,25],
                "Ownership": [26,27,28,29],
            }
            cat_vals = [len(flags[flags["Rule #"].isin(r)]) for r in rule_cats.values()]
            fig_cat = go.Figure(go.Bar(
                x=cat_vals,
                y=list(rule_cats.keys()),
                orientation="h",
                marker_color=["#3b82f6","#8b5cf6","#f97316","#10b981","#f43f5e","#0ea5e9"],
                marker_line=dict(color="rgba(0,0,0,0)", width=0),
                text=cat_vals, textposition="outside",
                textfont=dict(size=11, color="#0f172a"),
                hovertemplate="%{y}: %{x} flags<extra></extra>"
            ))
            fig_cat.update_layout(
                title=dict(text="Flags by Category", font=dict(size=12, color="#0f172a"), x=0.02),
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(tickfont=dict(size=11, color="#0f172a")),
                margin=dict(t=40,b=20,l=80,r=40),
                height=260, paper_bgcolor="white", plot_bgcolor="white",
                font=dict(family="Inter", color="#0f172a"))
            st.plotly_chart(fig_cat, use_container_width=True)

        with col3:
            cs_flags = flags.merge(df[["Customer","CS Owner"]], on="Customer", how="left")
            cs_flags["CS Owner"] = cs_flags["CS Owner"].fillna("Unassigned")
            cs_counts = cs_flags.groupby("CS Owner").size().sort_values(ascending=True)
            fig_cs = go.Figure(go.Bar(
                x=cs_counts.values,
                y=cs_counts.index,
                orientation="h",
                marker_color="#0ea5e9",
                marker_line=dict(color="rgba(0,0,0,0)", width=0),
                text=cs_counts.values, textposition="outside",
                textfont=dict(size=11, color="#0f172a"),
                hovertemplate="%{y}: %{x} flags<extra></extra>"
            ))
            fig_cs.update_layout(
                title=dict(text="Flags by CS Owner", font=dict(size=12, color="#0f172a"), x=0.02),
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(tickfont=dict(size=11, color="#0f172a")),
                margin=dict(t=40,b=20,l=80,r=40),
                height=260, paper_bgcolor="white", plot_bgcolor="white",
                font=dict(family="Inter", color="#0f172a"))
            st.plotly_chart(fig_cs, use_container_width=True)

        # ── CUSTOMER RISK TABLE ──
        st.markdown('<div class="bp-section"><div class="bp-section-title">Customer Risk Overview</div><div class="bp-section-line"></div></div>', unsafe_allow_html=True)
        sev_rank = {"Critical":4,"High":3,"Medium":2,"Low":1}
        badge_map = {"Critical":"badge-critical","High":"badge-high","Medium":"badge-medium","Low":"badge-low"}
        row_bg = {"Critical":"#fff5f5","High":"#fff8f4","Medium":"#fefce8","Low":"#f0f9ff"}

        customer_risk = flags.groupby("Customer").apply(
            lambda x: x.loc[x["Risk Level"].map(sev_rank).idxmax(),"Risk Level"]).reset_index()
        customer_risk.columns = ["Customer","Highest Severity"]
        customer_risk["Flag Count"] = flags.groupby("Customer").size().values
        customer_risk = customer_risk.sort_values("Highest Severity",key=lambda x: x.map(sev_rank),ascending=False)

        rows_risk = ""
        for _, r in customer_risk.iterrows():
            badge = f'<span class="badge {badge_map.get(r["Highest Severity"],"")} ">{r["Highest Severity"]}</span>'
            bg = row_bg.get(r["Highest Severity"],"#fff")
            rows_risk += f'<tr style="background:{bg};"><td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;font-weight:600;color:#0f172a;font-size:0.85rem;">{r["Customer"]}</td><td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;">{badge}</td><td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;color:#64748b;font-family:monospace;font-size:0.8rem;text-align:center;font-weight:600;">{r["Flag Count"]}</td></tr>'

        st.markdown(f'<div class="bp-table-wrap"><div class="bp-table-inner"><table style="width:100%;border-collapse:collapse;"><thead><tr style="background:#f8fafc;"><th style="padding:10px 16px;text-align:left;font-size:0.67rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;border-bottom:2px solid #e2e8f0;">Customer</th><th style="padding:10px 16px;text-align:left;font-size:0.67rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;border-bottom:2px solid #e2e8f0;">Highest Severity</th><th style="padding:10px 16px;text-align:center;font-size:0.67rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;border-bottom:2px solid #e2e8f0;">Flags</th></tr></thead><tbody>{rows_risk}</tbody></table></div></div>', unsafe_allow_html=True)

        # ── EXCEPTION DETAIL ──
        st.markdown('<div class="bp-section"><div class="bp-section-title">Exception Detail</div><div class="bp-section-line"></div></div>', unsafe_allow_html=True)
        severity_filter = st.multiselect("Filter by severity",
            options=["Critical","High","Medium","Low"],
            default=["Critical","High","Medium","Low"])
        filtered = flags[flags["Risk Level"].isin(severity_filter)]

        rows_detail = ""
        for _, r in filtered.iterrows():
            badge = f'<span class="badge {badge_map.get(r["Risk Level"],"")} ">{r["Risk Level"]}</span>'
            rows_detail += f'<tr onmouseover="this.style.background=\'#f8fafc\'" onmouseout="this.style.background=\'\'">'
            rows_detail += f'<td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;font-weight:600;color:#0f172a;font-size:0.85rem;white-space:nowrap;">{r["Customer"]}</td>'
            rows_detail += f'<td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;color:#3b82f6;font-family:monospace;font-size:0.75rem;font-weight:600;">R{r["Rule #"]}</td>'
            rows_detail += f'<td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;color:#334155;font-size:0.85rem;white-space:nowrap;">{r["Rule"]}</td>'
            rows_detail += f'<td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;">{badge}</td>'
            rows_detail += f'<td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;color:#475569;font-size:0.83rem;">{r["Description"]}</td>'
            rows_detail += f'<td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;color:#475569;font-size:0.83rem;">{r["Recommended Action"]}</td></tr>'

        st.markdown(f'<div class="bp-table-wrap"><div class="bp-table-inner" style="max-height:460px;"><table style="width:100%;border-collapse:collapse;"><thead><tr style="background:#f8fafc;position:sticky;top:0;z-index:1;"><th style="padding:10px 16px;text-align:left;font-size:0.67rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;border-bottom:2px solid #e2e8f0;">Customer</th><th style="padding:10px 16px;text-align:left;font-size:0.67rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;border-bottom:2px solid #e2e8f0;">Rule</th><th style="padding:10px 16px;text-align:left;font-size:0.67rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;border-bottom:2px solid #e2e8f0;">Name</th><th style="padding:10px 16px;text-align:left;font-size:0.67rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;border-bottom:2px solid #e2e8f0;">Severity</th><th style="padding:10px 16px;text-align:left;font-size:0.67rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;border-bottom:2px solid #e2e8f0;">Description</th><th style="padding:10px 16px;text-align:left;font-size:0.67rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;border-bottom:2px solid #e2e8f0;">Recommended Action</th></tr></thead><tbody>{rows_detail}</tbody></table></div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button("Download Exception Report (Excel)", data=to_excel(flags),
            file_name="BillingPulse_Exception_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # ── FINANCE LEAD SUMMARY ──
        st.markdown('<div class="bp-section"><div class="bp-section-title">Finance Lead Summary</div><div class="bp-section-line"></div></div>', unsafe_allow_html=True)
        st.caption("Plain-language summary generated by Claude for the Finance Lead and VP of Customer Success.")
        if st.button("Generate Finance Lead Summary"):
            with st.spinner("Generating..."):
                summary = generate_summary(flags, df)
            safe = summary.replace("$", "&#36;")
            # Clean up markdown artifacts
            safe = safe.replace("****", "").replace("***", "").replace("**", "").replace("* *", "")
            safe = safe.strip()
            # Split into Part 1 and Part 2 if both present
            if "PART 2" in safe or "COMPANY BREAKDOWN" in safe:
                parts = safe.replace("PART 1 — OVERALL SUMMARY", "").replace("PART 1:", "").replace("OVERALL SUMMARY", "").split("PART 2")
                if len(parts) == 2:
                    part1 = parts[0].strip().lstrip("—").strip()
                    part2 = parts[1].replace("— COMPANY BREAKDOWN", "").replace(": COMPANY BREAKDOWN", "").replace("COMPANY BREAKDOWN", "").strip()
                    st.markdown(f'<div class="bp-summary"><div style="font-weight:600;color:#0f172a;margin-bottom:0.75rem;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.06em;">Overall Summary</div>{part1}</div>', unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    # Format company breakdown
                    company_html = ""
                    for line in part2.strip().split("\n"):
                        line = line.strip()
                        if not line: continue
                        if ":" in line:
                            company, rest = line.split(":", 1)
                            company = company.strip().lstrip("-").strip().strip("[]")
                            company_html += f'<div style="padding:0.65rem 0;border-bottom:1px solid #f1f5f9;display:flex;gap:0.75rem;align-items:flex-start;"><span style="font-weight:700;color:#0f172a;white-space:nowrap;min-width:160px;font-size:0.85rem;">{company}</span><span style="color:#475569;font-size:0.85rem;line-height:1.6;">{rest.strip()}</span></div>'
                        else:
                            company_html += f'<div style="padding:0.5rem 0;color:#475569;font-size:0.85rem;">{line}</div>'
                    st.markdown(f'<div class="bp-summary"><div style="font-weight:600;color:#0f172a;margin-bottom:0.75rem;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.06em;">Company Breakdown</div>{company_html}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="bp-summary">{safe}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bp-summary">{safe}</div>', unsafe_allow_html=True)

        # ── RULES REFERENCE ──
        st.markdown('<div class="bp-section"><div class="bp-section-title">Validation Rules</div><div class="bp-section-line"></div></div>', unsafe_allow_html=True)
        with st.expander("View all 29 rules"):
            rules_list = [
                (1,"Billing","Active Account - Zero Invoice","High"),(2,"Billing","Inactive Account - Still Billed","High"),
                (3,"Billing","Invoice/Contract Price Mismatch","Medium"),(4,"Billing","Usage Underbilled","Medium"),
                (5,"Billing","Credit Exceeds Invoice","High"),(6,"Billing","Duplicate Invoice - No Usage Change","Medium"),
                (7,"Billing","Annual Billing Amount Error","High"),(8,"Billing","Pre-Contract Billing","High"),
                (9,"Margin","Negative Gross Margin","Critical"),(10,"Margin","Low Gross Margin Warning","Medium"),
                (11,"Margin","Missing Cost Data","Medium"),(12,"Margin","High Vendor Cost Ratio","Medium"),
                (13,"Margin","Gross Margin Calculation Mismatch","Medium"),(14,"Margin","Suspiciously High Gross Margin","Medium"),
                (15,"Contract","Expired Contract - Active Billing","High"),(16,"Contract","Missing Contract End Date","Medium"),
                (17,"Contract","Renewal Risk - Expiring Soon","Medium"),(18,"Contract","Price Review Due","Low"),
                (19,"Payment","Overdue Payment","High"),(20,"Payment","Partial Payment","Medium"),
                (21,"Payment","Credit Issued on Paid Account","Medium"),(22,"MoM","Large MoM Invoice Change","High"),
                (23,"Product","Hardware with Usage","Low"),(24,"Product","SaaS - Zero Usage (Churn Risk)","Medium"),
                (25,"Product","Software Support with Usage","Low"),(26,"Ownership","Missing Sales Owner","Medium"),
                (27,"Ownership","Missing CS Owner","Medium"),(28,"Multi-Entity","Customer in Multiple Entities","Medium"),
                (29,"Regional","International Currency Verification","Low"),
            ]
            bc_map = {"Critical":"background:#fef2f2;color:#dc2626","High":"background:#fff7ed;color:#ea580c","Medium":"background:#fefce8;color:#a16207","Low":"background:#eff6ff;color:#1d4ed8"}
            rhtml = '<div class="rules-grid">'
            for num, cat, name, sev in rules_list:
                rhtml += f'<div class="rule-item"><span class="rule-num">R{num} · {cat}</span>{name}<br><span style="{bc_map.get(sev,"")};padding:1px 7px;border-radius:20px;font-size:0.62rem;font-weight:700;margin-top:0.2rem;display:inline-block;">{sev}</span></div>'
            rhtml += "</div>"
            st.markdown(rhtml, unsafe_allow_html=True)

        # ── EXTENDING ──
        st.markdown('<div class="bp-section"><div class="bp-section-title">Extending the Engine</div><div class="bp-section-line"></div></div>', unsafe_allow_html=True)
        with st.expander("How to add new validation rules"):
            st.markdown('<div class="extend-box">All rules live in <code>run_validations()</code>. A new rule is 5 lines of Python — the engine automatically adds it to all charts, the exception table, the Excel download, and the Claude summary.</div>', unsafe_allow_html=True)
            st.code('if invoice > 10000:\n    flag(customer, 30, "High Value Invoice Review", "Medium",\n         f"Invoice ${invoice:,.0f} exceeds $10,000 threshold.",\n         "Route to Finance Lead for manual approval before sending.")', language="python")
            st.markdown('<div class="extend-box" style="margin-top:0.6rem;">For Finance teams that want to manage rules without touching code, the engine can load rule definitions from a YAML or JSON config file.</div>', unsafe_allow_html=True)

    except ValueError as e:
        st.markdown(f'<div style="background:#fef2f2;border:1px solid #fecaca;border-left:4px solid #dc2626;border-radius:10px;padding:1rem 1.25rem;color:#991b1b;font-size:0.875rem;line-height:1.6;margin-bottom:1rem;"><strong>Column mismatch:</strong> {str(e)}</div>', unsafe_allow_html=True)
        cols = "Customer · Region · Entity · Product · Account Status · Contracted Price ($) · Actual Invoice ($) · Usage Qty · Expected Usage Charge ($) · Product Cost ($) · Vendor Cost ($) · Gross Margin % · Prior Month Invoice ($) · Payment Status · Credit Issued ($) · Sales Owner · CS Owner · Contract Start · Contract End · Billing Frequency"
        st.markdown(f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:0.85rem 1.1rem;font-size:0.8rem;color:#475569;margin-top:0.5rem;"><strong style="color:#0f172a;">Required columns:</strong><br><span style="font-family:monospace;font-size:0.75rem;">{cols}</span></div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.caption("Make sure the file is a valid .xlsx with billing data in the expected format.")
else:
    st.markdown("""
    <div style="background:#ffffff;border:2px dashed #cbd5e1;border-radius:14px;padding:3rem 2rem;text-align:center;color:#94a3b8;margin-top:1rem;">
        <div style="font-size:2rem;margin-bottom:0.75rem;">📂</div>
        <div style="font-size:0.95rem;font-weight:600;color:#475569;margin-bottom:0.25rem;">Upload your billing file to get started</div>
        <div style="font-size:0.8rem;">Standard GoFleet / ZenduIT monthly billing export (.xlsx)</div>
    </div>""", unsafe_allow_html=True)
