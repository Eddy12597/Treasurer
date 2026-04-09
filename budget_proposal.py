
from datetime import datetime
from enum import Enum
import re
import json

EMAIL_RE = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def raise_error(info: str | None):
    raise RuntimeError(info)

class EventType(Enum):
    FUNDRAISER_CHARITY="FUNDRAISER_CHARITY"
    SPORTS="SPORTS"
    THEME_BASED="THEME_BASED"
    OTHER="OTHER"

class BudgetProposal:
    last_prop_id=0
    def __init__(self,
                 # event info 
                 event_name: str, event_chair: str, contact_email: str, event_start_date: str, event_type: EventType,
                 # budgets
                 itemized_budget: dict[str, int | float], expected_revenue: int | float,
                 # justification
                 justification: str, purpose: str, nhs_fund_reason: str,
                 # execution details
                 estimated_attendance: int, vendors_suppliers: str, reimbursement_contact: str):
        self.event_name = event_name
        self.event_chair = event_chair
        self.contact_email = str(contact_email).strip() if re.match(EMAIL_RE, contact_email) else raise_error("Contact Email is invalid")
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
        with open("data.json", encoding='utf-8') as f:
            d = json.load(f)
            BudgetProposal.last_prop_id = int(d.get("LastPropID", 0)) + 1
        d["LastPropID"] = BudgetProposal.last_prop_id
        with open("data.json", "r", encoding='utf-8') as f:
            json.dump(d, f)
                
        
        
    @classmethod
    def from_dict(cls, data: dict) -> 'BudgetProposal | None':
        
        event_name = data.get("event_name", "")
        
        event_chair = data.get("event_chair", "")
        
        contact_email = data.get("contact_email", "")
        event_start_date = data.get("event_start_date", "")
        
        # Fix: Convert string to Enum
        event_type_str = data.get("event_type", "OTHER")
        try:
            event_type = EventType(event_type_str)
        except ValueError:
            event_type = EventType.OTHER
        
        itemized_budget = data.get("itemized_budget", {})
        expected_revenue = data.get("expected_revenue", 0)

        justification = data.get("justification", "")
        purpose = data.get("purpose", "")
        nhs_fund_reason = data.get("nhs_fund_reason", "")
        
        estimated_attendance = data.get("estimated_attendance", 0)
        
        # Fix: Handle string instead of list
        vendors_suppliers = data.get("vendors_suppliers", "")
        if isinstance(vendors_suppliers, str) and vendors_suppliers:
            vendors_suppliers = vendors_suppliers
        elif not vendors_suppliers:
            vendors_suppliers = ""
        
        reimbursement_contact = data.get("reimbursement_contact", "")
        
        return cls(
            event_name, event_chair, contact_email, event_start_date, event_type,
            itemized_budget, expected_revenue,
            justification, purpose, nhs_fund_reason,
            estimated_attendance, vendors_suppliers, reimbursement_contact)

    def _safe_str(self, value) -> str:
            if value is None:
                return ""
            if isinstance(value, float):
                # Handle NaN, Infinity
                if str(value) in ('nan', 'inf', '-inf'):
                    return ""
                # Format floats to avoid excessive decimals
                return f"{value:.2f}" if value == int(value) else str(value)
            if isinstance(value, Enum):
                return value.value
            if isinstance(value, (list, dict)):
                # Use JSON-like string representation for complex types
                return json.dumps(value, ensure_ascii=False)
            return str(value)
        
    def _escape_csv_field(self, field: str) -> str:
        if not field:
            return field
        
        needs_escape = any(char in field for char in [',', '"', '\n', '\r'])
        
        if needs_escape:
            field = field.replace('"', '""')
            return f'"{field}"'
        
        return field

    def to_row(self) -> list:
        fields = [
            self._safe_str(self.event_name),
            self._safe_str(self.event_chair),
            self._safe_str(self.contact_email),
            self._safe_str(self.event_start_date),
            self._safe_str(self.event_type),
            self._safe_str(self.itemized_budget),
            self._safe_str(self.expected_revenue),
            self._safe_str(self.justification),
            self._safe_str(self.purpose),
            self._safe_str(self.nhs_fund_reason),
            self._safe_str(self.estimated_attendance),
            self._safe_str(self.vendors_suppliers),
            self._safe_str(self.reimbursement_contact),
            str(BudgetProposal.last_prop_id),
            "",
            "0", # unapproved by default,
            "0"
        ]
        
        return [self._escape_csv_field(field) for field in fields]