# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class AuditEngagement(Document):
	def before_save(self):
		self._update_counts()

	def validate(self):
		self._validate_dates()
		self._validate_status_transition()

	def _validate_dates(self):
		if self.period_start and self.period_end and self.period_start > self.period_end:
			frappe.throw(_("Period Start cannot be after Period End"))

	def _validate_status_transition(self):
		if self.is_new():
			return
		old_status = self.get_db_value("status")
		if old_status == self.status:
			return

		valid_transitions = {
			"Planning": ["Fieldwork", "Closed"],
			"Fieldwork": ["Reporting", "Closed"],
			"Reporting": ["Review", "Closed"],
			"Review": ["Closed", "Reporting"],
		}
		allowed = valid_transitions.get(old_status, [])
		if self.status not in allowed:
			frappe.throw(
				_("Cannot change status from {0} to {1}").format(old_status, self.status)
			)

		if self.status == "Fieldwork" and not self.actual_start:
			self.actual_start = today()
		if self.status == "Closed" and not self.actual_end:
			self.actual_end = today()

	def _update_counts(self):
		if not self.name:
			return
		findings = frappe.get_all(
			"Audit Finding",
			filters={"audit_engagement": self.name},
			fields=["severity", "status"],
		)
		self.findings_count = len(findings)
		self.critical_findings_count = sum(1 for f in findings if f.severity in ("Critical", "High"))
		self.open_actions_count = frappe.db.count(
			"Corrective Action",
			filters={
				"audit_finding": ["in", [f.name for f in frappe.get_all("Audit Finding", filters={"audit_engagement": self.name}, pluck="name")] or [""]],
				"status": ["in", ["Open", "In Progress", "Overdue"]],
			},
		) if self.findings_count > 0 else 0
