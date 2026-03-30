import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("key_file.json", scope) # type: ignore
client = gspread.authorize(creds) # type: ignore

workbook = client.open("NHS Treasurer 2026")
proposals_sheet = workbook.worksheet("Proposals")
transactions_sheet = workbook.worksheet("Transactions")

proposals_df = pd.DataFrame(proposals_sheet.get_all_records())

print(proposals_df.head())