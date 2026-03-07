import frappe
from frappe.model.document import Document


class ESignatureLog(Document):
    def before_save(self):
        if not self.is_new():
            frappe.throw("E-Signature Log entries cannot be modified (append-only)")
