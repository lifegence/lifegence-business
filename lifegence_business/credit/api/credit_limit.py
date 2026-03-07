# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def update_credit_limit(customer, new_amount, change_reason, company=None, change_detail=None):
	"""Update credit limit amount with history recording."""
	if not frappe.db.exists("Customer", customer):
		return {"success": False, "error": _("取引先 {0} は存在しません。").format(customer)}

	if not company:
		company = frappe.defaults.get_defaults().get("company")

	cl_name = frappe.db.get_value(
		"Credit Limit",
		{"customer": customer, "company": company},
		"name",
	)

	if not cl_name:
		return {"success": False, "error": _("取引先 {0} の与信枠が設定されていません。").format(customer)}

	cl = frappe.get_doc("Credit Limit", cl_name)
	previous_amount = cl.credit_limit_amount

	# Update credit limit
	cl.credit_limit_amount = float(new_amount)
	cl.save(ignore_permissions=True)

	# Record history
	history = frappe.get_doc({
		"doctype": "Credit Limit History",
		"credit_limit": cl.name,
		"customer": customer,
		"company": company,
		"previous_amount": previous_amount,
		"new_amount": float(new_amount),
		"change_reason": change_reason,
		"change_detail": change_detail or "",
		"changed_by": frappe.session.user,
	})
	history.insert(ignore_permissions=True)

	return {
		"success": True,
		"credit_limit": cl.name,
		"previous_amount": previous_amount,
		"new_amount": float(new_amount),
		"change_reason": change_reason,
		"history": history.name,
	}
