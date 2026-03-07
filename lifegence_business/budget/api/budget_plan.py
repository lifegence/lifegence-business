# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.utils import today


@frappe.whitelist()
def submit_budget_plan(budget_plan, action, comment=None):
	"""Transition Budget Plan status."""
	try:
		doc = frappe.get_doc("Budget Plan", budget_plan)
		valid_transitions = {
			"submit": {"from": ["Draft"], "to": "Submitted"},
			"approve": {"from": ["Submitted"], "to": "Approved"},
			"reject": {"from": ["Submitted"], "to": "Rejected"},
		}

		if action not in valid_transitions:
			return {"success": False, "error": f"Invalid action: {action}"}

		transition = valid_transitions[action]
		if doc.status not in transition["from"]:
			return {"success": False, "error": f"Cannot {action} from status {doc.status}"}

		if action == "reject" and not comment:
			return {"success": False, "error": "差戻理由を入力してください"}

		previous_status = doc.status
		doc.status = transition["to"]

		if action == "approve":
			doc.approved_by = frappe.session.user
			doc.approved_date = today()
		elif action == "reject":
			doc.rejection_reason = comment

		doc.save(ignore_permissions=True)

		if action == "submit":
			doc.submit()

		return {
			"success": True,
			"data": {
				"budget_plan": doc.name,
				"previous_status": previous_status,
				"new_status": doc.status,
				"action_by": frappe.session.user,
				"action_date": today(),
			},
		}
	except Exception as e:
		frappe.log_error(f"submit_budget_plan error: {e}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def create_revision(budget_plan, reason, revision_type, revised_items=None):
	"""Create a Budget Revision for the given Budget Plan."""
	try:
		if isinstance(revised_items, str):
			revised_items = json.loads(revised_items)

		bp = frappe.get_doc("Budget Plan", budget_plan)

		# Check max revision count
		settings = frappe.get_single("Budget Settings")
		max_revisions = settings.max_revision_count or 3
		if (bp.amendments or 0) >= max_revisions:
			return {"success": False, "error": f"最大修正回数（{max_revisions}回）に達しています"}

		# Calculate revision number
		existing_count = frappe.db.count("Budget Revision", {"budget_plan": budget_plan})

		rev_doc = frappe.get_doc({
			"doctype": "Budget Revision",
			"budget_plan": budget_plan,
			"revision_number": existing_count + 1,
			"revision_date": today(),
			"revision_type": revision_type,
			"reason": reason,
			"requested_by": frappe.session.user,
			"revised_items": revised_items or [],
		})
		rev_doc.insert(ignore_permissions=True)

		return {
			"success": True,
			"data": {
				"revision": rev_doc.name,
				"budget_plan": budget_plan,
				"revision_number": rev_doc.revision_number,
				"status": rev_doc.status,
				"total_change_amount": rev_doc.total_change_amount,
			},
		}
	except Exception as e:
		frappe.log_error(f"create_revision error: {e}")
		return {"success": False, "error": str(e)}
