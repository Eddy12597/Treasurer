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
import json
import sys
import hashlib
import threading
from queue import Queue

if 'win' not in sys.platform:
    load_dotenv(dotenv_path="/home/eddy12598/Treasurer/.env")
else:
    load_dotenv()
app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# for reference
cols = ["event_name", "event_chair", "contact_email", "event_start_date", "event_type", "itemized_budget", "expected_revenue", "justification", "purpose", "nhs_fund_reason", "estimated_attendance", "vendors_suppliers", "reimbursement_contact",
        "PROP_ID", "NOTES", "APPSTATUS"]



def get_email_body(name: str, propid: str, event_name: str, event_chair: str, event_start_date: str, event_type: str,
                   itemized_budget: dict, expected_revenue: str, estimated_attendance: str, vendors_suppliers: str, reimbursement_contact: str) -> str:
    res =  """<div style="margin: 20px 50px 20px 50px; display: flex; flex-direction: column;">
    <div style="display: flex; align-items: center; justify-content: center; gap: 50px; margin-bottom: 50px">
        <img src="https://biph-nhs-treasury.netlify.app/assets/nhs-logo-DVUP6B8n.png" style=
        "height: 100px; margin-top: 50px;"/>
        <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAWIAAABkCAMAAACLrMrhAAAAe1BMVEUAAAAnSZwoSJ8nSZ0oSJsgUJ8mSpsoTJsmSZwmSp0mSpwnSZsoSp0rSpomSZwmSZwlSp0lSZwmSZwoSJ0mSZwmSp0nSZwmSJslSZ0mSpwlSJ0nSZ0lSpooUJ8nSpwmSpwnSJsmS54mSJ4mSJwnSZwnSZsmSJ0oSJsmSZwYfxBoAAAAKHRSTlMAvyDfQBCAQN+f73BgMFCgYJDvYM9/r4CPz2CPMCBvr7BfX6CQwJ+AeoaNAgAADqhJREFUeF7tnfmaoroWxc2wGRJAUZxq6j63z7k37/+E15iEBYIylP0d7c/1TwkZxB9hZ2cnpBZj9VnodFcJZU5Sgu0OOqbFvfRSrHfK9KhKV3wxX0XmFbcSZBTlzWPSaXqov4hnWUil7JAeNP8D+B6UuaFq/m9kJihZLSBhDFtAB+OUOpaZMZFL+PLXxZ4bMm2VGRRbzUUMadxSeyhBGHnyFuItEuQTN2BmxilJ+TzEG3lSsTNmTSEhtdDScMQtflrkG2FKtGLf2Eta8FPC7o8BLHal3hRnJpuoZKqdmvI5iCU+gSk7GhOI6xq3JiB2jf2nS9g8q6HgTcCKaUkdIyLLZp5kOx/xDyBOjXnTxkRAXKJEGzF7chvc4FsC76X4ZteAvJqJmAuTLBb4SMqsqSa6XvUh/jDGbJ/ZixDoywrwvUJZTLUWQFxmJ22FMW8gePoY1f0f2coT5xwCsS9t1A4Jz6UDmI3qrAE5kfM8ireGx3aCxmEFcgG3pYWY+4Rq9axWGB7nNMjbWYjNew0whQ1x2hyRBYhtgqvg+TyKPNCq0CKnQE5pii3mVsXRAvSnVvFJ21ZnxoulrX0FxF7kEqLnIvyXd8aUntr4l8FY8PGIc49KOTeNm4b4Ze0/gbihvTHJUxH+Ck0YnCY35ISPb8X4yJ3HBpWOfsNfBuJGAhmzfh6+GJWWNMuKg/E0xNy1Ym77Sy/vt3HhjXt8ibhKeWBfPWEb1nMrKMF4FGIdn1RshXvYt41vLh3K6pSi48/Pwjl2QHywvtwpwfqX6RPZYW+G5fwq9hMYMwMpHjw2L+mef60wsml5FJY5jP+zKFfA813GFU1BrBiHx9Y2I3zpIe/owi/ei6cLZnJxlzaxMVZjHt4P6ZVTOCakcik9O6mjaEOt00h4qpC8wBP7Lekr9vylLeLe39S+t6aXiju2vaWzOPSi2mOI93cBQMcQVIBeSuEX3UFcXc6pvcQHurp5XV6FhJeO93YCWLvClzKYiXuaCswrvyQQPbyXImMVIeHViO8dTCEx2IxXjBX2IGX1GDhnLLKFGeQzXZ5AlgOvy763qg7KhIhClqYKd+YQ8vGDveYKE5AHXBjZfPCYRCNAoBnLhy3xvRsxBtLR7Ya+ulhhFbs7zQ3kM7VPIAsms2L3CVUHifpWx516Y3z3AbNc6FASQrga96z1w5YDrhO+OP0t1icZh9i8j0AsggqXRdkDFZhgpRYQg2t0CzE66CM7NoJYDFiA2F/wehLi9P6NGI6bHIfY/AeIW7PRQbhbF7+Z2/E6BX4JB2K0RR/fByF3AMSuDZcUJsjeQV13EGe2QlNMQEzjGzFlh0oYJUbFD0lhengY8ZpPRwyGq4DYVDViZExx2IvYF35rxFgkPE8JxAiz4nAM4gwVjV4GS6OdijWNQbyzVm8yYtQTubL/CGPeA2I8oxKZryH+0fxi5k8yd2E8IMY9O2Mej5jBZo5bXjF2PlLCkg4hJmHZTkUMiNqXld7kADG3BUHkGmJYSsy42FLc4u58nbRZdqMRE6Z7b+lLGYhNGOL9HIP4PFTRtxGvmVfeRpw7PK6stiYnIMYKLjzY/Yg/2ndQWeAOMXcPBhBzlxWrR4cRF2OCu7QzEG7IKEsxCrFlY/JbiCEZfmlkxfz1+LLLs8kBYuHYsUCkH3HsESNH7hEv3IMBxNoZbaweHUacjrATVBkvVm42uiwWEyyFHIV4UVo2NxELL48Y+rUAYrKWHYgzexJEprfihXswPGLcM6weHUZ8HOFP+Das9rSYJAWvZwCxuxA2yRZjYVgDsTM5DrGjVLGTKnS8fYjJd+GoO9hi9+uTj4A4CxbLfs04xISVkVe1nbt+ZQljPIDYs9lNQcw459bM5UAchpXMIz6RgaIb3R3zycFH/tlATOJcIfOFoWoc4njYFPMrc07ER40+1iMQw65M8iiCfQFiqxKeTArzggr6EG8aEPKGX8zDzYf/rISTsrmAeAYFKO2fc/pSN0PuaEQ0EvFiPwMx1as6YWQYAhkoBb+tg9gnr1e175SGcxzxFuZZFOhp2CjES+C72YgvccYVGvaAFSqGEQPDCKeNFUDsFtgUbcRceMRpwwQWvkAXMcokaXRQ9i8Bcf1gsPqeoafJHcGKeV3zXZmcFmvAOGRNY0JBq9GISdxADK0aiH2PD8RW0mcS5xSM5+UVxPhJWHgExKEvru8Zrr88I4b6ISTTR3944fF9qOytgKYWwoWChQgJ+VH8jcJCALFwQqRNiDC8+iHEf61VEq4sqi6EKFtf979QL0yZrwar7hVa3BIXwI82HzFR8cuw8d8C6v+diyF1okRZADwcn1ui7DOIcvlvrN/6uHyBlpnxQ+kSXttLA17dqmHSnFI2IkIXjY9ovBC3qdkuUo6YttajEb8Q65aXoN4wrI6GYtHtu/BSfLAE2QoJ/LK7k2pPrbUSExC/lInu4n7qBOGps1biZSjm7I6Apavo1vqdjXRkd/cST01Lu4v+bdbUdflCfGuHGglj3B9pKIanrn8M5PjsbL5EhY50Qf4ojl0qPvoDnaYRjrEdU1RwHMdx/jCA8YqVSjebyB2UbUux5v2rvvnMATTCAirlnUfJn8KwvxmAiVnPBhjUKIoA8uMZ4ZIArwrJOXrALuH9jGkP1OC1LvydVugLiquIt6YZsPHKG0XzR0NMB+PF8uZ6tOT6O6GYka5GBDPl9SZebWSxFLZmz8SosjidsveuixiEk30htWjYea5s0Y0rus4fC/FWdbfroDY9Ep1nkIH64LCFrvEPbsv+rW7VFfeBrV/XDEUGG6ZhhUR9Ldx+pIdCzPqmPpXvpdBGvFiUZfqg4D3PnlLpvh++bbiKRNcQi4Zx0mHkk50J42Kjh0Ise6KSH3i+Yek6Gt5R4cctn40uzbToTtN2Ecett82Yr+J4ESpnj4MYoYb3y5a9y+EmoWuCxsxIi5sOBbP8ddxE3hOrjp0yj1iDG44I5ghHj4IYVoBfDina/hRfmraYHBlqlgPv+qnUUcaKHMhAPnXZumfF1cU8j4QYwzdMfEIwcYAMwAMqB2a3SQvMT81AjMU8HcTygRDDYZBw4aCW5eOb3VEYcUw1japYDM955HoXjAlH1K6JeOOkLUXMSSKSx3zRBaQexVBAGzQSjKOPDE1snj6GFxqFZe5rT0YOdncSNLHuFUVhcYD4gRy3CLsMJpqw7QHNRJyOKo3Z/NKYahAxKUsVJw33bbuiRnXpQyGG47Zmxknp1rBOz7c/N3/k9p1aDzZXdXY6VHTFL9a4Iu5gevAp1bGKhAPxo2jZdsYmvAYy/wWHLxvH4c76VzW9ZJXTp+0GWQ9iLBmKaZFvlYOJonxxLmp0MBi72Iv/64hJwVfILzss9hteCsPOSqIRKd2bWurtGmI69vg7KIrQVGyg1UM4bghUQGr+OohssLPjS+D02gjc6C7iDs4dNeOx+AkPiZgErrmD6e6NGF5gyljbBSxKxtJ9oBRFwQmmKNKNcuwodvu8DaBYMnFMJXJFUP4wPV5CvUH3GdrikX3pwnGDYjEfE+/esZdyTB+1hnnJN24YTMxLcIJ3iNR/Y2e8r7678xIpOLIY5vFvB++gl3SIuPHmdOl896S8kvzahGm7NfAwZ2n36utuOW6Q2s/eGvJlJkbtKFzSbMIvl3igm8KsxkzCYw0xj53ywTvf/0ig5GwR6uBDsaI7eUgRluJ8j3BFE8J7yXYOYv7dBYmId2LjkN+PmBSWVHyHcMKnRVAr+tMRQxss+ZkhSkF4FOLUzspZ1NEfjxgqYYR/9z+dWIYY4ybMx1GeZQVvmtpYExDn9tQNxJ9FlsUwrXQqHcHkURxFBR+BmBrVkLXQVOiA2NZIKE/uepG1sUw3t38+9V1jfF8KhMcixuQdRjwpBYLcwfWIv1A1EHe+PilC5QWrrwarPrdDiDPW7B8yY6JcmMQh5q5G3V68y3idFc3dvQd8uGukmjMsw5qG2DOEW84Cwco0EP8FXEDc53FKjzhBHMtFTYQA46uItfHaem6pMAGx8Em67X+t8yuItwaI77jA8xctpiLmfn601DnPN8JB4o52GgxFDML9iGVZcC6X2MLAlDzfm7o2JZ0pk23EVeTEPCFim9yVozApoZgzFLZGN1fDnVkMx2vej1gZUeZ3fNUJI46JiKlqwZLY1FHJupHnyig+1N2FzL4v9aij8Ao+KgdiyBNCo9aWG0xN7ezv3Idt+LF7d9xBPJIGjQJ8nB7VwEYOlWXJ8eqHRecRv9XUpNv84SZiirOsyEtjpEMrGxbyaNbYPWkAcW6rKdxhhkhA/Um6GXMRqlwos+5HnI56ySZZ0fgXcX7RvJUFSd6y5lhEVSNWwcYOdnemDzE2yFLGtBH/I53OzR1xXFUjZh2n7XxlhJRTUd6LWI59/HfXKX9qhwVNeBpiYbXTFFw+pjdRd38/5n7ymm4h3p7fRNBLcQUxdLO74+dqNuWxRhz1IrYZKyyjznsR04Q3HVkUUwdvdhAGmjgmDBSgLCyf60VclMbsriPGDipRF7FLHTP0wOY/cRdxQPbh4LqN2gAz87aagHiIgGSmJcXSSGdFXNhXEdIK5gGA5yMGmwXvQ6zPcX59A3E4SnsRl57cggYQMw8m6yIOTSB1LMtw/OUqKTzabBgxJJdmUAD8XcTaXTJVl4jhNq95G3GSeZ2SlUv9q98Wc+U2sIrF+23EP9y+plz0ITZpvsh3wWlT5+PPgz8ma1Pjz60agxjiS2EGxTQAfwMx2WtLU6V6Ebtmw1qIoZULEu5SZtQlYowolH30VH4TsTw748yYHsRr0fJMNyborbknYzISMSRvU2Z7tKxZiKFcOO/iGmKYii7iega97LXFWMvF8oHR3d5l6zMUCf8RFq7igtHNE3PD6fGIoVwzZXok0g0t5os4vyheRNGJi5QWA9k/Th9SOqg4dc4AOZdER5psJnJlyJfhqF3Li0uoU5GRb2w2l4Kz/rKk1pJQXupGlS7VZ7R/JnpYeRGl7Oh9RnHclfiqm3rp/1T7DdcX2IUNAAAAAElFTkSuQmCC" style="height: 80px; margin-top: 50px;"/>
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
    <p style="font-family: Roboto; margin-bottom: 30px;">
        Below is a receipt of the submitted proposal:
    </p>
    <div style="width: 70%; margin: 0 20px 0 20px; font-family: Roboto; font-size: 13px; border: black 1px solid; padding: 10px 20px 10px 20px; border-radius: 5px;">
        <p style="font-size: 15px; text-decoration: underline;">
            Section 1
        </p>
        <p style="margin-left: 10px;">
            Event Name: __EVENT_NAME__
        </p>
        <p style="margin-left: 10px;">
            Event Chair: __EVENT_CHAIR__
        </p>
        <p style="margin-left: 10px;">
            Event Start Date: __EVENT_START_DATE__
        </p>
        <p style="margin-left: 10px;">
            Event Type: __EVENT_TYPE__
        </p>
        <p style="font-size: 15px; text-decoration: underline;">
            Section 2
        </p>
        <p style="margin-left: 10px;">
            Itemized Budget:
        </p>
        <ul>
           __ITEMIZED_BUDGET__
        </ul>
        <p style="margin-left: 10px;">
            Expected Revenue: __EXPECTED_REVENUE__
        </p>
        <span style="font-size: 15px; text-decoration: underline">
            Section 3
        </span>
        <span style="font-size: 15px; margin-left: 2px; ">
            is omitted.
        </span>
        <p style="font-size: 15px; text-decoration: underline">
            Section 4
        </p>
        <p style="margin-left: 10px;">
            Estimated Attendance: __ESTIMATED_ATTENDANCE__
        </p>
        <p style="margin-left: 10px;">
            Vendors / Suppliers: __VENDORS_SUPPLIERS__
        </p>
        <p style="margin-left: 10px;">
            Reimbursement Primary Contact: __REIM_CONTACT__
        </p>
    </div>
    <p style="font-family: Roboto">
        If you have any questions, please reach out to <a style="color: #02437A" href="mailto:eddy12597@163.com">eddy12597@163.com</a>.
    </p>
    <p style="font-family: Roboto">
        Best Regards,
    </p>
    <p style="font-family: Roboto">
        BIPH NHS Treasury
    </p>
    <p style="font-family: Roboto; font-size: 10px">
        This email is automatically generated from a template and sent via an automated script, so it may contain errors. If this email was not meant to be delivered to you, please reach out to the above email, and you may ignore this email.
    </p>
</div>"""\
    .replace("__NAME__", name)\
    .replace("__PROP_ID__", propid)\
    .replace("__EVENT_NAME__", event_name)\
    .replace("__EVENT_CHAIR__", event_chair)\
    .replace("__EVENT_START_DATE__", event_start_date)\
    .replace("__EVENT_TYPE__", event_type)\
    \
    .replace("__EXPECTED_REVENUE__", expected_revenue)\
    .replace("__ESTIMATED_ATTENDANCE__", estimated_attendance)\
    .replace("__VENDORS_SUPPLIERS__", vendors_suppliers)\
    .replace("__REIM_CONTACT__", reimbursement_contact)

    itemized_budget_str = ""
    
    for k, v in itemized_budget.items():
        itemized_budget_str += f"<li>Item Name: {k} | Item cost: ￥{v}</li>"
    res = res.replace("__ITEMIZED_BUDGET__", itemized_budget_str)
    
    return res


