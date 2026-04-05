import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from contextman import NHSGoogleSheets

def main():
    with NHSGoogleSheets("NHS Treasurer 2026") as sheets:
        proposals_df = sheets.get_df("Proposals")
        print(proposals_df.head())

main()