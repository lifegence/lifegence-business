import frappe
from frappe.model.document import Document


class ESignatureProviderSettings(Document):
    def validate(self):
        if self.api_endpoint and not self.api_endpoint.startswith("https://"):
            frappe.throw("API Endpoint must use HTTPS")
