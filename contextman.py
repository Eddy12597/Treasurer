import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from copy import deepcopy

class NHSGoogleSheets:
    def __init__(self, sheet_name, json_keyfile="key_file.json"):
        self.sheet_name = sheet_name
        self.json_keyfile = json_keyfile
        self.client = None
        self.workbook = None
        self.sheets = {}  # Store sheet objects
        self.data = {}    # Store pandas DataFrames (local cache)
    
    def __enter__(self):
        # Connect to Google
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.json_keyfile, scope) # type: ignore
        self.client = gspread.authorize(creds) # type: ignore
        self.workbook = self.client.open(self.sheet_name)
        
        # Load all sheets into local cache
        for worksheet in self.workbook.worksheets():
            sheet_name = worksheet.title
            self.sheets[sheet_name] = worksheet
            # Read all data into pandas DataFrame
            records = worksheet.get_all_records()
            self.data[sheet_name] = pd.DataFrame(records)
        
        return self
    
    def get_df(self, sheet_name) -> pd.DataFrame:
        """Get DataFrame for a sheet (read from local cache)"""
        if sheet_name not in self.data:
            raise RuntimeError(f"Cannot find sheet name: {sheet_name}\n\tin: {self.data}")
        return self.data[sheet_name].copy()
    
    def update_cell(self, sheet_name, row, col, value):
        """Update a single cell (immediate write)"""
        self.sheets[sheet_name].update_cell(row, col, value)
        # Also update local cache
        self.data[sheet_name].iloc[row-2, col-1] = value  # -2 because header is row1
    
    def replace_sheet(self, sheet_name, df):
        """Replace entire sheet with new DataFrame"""
        self.data[sheet_name] = df.copy()
        # Don't write yet — wait for __exit__
    
    def append_row(self, sheet_name, row_data: list):
        """Append a row (immediate write)"""
        self.sheets[sheet_name].append_row(row_data)
        # Also update local cache
        new_row_df = pd.DataFrame([row_data], columns=self.data[sheet_name].columns)
        self.data[sheet_name] = pd.concat([self.data[sheet_name], new_row_df], ignore_index=True)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """On exit, sync all modified sheets back to Google"""
        print("Syncing changes to Google Sheets...")
        
        for sheet_name, df in self.data.items():
            original_sheet = self.sheets[sheet_name]
            
            # Get current data from Google (to compare)
            current_data = original_sheet.get_all_records()
            current_df = pd.DataFrame(current_data)
            
            # Check if DataFrame changed
            if not df.equals(current_df):
                print(f"  Updating {sheet_name}...")
                original_sheet.clear()
                original_sheet.update([df.columns.tolist()] + df.values.tolist())
        
        print("Sync complete!")
        return False  # Don't suppress exceptions