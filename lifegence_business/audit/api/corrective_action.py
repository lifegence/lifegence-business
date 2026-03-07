# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today


@frappe.whitelist()
def create_corrective_action(audit_finding, action_title, action_description, responsible_person, due_date, priority="Normal"):
	"""Create a new corrective action."""
	try:
		doc = frappe.get_doc({
			"doctype": "Corrective Action",
			"audit_finding": audit_finding,
			"action_title": action_title,
			"action_description": action_description,
			"responsible_person": responsible_person,
			"due_date": due_date,
			"priority": priority,
		})
		doc.insert(ignore_permissions=True)

		# Link corrective action to the finding
		finding = frappe.get_doc("Audit Finding", audit_finding)
		if not finding.corrective_action:
			finding.corrective_action = doc.name
			finding.save(ignore_permissions=True)

		return {
			"success": True,
			"data": {"corrective_action": doc.name, "status": doc.status},
		}
	except Exception as e:
		frappe.log_error(f"create_corrective_action error: {e}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_corrective_action(action_name, status, completion_date=None, evidence_description=None):
	"""Update corrective action status."""
	try:
		doc = frappe.get_doc("Corrective Action", action_name)
		doc.status = status
		if completion_date:
			doc.completion_date = completion_date
		if evidence_description:
			doc.evidence_description = evidence_description
		doc.save(ignore_permissions=True)

		return {
			"success": True,
			"data": {"corrective_action": doc.name, "new_status": doc.status},
		}
	except Exception as e:
		frappe.log_error(f"update_corrective_action error: {e}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_overdue_actions(department=None, priority=None):
	"""Get overdue corrective actions."""
	try:
		from lifegence_audit.services.corrective_action_service import get_overdue_actions_data

		actions = get_overdue_actions_data(department, priority)
		return {
			"success": True,
			"data": {"overdue_actions": actions, "total": len(actions)},
		}
	except Exception as e:
		frappe.log_error(f"get_overdue_actions error: {e}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def verify_completion(action_name, verified_by, verification_comments=None):
	"""Verify completion of a corrective action."""
	try:
		doc = frappe.get_doc("Corrective Action", action_name)
		doc.completion_verified_by = verified_by
		doc.verification_date = today()
		if verification_comments:
			doc.verification_comments = verification_comments
		doc.save(ignore_permissions=True)

		return {
			"success": True,
			"data": {
				"corrective_action": doc.name,
				"verified_by": doc.completion_verified_by,
				"verification_date": str(doc.verification_date),
			},
		}
	except Exception as e:
		frappe.log_error(f"verify_completion error: {e}")
		return {"success": False, "error": str(e)}
