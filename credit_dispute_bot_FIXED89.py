
import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="Credit Dispute Chatbot", layout="centered")
st.title("🤖 AI Credit Dispute Chatbot")

with st.expander("🔍 How We Score Your Credit Report"):
    st.markdown("""
We analyze your credit report and prioritize negative items for dispute using the following criteria:

### 📊 Scoring Breakdown
- **Age of Item**
  - 🟢 Older than 12 months = +2 points (more likely to be removed)
  - 🟡 Less than 12 months = +1 point

- **Account Type & Status**
  - 🔴 Charge-Off or Collection = +3 points
  - 🔶 Multiple Late Payments = +2 points
  - ⚠️ Balance exceeds limit = +2 points

- **Recency**
  - 🕒 Recently added collections = +1 point

### 🏆 What This Means
The higher the score, the more likely the item is:
- Legally challengeable
- Missing documentation
- Impacting your credit score

We recommend starting with the **highest scoring items first**.
""")

def months_since(date_str):
    report_date = datetime.strptime(date_str, "%Y-%m-%d")
    today = datetime.today()
    return (today.year - report_date.year) * 12 + (today.month - report_date.month)

def score_item(item, category):
    score = 0
    reasons = []
    months_old = months_since(item["last_reported"])

    if months_old > 12:
        score += 2
        reasons.append("Older than 12 months")
    else:
        score += 1
        reasons.append("Recent negative reporting")

    if category == "tradelines":
        if item["balance"] > item.get("credit_limit", 1):
            score += 2
            reasons.append("Balance exceeds limit")
        if "charge" in item["status"].lower() or "off" in item["status"].lower():
            score += 3
            reasons.append("Account charged off")
        if "late" in item["status"].lower():
            score += 2
            reasons.append("Multiple late payments")

    if category == "collections":
        score += 3
        reasons.append("Collection account")
        if months_old < 6:
            score += 1
            reasons.append("Recently added")

    return {
        "category": category,
        "creditor": item.get("creditor_name") or item.get("agency_name"),
        "status": item["status"],
        "balance": item.get("balance", item.get("amount")),
        "score": score,
        "reasons": reasons
    }

def generate_dispute_letter(consumer_info, item):
    name = consumer_info["name"]
    address = consumer_info["address"]
    creditor = item["creditor"]
    reasons_text = ", ".join(item["reasons"])
    account_status = item["status"]
    balance = item["balance"]

    return f"""To Whom It May Concern,

My name is {name}, and I am writing to formally dispute an item on my credit report. I have reviewed the information on my report and have identified the following account that I believe is inaccurate or requires further verification:

Creditor: {creditor}  
Status: {account_status}  
Reported Balance: ${balance}  

Reason for Dispute: {reasons_text}.

Under the Fair Credit Reporting Act (FCRA), I am requesting that you conduct a thorough investigation and provide verification of this account. If you cannot verify the accuracy, I respectfully request that the item be deleted from my credit file.

Please mail me a copy of the results of your investigation to the address listed below:

{address}

Thank you for your time and attention to this matter.

Sincerely,  
{name}
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

st.chat_message("assistant").write("Welcome! Please upload your JSON credit report to begin.")

uploaded_file = st.file_uploader("Upload JSON Credit Report", type="json")
if uploaded_file:
    try:
        data = json.load(uploaded_file)
        consumer_info = data["consumer_info"]
        recommendations = []

        for item in data.get("tradelines", []):
            recommendations.append(score_item(item, "tradelines"))
        for item in data.get("collections", []):
            recommendations.append(score_item(item, "collections"))

        recommendations = sorted(recommendations, key=lambda x: x["score"], reverse=True)

        st.chat_message("assistant").write(f"✅ Report received. Found {len(recommendations)} dispute-worthy items:")

        for i, item in enumerate(recommendations, start=1):
            st.chat_message("assistant").write(
                f"**{i}. {item['creditor']}**  \nStatus: {item['status']}  \nBalance: ${item['balance']}  \nReasons: {', '.join(item['reasons'])}"
            )

        st.subheader("📨 Dispute Letters")
        for i, item in enumerate(recommendations, start=1):
            letter = generate_dispute_letter(consumer_info, item)
            with st.expander(f"View Letter {i}: {item['creditor']}"):
                st.text_area("Dispute Letter", letter, height=300)

    except Exception as e:
        st.chat_message("assistant").write(f"⚠️ Error reading report: {e}")