@app.route('/')
def index():
    version_info = get_version_info()
    return f"Backend is running! Use /submit-budget-proposal to submit.\n\n{version_info}"

@app.route('/submit-budget-proposal', methods=['POST'])
def handle_submit_budget_proposal():
    data = request.get_json()
    prop = budget_proposal.BudgetProposal.from_dict(data)
    if prop is None:
        return "Failed to parse proposal", 400
    
    with NHSGoogleSheets("NHS Budget Proposals") as sheets:
        sheets.append_row("Proposals", prop.to_row())
        proposals_df = sheets.get_df("Proposals")
        row = proposals_df.iloc[-1].fillna("__ERROR__")
    
    recipient = row["contact_email"]
    name = row["event_chair"]
    propid = row["PROP_ID"]
    event_name = row["event_name"]
    event_chair = row["event_chair"]
    event_start_date = row["event_start_date"]
    event_type = row["event_type"]
    
    # Process itemized_budget
    raw_budget = row["itemized_budget"]
    if isinstance(raw_budget, dict):
        itemized_budget = raw_budget
    else:
        try:
            # Clean up potential Google Sheets formatting issues
            clean_str = str(raw_budget).replace('""', '"')
            if clean_str.startswith('"') and clean_str.endswith('"'):
                clean_str = clean_str[1:-1]
            itemized_budget = json.loads(clean_str)
        except Exception:
            try:
                import ast
                itemized_budget = ast.literal_eval(str(raw_budget))
            except Exception as e:
                print(f"Final fallback failed: {e}")
                itemized_budget = {}

    expected_revenue = row["expected_revenue"]
    estimated_attendance = row["estimated_attendance"]
    vendors_suppliers = row["vendors_suppliers"]
    reimbursement_contact = row["reimbursement_contact"]
    
    try:
        email_content = get_email_body(name, propid, event_name, event_chair, event_start_date, 
                                       event_type, itemized_budget, expected_revenue, 
                                       estimated_attendance, vendors_suppliers, reimbursement_contact)
        send_email(recipient, email_content, debug=False)
    except Exception as e:
        print(f"Email error: {e}")
        return f"Server Error: {e}", 500
    
    return 'Success', 200

