
from contextman import NHSGoogleSheets
import json

def get_stats_and_upcoming_events():
    # requires balance, pending_proposals, pending_reimbursements, approved_proposals, approved_reimbursements
    with NHSGoogleSheets("NHS Budget Proposals") as sheets:
        
        proposals_df = sheets.get_df("Proposals")
        approved_proposals = int(proposals_df.loc[proposals_df["APPSTATUS"] == 1, "APPSTATUS"].sum().item())
        pending_proposals = len(proposals_df["APPSTATUS"]) - approved_proposals
    
        reimbursements_df = sheets.get_df("Reimbursements")
        
        approved_reimbursements = int(reimbursements_df.loc[reimbursements_df["APPSTATUS"] == 1, "APPSTATUS"].sum().item())
        pending_reimbursements = len(reimbursements_df["APPSTATUS"]) - approved_reimbursements
        
        transactions_df = sheets.get_df("Transactions")
        balance = float(transactions_df.iloc[-1]["Balance"].item())
        
        upcoming_events = []
        features = ["event_name", "event_chair"]
        for i, row in proposals_df.iterrows():
            obj = { feature: row[feature] for feature in features}
            
            itemized_budget = json.loads(row["itemized_budget"])
            
            obj["approx_total_budget"] = sum(itemized_budget.values())
            
            upcoming_events.append(obj)
            
        
    return {
        "stats": {
            "balance": balance,
            "pending_proposals": pending_proposals,
            "pending_reimbursements": pending_reimbursements,
            "approved_proposals": approved_proposals,
            "approved_reimbursements": approved_reimbursements,
        },
        "upcoming_events": upcoming_events 
    }