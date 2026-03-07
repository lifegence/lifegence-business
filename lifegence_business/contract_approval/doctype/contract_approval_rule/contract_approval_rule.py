import frappe
from frappe.model.document import Document


class ContractApprovalRule(Document):
    def validate(self):
        if self.min_amount and self.max_amount:
            if self.min_amount > self.max_amount:
                frappe.throw("Minimum amount cannot exceed maximum amount")