def find_nonce(transaction_data: str, prev_hash: str, target_prefix: str = "0000000") -> tuple[int, str]:
    """
    Brute‑force a nonce so that:
        SHA256(transaction_data + prev_hash + str(nonce))
    starts with target_prefix.
    Returns (nonce, final_hash)
    """
    
    # 5 zeros: 0~2 s
    # 6 zeros: 5~15s
    nonce = 0
    for _ in range(100_000_000): # ~1 minute
        data_to_hash = f"{transaction_data}{prev_hash}{nonce}"
        h = hashlib.sha256(data_to_hash.encode()).hexdigest()
        if h.startswith(target_prefix):
            return nonce, h
        nonce += 1
    raise TimeoutError(f"Cannot find nonce for {transaction_data}, with previous hash {prev_hash}. Timeout after nonce={nonce}")

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
    with NHSGoogleSheets("NHS Budget Proposals") as sheets:
        transactions_df = sheets.get_df("Transactions")
        # transactions_df["PrevHash"][0] = "0" * 64
        transactions_df.loc[0, "PrevHash"] = "0" * 64
        data = transactions_df.to_dict(orient="records")
    return {
        "data": data
    }, 200

transaction_queue = Queue()

def mine_block(Timestamp, From, To, Amount, Notes, PrevHash, max_trials: int = 500_000_000, prefix="000000"):
    # Pre-encode static data to speed up loop
    encoded_base = f"{Timestamp}{From}{To}{Amount}{Notes}{PrevHash}"
    print(f"Mining started for encoded base:\n{encoded_base}")
    x = max_trials / 20
    for i in range(max_trials):
        h = hashlib.sha256(f"{encoded_base}{i}".encode()).hexdigest()
        if h.startswith(prefix):
            return i, h
        if h.startswith(prefix[:-1]):
            print(f"{i}: {h}")
    raise TimeoutError(f"Could not get nonce for transaction data: {encoded_base}. Timeout after {max_trials} trials.")

