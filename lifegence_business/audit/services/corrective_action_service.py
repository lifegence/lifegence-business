# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today


def on_corrective_action_update(doc, method=None):
	"""Update related Audit Finding status when Corrective Action status changes."""
	if not doc.audit_finding:
		return

	finding = frappe.get_doc("Audit Finding", doc.audit_finding)

	if doc.status == "Completed" and finding.status in ("Open", "In Progress"):
		finding.status = "Remediated"
		finding.save(ignore_permissions=True)
	elif doc.status == "In Progress" and finding.status == "Open":
		finding.status = "In Progress"
		finding.save(ignore_permissions=True)


def check_overdue_actions():
	"""Daily scheduler: mark overdue corrective actions."""
	overdue_actions = frappe.get_all(
		"Corrective Action",
		filters={
			"status": ["in", ["Open", "In Progress"]],
			"due_date": ["<", today()],
		},
		pluck="name",
	)

	for name in overdue_actions:
		frappe.db.set_value("Corrective Action", name, "status", "Overdue")

	if overdue_actions:
		frappe.db.commit()


def get_overdue_actions_data(department=None, priority=None):
	"""Get list of overdue corrective actions."""
	filters = {"status": "Overdue"}
	if department:
		filters["responsible_department"] = department
	if priority:
		filters["priority"] = priority

	actions = frappe.get_all(
		"Corrective Action",
		filters=filters,
		fields=[
			"name", "action_title", "due_date", "responsible_person",
			"priority", "audit_finding",
		],
		order_by="due_date asc",
	)

	for action in actions:
		from frappe.utils import date_diff
		action["days_overdue"] = date_diff(today(), action.due_date)

	return actions
