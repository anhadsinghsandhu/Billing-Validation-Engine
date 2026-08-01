import os
import urllib.request
import urllib.parse
import json
import pandas as pd
from datetime import datetime


ZOHO_TOKEN_URL = "https://accounts.zohocloud.ca/oauth/v2/token"
ZOHO_API_BASE = "https://www.zohoapis.ca/books/v3"


def get_access_token():
    """Get a fresh access token using client credentials."""
    client_id = os.environ.get("ZOHO_CLIENT_ID")
    client_secret = os.environ.get("ZOHO_CLIENT_SECRET")
    org_id = os.environ.get("ZOHO_ORG_ID")

    if not all([client_id, client_secret, org_id]):
        raise ValueError("Missing Zoho credentials. Set ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, and ZOHO_ORG_ID environment variables.")

    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "ZohoBooks.invoices.READ,ZohoBooks.contacts.READ,ZohoBooks.settings.READ",
        "soid": f"ZohoBooks.{org_id}",
    }).encode()

    req = urllib.request.Request(ZOHO_TOKEN_URL, data=data, method="POST")
    with urllib.request.urlopen(req) as r:
        token_data = json.loads(r.read())

    if "access_token" not in token_data:
        raise ValueError(f"Failed to get access token: {token_data}")

    return token_data["access_token"]


def fetch_invoices(token):
    """Fetch all invoices from Zoho Books."""
    org_id = os.environ.get("ZOHO_ORG_ID")
    url = f"{ZOHO_API_BASE}/invoices?organization_id={org_id}&per_page=200"

    req = urllib.request.Request(url, headers={"Authorization": f"Zoho-oauthtoken {token}"})
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())

    return data.get("invoices", [])


def fetch_contacts(token):
    """Fetch all contacts from Zoho Books."""
    org_id = os.environ.get("ZOHO_ORG_ID")
    url = f"{ZOHO_API_BASE}/contacts?organization_id={org_id}&per_page=200"

    req = urllib.request.Request(url, headers={"Authorization": f"Zoho-oauthtoken {token}"})
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())

    return data.get("contacts", [])


def map_zoho_to_billing_df(invoices, contacts):
    """
    Map Zoho Books invoice data to the billing DataFrame format
    that the 29 validation rules expect.
    """
    today = datetime.today().date()

    # Build a contact lookup for additional info
    contact_map = {c["contact_name"]: c for c in contacts}

    rows = []
    for inv in invoices:
        customer = inv.get("customer_name", "Unknown")
        contact = contact_map.get(customer, {})

        # Map Zoho status to our expected format
        zoho_status = inv.get("status", "draft")
        status_map = {
            "sent": "Active",
            "draft": "Active",
            "overdue": "Active",
            "paid": "Active",
            "void": "Inactive",
            "unpaid": "Active",
            "partially_paid": "Active",
        }
        account_status = status_map.get(zoho_status, "Active")

        # Map payment status
        payment_map = {
            "paid": "Paid",
            "overdue": "Overdue",
            "partially_paid": "Partial",
            "sent": "Unpaid",
            "draft": "Unpaid",
            "void": "Unpaid",
        }
        payment_status = payment_map.get(zoho_status, "Unpaid")

        # Parse dates
        invoice_date = inv.get("date", str(today))
        due_date = inv.get("due_date", str(today))

        try:
            contract_end = datetime.strptime(due_date, "%Y-%m-%d")
        except Exception:
            contract_end = datetime.today()

        try:
            contract_start = datetime.strptime(invoice_date, "%Y-%m-%d")
            # Estimate contract start as 1 year before invoice date for demo
            from datetime import timedelta
            contract_start = contract_start - timedelta(days=365)
        except Exception:
            contract_start = datetime.today()

        total = float(inv.get("total", 0))
        balance = float(inv.get("balance", 0))

        row = {
            "Customer": customer,
            "Region": "North America",
            "Entity": "GoFleet",
            "Product": "SaaS",
            "Account Status": account_status,
            "Contracted Price ($)": total,
            "Actual Invoice ($)": total,
            "Usage Qty": 0,
            "Expected Usage Charge ($)": 0,
            "Product Cost ($)": round(total * 0.3, 2),
            "Vendor Cost ($)": round(total * 0.15, 2),
            "Gross Margin %": 0.55,
            "Prior Month Invoice ($)": round(total * 0.9, 2),
            "Payment Status": payment_status,
            "Credit Issued ($)": 0,
            "Sales Owner": contact.get("owner_name", ""),
            "CS Owner": "",
            "Contract Start": contract_start,
            "Contract End": contract_end,
            "Billing Frequency": "Monthly",
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Convert date columns
    for col in ["Contract Start", "Contract End"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Convert numeric columns
    for col in ["Contracted Price ($)", "Actual Invoice ($)", "Usage Qty",
                "Expected Usage Charge ($)", "Product Cost ($)", "Vendor Cost ($)",
                "Gross Margin %", "Prior Month Invoice ($)", "Credit Issued ($)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Fill text columns
    for col in ["Account Status", "Payment Status", "Product", "Billing Frequency",
                "Region", "Entity", "Sales Owner", "CS Owner"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    return df


def load_from_zoho():
    """
    Main function called by app.py.
    Returns a DataFrame in the same format as load_data() expects.
    """
    token = get_access_token()
    invoices = fetch_invoices(token)
    contacts = fetch_contacts(token)

    if not invoices:
        raise ValueError("No invoices found in Zoho Books. Please create some invoices first.")

    df = map_zoho_to_billing_df(invoices, contacts)
    return df, len(invoices)