mining_results = {} # key=PrevHash, value=tuple[status: str, Nonce: str, hashval: str]

def worker():
    while True:
        # 1. Get the next transaction from the queue
        js = transaction_queue.get()
        print(f"Received: {js}")
        
        # 2. Re-fetch the LATEST hash from the sheet RIGHT BEFORE mining
        with NHSGoogleSheets("NHS Budget Proposals") as sheets:
            df = sheets.get_df("Transactions")
            latest_prev_hash = df.iloc[-1]["Hash"]
            latest_balance = df.iloc[-1]["Balance"]
        
        try: 
            latest_prev_hash = str(latest_prev_hash.item()) if hasattr(latest_prev_hash, 'item') else str(latest_prev_hash)
            latest_balance = float(latest_balance.item()) if hasattr(latest_balance, 'item') else float(latest_balance)
        except: 
            latest_prev_hash = str(latest_prev_hash)
            latest_balance = float(latest_balance)
        
        # 3. Mine the block
        data = f"{js['Timestamp']}{js['From']}{js['To']}{js['Amount']}{js['Notes']}{latest_prev_hash}"
        
        nonce, hashval = mine_block(js["Timestamp"], js["From"], js["To"], js["Amount"], js["Notes"], latest_prev_hash)
        
        # Calculate new balance
        amount = float(js["Amount"])
        if js["From"] == "Treasury":
            balance_change = -amount
        elif js["To"] == "Treasury":
            balance_change = amount
        else:
            balance_change = 0
        
        new_balance = latest_balance + balance_change
        
        # 4. Write to Google Sheets immediately - USE SCALAR VALUES, NOT SERIES
        with NHSGoogleSheets("NHS Budget Proposals") as sheets:
            sheets.append_row("Transactions", [
                js["Timestamp"],
                js["From"],  
                js["To"],  
                float(js["Amount"]),
                "N/A",
                float(new_balance), 
                js["Notes"],  
                latest_prev_hash, 
                float(nonce), 
                data, 
                f"{data}{latest_prev_hash}{nonce}", 
                hashval, 
                "Yes"
            ])
        
        transaction_queue.task_done()
        print("Task done!")

threading.Thread(target=worker, daemon=True).start()

@app.route("/add-transaction", methods=['POST'])
def add_transaction():
    js = request.json
    if js is None:
        return "Failed to parse transaction", 400
    # required: Timestamp, From, To, Amount, Notes
    try:
        js["Timestamp"], js["From"], js["To"], js["Amount"], js["Notes"] # pyright: ignore[reportUnusedExpression]
    except KeyError:
        return "Missing fields", 400
    transaction_queue.put(request.json)
    print(f"queued: {request.json}")
    return {"status": "queued"}, 202
    