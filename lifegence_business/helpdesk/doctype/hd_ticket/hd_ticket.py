# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, add_to_date, time_diff_in_hours


# Valid status transitions
VALID_TRANSITIONS = {
	"Open": ["In Progress", "Closed"],
	"In Progress": ["Waiting for Customer", "Resolved", "Closed"],
	"Waiting for Customer": ["In Progress", "Resolved", "Closed"],
	"Resolved": ["Closed", "In Progress"],
	"Closed": [],
}


class HDTicket(Document):
	def before_insert(self):
		self._apply_category_defaults()
		self._apply_sla_policy()

	def validate(self):
		self._validate_status_transition()
		self._handle_status_change()

	def _apply_category_defaults(self):
		"""Auto-assign from category defaults."""
		if not self.category:
			return
		category = frappe.get_cached_doc("HD Category", self.category)
		if not self.assigned_to and category.default_assigned_to:
			self.assigned_to = category.default_assigned_to
		if self.priority == "Medium" and category.default_priority:
			self.priority = category.default_priority

	def _apply_sla_policy(self):
		"""Apply default SLA policy and calculate due dates."""
		if self.sla_policy:
			return

		# Find default SLA policy
		default_policy = frappe.db.get_value(
			"HD SLA Policy",
			{"is_default": 1, "enabled": 1},
			"name",
		)
		if not default_policy:
			return

		self.sla_policy = default_policy
		self._calculate_sla_due_dates()

		# Add initial SLA timer event
		self.append("sla_timers", {
			"event": "Started",
			"timestamp": now_datetime(),
			"status_at_event": self.status or "Open",
		})

	def _calculate_sla_due_dates(self):
		"""Calculate response and resolution due dates based on SLA policy."""
		if not self.sla_policy:
			return

		policy = frappe.get_cached_doc("HD SLA Policy", self.sla_policy)
		priority = (self.priority or "Medium").lower()

		response_hours = policy.get(f"{priority}_response_time") or 8
		resolution_hours = policy.get(f"{priority}_resolution_time") or 24

		now = now_datetime()
		self.response_due = add_to_date(now, hours=response_hours)
		self.resolution_due = add_to_date(now, hours=resolution_hours)

	def _validate_status_transition(self):
		"""Validate status transitions."""
		if self.is_new():
			return

		old_status = self.get_doc_before_save()
		if not old_status:
			return

		old_status = old_status.status
		new_status = self.status

		if old_status == new_status:
			return

		allowed = VALID_TRANSITIONS.get(old_status, [])
		if new_status not in allowed:
			frappe.throw(
				_("ステータスを {0} から {1} に変更できません。").format(old_status, new_status)
			)

	def _handle_status_change(self):
		"""Handle SLA timer events on status change."""
		if self.is_new():
			return

		old_doc = self.get_doc_before_save()
		if not old_doc:
			return

		old_status = old_doc.status
		new_status = self.status

		if old_status == new_status:
			return

		now = now_datetime()

		# Track first response
		if old_status == "Open" and new_status == "In Progress":
			if not self.first_responded_on:
				self.first_responded_on = now
			self.append("sla_timers", {
				"event": "Resumed",
				"timestamp": now,
				"status_at_event": new_status,
			})

		# Pause SLA when waiting for customer
		elif new_status == "Waiting for Customer":
			self.append("sla_timers", {
				"event": "Paused",
				"timestamp": now,
				"status_at_event": new_status,
			})

		# Resume SLA when back from waiting
		elif old_status == "Waiting for Customer" and new_status == "In Progress":
			self.append("sla_timers", {
				"event": "Resumed",
				"timestamp": now,
				"status_at_event": new_status,
			})

		# Mark resolved
		elif new_status == "Resolved":
			self.resolved_on = now
			self.append("sla_timers", {
				"event": "Completed",
				"timestamp": now,
				"status_at_event": new_status,
			})

		# Reopen from resolved
		elif old_status == "Resolved" and new_status == "In Progress":
			self.resolved_on = None
			self.append("sla_timers", {
				"event": "Resumed",
				"timestamp": now,
				"status_at_event": new_status,
			})

		# Update SLA status
		self._update_sla_status()

	def _update_sla_status(self):
		"""Check SLA breaches and warnings."""
		if not self.sla_policy or self.status in ("Resolved", "Closed"):
			return

		now = now_datetime()

		# Check resolution due breach
		if self.resolution_due and now > self.get_datetime("resolution_due"):
			self.sla_status = "Breached"
			return

		# Check response due breach (if not yet responded)
		if (
			not self.first_responded_on
			and self.response_due
			and now > self.get_datetime("response_due")
		):
			self.sla_status = "Breached"
			return

		# Check warning threshold (80% of resolution time elapsed)
		if self.resolution_due:
			total_hours = time_diff_in_hours(self.resolution_due, self.creation)
			elapsed_hours = time_diff_in_hours(now, self.creation)
			if total_hours > 0 and (elapsed_hours / total_hours) >= 0.8:
				self.sla_status = "Warning"
				return

		self.sla_status = "On Track"

	def get_datetime(self, fieldname):
		"""Get field value as datetime object."""
		val = self.get(fieldname)
		if isinstance(val, str):
			return frappe.utils.get_datetime(val)
		return val
