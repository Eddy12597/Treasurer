
from datetime import datetime
from enum import Enum
import re

EMAIL_RE = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"

def raise_error(info: str | None):
    raise RuntimeError(info)

class EventType(Enum):
    FUNDRAISER_CHARITY="FUNDRAISER_CHARITY"
    SPORTS="SPORTS"
    THEME_BASED="THEME_BASED"
    OTHER="OTHER"


class BudgetProposal:
    def __init__(self,
                 # event info 
                 event_name: str, event_chairs: list[str], contact_email: str, event_start_date: str, event_type: EventType,
                 # budgets
                 itemized_budget: dict[str, int | float], expected_revenue: int | float,
                 # justification
                 justification: str, purpose: str, nhs_fund_reason: str,
                 # execution details
                 estimated_attendance: int, vendors_suppliers: list[str], reimbursement_contact: str):
        self.event_name = event_name
        self.event_chairs = event_chairs
        self.contact_email = contact_email if re.match(EMAIL_RE, contact_email) else raise_error("Contact Email is invalid")
        self.event_start_date = event_start_date
        self.event_type = event_type
        
        self.itemized_budget = itemized_budget
        self.expected_revenue = expected_revenue
        
        self.justification = justification
        self.purpose = purpose
        self.nhs_fund_reason = nhs_fund_reason
        
        self.estimated_attendance = estimated_attendance
        self.vendors_suppliers = vendors_suppliers
        self.reimbursement_contact = reimbursement_contact
        
    @classmethod
    def from_dict(cls, data: dict) -> 'BudgetProposal | None':
        
        event_name = data.get("event_name", "")
        event_chairs = data.get("event_chairs", [])
        contact_email = data.get("contact_email", "")
        event_start_date = data.get("event_start_date", "")
        event_type = data.get("event_type", EventType.OTHER)
        
        itemized_budget = data.get("itemized_budget", {})
        expected_revenue = data.get("expected_revenue", 0)
    
        justification = data.get("justification", "")
        purpose = data.get("purpose", "")
        nhs_fund_reason = data.get("nhs_fund_reason", "")
        
        estimated_attendance = data.get("estimated_attendance", 0)
        vendors_suppliers = data.get("vendors_suppliers", [])
        reimbursement_contact = data.get("reimbursement_contact", "")
        
        return cls(
            event_name, event_chairs, contact_email, event_start_date, event_type,
            itemized_budget, expected_revenue,
            justification, purpose, nhs_fund_reason,
            estimated_attendance, vendors_suppliers, reimbursement_contact)
