# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, nowdate


@frappe.whitelist()
def get_check_status(customer):
	"""Get anti-social check status for a customer."""
	if not frappe.db.exists("Customer", customer):
		return {"success": False, "error": _("取引先 {0} は存在しません。").format(customer)}

	customer_name = frappe.db.get_value("Customer", customer, "customer_name")

	checks = frappe.get_all(
		"Anti-Social Check",
		filters={"customer": customer},
		fields=[
			"name", "check_date", "check_source", "result",
			"valid_until", "requires_renewal", "checked_by",
		],
		order_by="check_date desc",
	)

	if not checks:
		return {
			"success": True,
			"customer": customer,
			"customer_name": customer_name,
			"latest_check": None,
			"check_history": [],
		}

	latest = checks[0]

	return {
		"success": True,
		"customer": customer,
		"customer_name": customer_name,
		"latest_check": {
			"name": latest.name,
			"check_date": str(latest.check_date) if latest.check_date else None,
			"check_source": latest.check_source,
			"result": latest.result,
			"valid_until": str(latest.valid_until) if latest.valid_until else None,
			"requires_renewal": bool(latest.requires_renewal),
			"checked_by": latest.checked_by,
		},
		"check_history": [
			{
				"name": c.name,
				"check_date": str(c.check_date) if c.check_date else None,
				"check_source": c.check_source,
				"result": c.result,
			}
			for c in checks
		],
	}


@frappe.whitelist()
def run_anti_social_check(customer, check_source, result, result_detail=None):
	"""Create a new anti-social check record."""
	if not frappe.db.exists("Customer", customer):
		return {"success": False, "error": _("取引先 {0} は存在しません。").format(customer)}

	doc = frappe.get_doc({
		"doctype": "Anti-Social Check",
		"customer": customer,
		"check_source": check_source,
		"result": result,
		"result_detail": result_detail or "",
		"checked_by": frappe.session.user,
		"check_date": nowdate(),
		"valid_until": add_days(nowdate(), 365),
	})
	doc.insert(ignore_permissions=True)

	return {
		"success": True,
		"check": doc.name,
		"customer": customer,
		"result": doc.result,
		"valid_until": str(doc.valid_until) if doc.valid_until else None,
	}
