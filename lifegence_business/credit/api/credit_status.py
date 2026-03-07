# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def get_credit_status(customer, company=None):
	"""Get credit status for a customer including limit, balance, and risk grade."""
	if not frappe.db.exists("Customer", customer):
		return {"success": False, "error": _("取引先 {0} は存在しません。").format(customer)}

	filters = {"customer": customer}
	if company:
		filters["company"] = company

	cl = frappe.get_all(
		"Credit Limit",
		filters=filters,
		fields=[
			"name", "customer", "customer_name", "company",
			"credit_limit_amount", "used_amount", "available_amount",
			"usage_percentage", "status", "risk_grade",
			"valid_until", "next_review_date",
		],
		limit_page_length=1,
	)

	if not cl:
		return {"success": False, "error": _("取引先 {0} の与信枠が設定されていません。").format(customer)}

	credit = cl[0]

	# Get anti-social check info
	asc = frappe.get_all(
		"Anti-Social Check",
		filters={"customer": customer},
		fields=["result", "check_date", "valid_until"],
		order_by="check_date desc",
		limit_page_length=1,
	)

	anti_social = None
	if asc:
		anti_social = {
			"result": asc[0].result,
			"check_date": str(asc[0].check_date) if asc[0].check_date else None,
			"valid_until": str(asc[0].valid_until) if asc[0].valid_until else None,
		}

	# Count open alerts
	open_alerts = frappe.db.count("Credit Alert", {"customer": customer, "status": "Open"})

	return {
		"success": True,
		"credit_status": {
			"customer": credit.customer,
			"customer_name": credit.customer_name,
			"credit_limit_amount": credit.credit_limit_amount,
			"used_amount": credit.used_amount,
			"available_amount": credit.available_amount,
			"usage_percentage": credit.usage_percentage,
			"status": credit.status,
			"risk_grade": credit.risk_grade,
			"valid_until": str(credit.valid_until) if credit.valid_until else None,
			"next_review_date": str(credit.next_review_date) if credit.next_review_date else None,
			"anti_social_check": anti_social,
			"open_alerts": open_alerts,
		},
	}
