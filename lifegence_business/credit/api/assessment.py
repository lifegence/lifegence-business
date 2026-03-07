# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def create_assessment(customer, requested_amount, assessment_type="新規取引",
					  revenue=None, profit=None, capital=None, years_in_business=None):
	"""Create a new credit assessment."""
	if not frappe.db.exists("Customer", customer):
		return {"success": False, "error": _("取引先 {0} は存在しません。").format(customer)}

	doc_data = {
		"doctype": "Credit Assessment",
		"customer": customer,
		"assessment_type": assessment_type,
		"requested_amount": float(requested_amount),
	}

	if revenue is not None:
		doc_data["revenue"] = float(revenue)
	if profit is not None:
		doc_data["profit"] = float(profit)
	if capital is not None:
		doc_data["capital"] = float(capital)
	if years_in_business is not None:
		doc_data["years_in_business"] = int(years_in_business)

	doc = frappe.get_doc(doc_data)
	doc.insert(ignore_permissions=True)

	return {
		"success": True,
		"assessment": doc.name,
		"status": doc.status,
		"customer": doc.customer,
		"assessment_type": doc.assessment_type,
		"requested_amount": doc.requested_amount,
		"risk_score": doc.risk_score,
		"risk_grade": doc.risk_grade,
		"recommended_limit": doc.recommended_limit,
	}
