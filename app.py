from flask import Flask, request
from flask_cors import CORS
import budget_proposal
from version import get_version_info
from contextman import NHSGoogleSheets
from hashlib import sha256
from dotenv import load_dotenv
import os
import smtplib
from functions import get_stats_and_upcoming_events
from utils import send_email, convert_numpy_types

load_dotenv()
app = Flask(__name__)

CORS(app, expose_headers=['Content-Disposition', 'Content-Type'])

# for reference
cols = ["event_name", "event_chairs", "contact_email", "event_start_date", "event_type", "itemized_budget", "expected_revenue", "justification", "purpose", "nhs_fund_reason", "estimated_attendance", "vendors_suppliers", "reimbursement_contact",
        "PROP_ID", "NOTES", "APPSTATUS"]

def get_email_body(name: str, propid: str) -> str:
    return """<div style="margin: 20px 50px 20px 50px; display: flex; flex-direction: column;">
    <div style="display: flex; align-items: center; flex-direction: column; margin-bottom: 50px">
        <img src="https://biph-nhs-treasury.netlify.app/assets/nhs-logo-DVUP6B8n.png" style=
        "height: 100px; margin-top: 50px;"/>
    </div>
    <p style="font-family: Roboto">
        Dear __NAME__,
    </p>
    <p style="font-family: Roboto">
        Your budget proposal for __EVENT_NAME__ is received.
    </p>
    <p style="font-family: Roboto">
        Your <strong>Proposal ID</strong> is: __PROP_ID__
    </p>
    <p style="font-family: Roboto">
        If you have any questions, please reach out to <a style="color: #02437A" href="mailto:eddy12597@163.com">eddy12597@163.com</a>.
    </p>
    <p style="font-family: Roboto">
        Best Regards,
    </p>
    <p style="font-family: Roboto">
        Eddy Zhang
    </p>
    <p style="font-family: Roboto">
        Treasurer, BIPH Chapter of the NHS
    </p>
    <p style="font-family: Roboto; font-size: 10px">
        This email is automatically generated from a template and sent via an automated script, so it may contain errors. If this email was not meant to be delivered to you, please reach out to the above email, and you may ignore this email.
    </p>
</div>""".replace("__NAME__", name).replace("__PROP_ID__", propid)

@app.route('/')
def index():
    version_info = get_version_info()
    return f"Backend is running! Use /submit-budget-proposal to submit.\n\n{version_info}"

@app.route('/submit-budget-proposal', methods=['POST'])
def handle_submit_budget_proposal():
    data = request.form
    prop = budget_proposal.BudgetProposal.from_dict(data)
    if prop is None:
        return "Failed to parse proposal", 400
    
    with NHSGoogleSheets("NHS Treasurer 2026") as sheets:
        sheets.append_row("Proposals", prop.to_row())
        proposals_df = sheets.get_df("Proposals")
        
        recipient = proposals_df.iloc[-1]["contact_email"]
        name = proposals_df.iloc[-1]["event_chairs"]
        propid = proposals_df.iloc[-1]["PROP_ID"]
        
    try:
        send_email(recipient, get_email_body(name, propid))
    except Exception as e:
        return f"Server Error: {e}", 500
    
    return 'Success', 200

@app.route("/get-stats-and-upcoming-events", methods=['GET'])
def stats():
    # frontend needs current balance, num pending (prop, reimbursements), num approved (prop, reimbursements)
    try:
        data = get_stats_and_upcoming_events()
        return data, 200
    except Exception as e:
        print(f"Exception: {e}")
        return str(e), 500


"""
        transactions_df = sheets.get_df("Transactions")
        last_row = transactions_df.iloc[-1]
        data_string = f'{last_row["Timestamp"]}{last_row["From"]}{last_row["To"]}{last_row["Amount"]}{last_row["PrevHash"]}'
        salt = os.getenv("HASH_SALT")
        if salt is None:
            return "Failed to get Hash Salt", 500
        new_hash = sha256((data_string + salt).encode()).hexdigest()
        
"""


@app.route("/get-logs", methods=['GET', 'POST'])
def get_logs():
    with NHSGoogleSheets("NHS Treasurer 2026") as sheets:
        transactions_df = sheets.get_df("Transactions")
        data = transactions_df.to_dict(orient="records")
    return {
        "data": data
    }, 200




# if __name__ == "__main__":
#     app.run(debug=True)