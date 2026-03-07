import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class Contract(Document):
    def validate(self):
        if self.end_date and self.start_date:
            if getdate(self.end_date) < getdate(self.start_date):
                frappe.throw("End date cannot be before start date")

    def on_submit(self):
        self.db_set("status", "Active")

    def on_cancel(self):
        self.db_set("status", "Terminated")
