# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class AuditPlan(Document):
	def before_save(self):
		if self.is_new():
			self.audit_manager = self.audit_manager or frappe.session.user
		self._update_summary()

	def validate(self):
		self._validate_status_transition()
		self._validate_dates()

	def _validate_status_transition(self):
		if self.is_new():
			return
		old_status = self.get_db_value("status")
		if old_status == self.status:
			return

		valid_transitions = {
			"Draft": ["Submitted", "Cancelled"],
			"Submitted": ["Approved", "Draft"],
			"Approved": ["In Progress", "Cancelled"],
			"In Progress": ["Completed", "Cancelled"],
		}
		allowed = valid_transitions.get(old_status, [])
		if self.status not in allowed:
			frappe.throw(
				_("Cannot change status from {0} to {1}").format(old_status, self.status)
			)

		if self.status == "Approved":
			self.approved_by = frappe.session.user
			self.approval_date = today()

	def _validate_dates(self):
		if self.plan_period_start and self.plan_period_end:
			if self.plan_period_start > self.plan_period_end:
				frappe.throw(_("Plan Period Start cannot be after Plan Period End"))

	def _update_summary(self):
		if not self.name:
			return
		engagements = frappe.get_all(
			"Audit Engagement",
			filters={"audit_plan": self.name},
			fields=["status"],
		)
		self.planned_audits = len(engagements)
		self.completed_audits = sum(1 for e in engagements if e.status == "Closed")

		findings = frappe.get_all(
			"Audit Finding",
			filters={"audit_engagement": ["in", [e.name for e in frappe.get_all("Audit Engagement", filters={"audit_plan": self.name}, pluck="name")] or [""]]},
			fields=["severity"],
		) if self.planned_audits > 0 else []
		self.total_findings = len(findings)
		self.critical_findings = sum(1 for f in findings if f.severity in ("Critical", "High"))
