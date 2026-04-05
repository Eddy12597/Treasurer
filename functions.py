
from contextman import NHSGoogleSheets

def get_stats():
    # requires balance, pending_proposals, pending_reimbursements, approved_proposals, approved_reimbursements
    with NHSGoogleSheets("NHS Budget Proposals") as sheets:
        proposals_df = sheets.get_df("Proposals")
        
        approved_proposals = proposals_df.loc[proposals_df["APPSTATUS"] == 1, "APPSTATUS"].sum()
        pending_proposals = len(proposals_df["APPSTATUS"]) - approved_proposals
    
        reimbursements_df = sheets.get_df("Reimbursements")
        
        approved_reimbursements = reimbursements_df.loc[reimbursements_df["APPSTATUS"] == 1, "APPSTATUS"].sum()
        pending_reimbursements = len(reimbursements_df["APPSTATUS"]) - approved_reimbursements
        
        transactions_df = sheets.get_df("Transactions")
        balance = float(transactions_df.iloc[-1]["Balance"])
        
        
    return {
        "balance": balance,
        "pending_proposals": pending_proposals,
        "pending_reimbursements": pending_reimbursements,
        "approved_proposals": approved_proposals,
        "approved_reimbursements": approved_reimbursements        
    }