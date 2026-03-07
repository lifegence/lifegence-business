# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def recalculate_customer_balance_from_doc(doc, method=None):
	"""Recalculate customer balance triggered by doc_events on SO/SI/PE.

	Called from hooks.py doc_events for Sales Order, Sales Invoice, Payment Entry.
	"""
	customer = _get_customer_from_doc(doc)
	if not customer:
		return

	company = doc.company if hasattr(doc, "company") else None
	if not company:
		return

	recalculate_customer_balance(customer, company)


def recalculate_customer_balance(customer, company):
	"""Recalculate credit balance for a customer/company and update Credit Limit."""
	cl_name = frappe.db.get_value(
		"Credit Limit",
		{"customer": customer, "company": company},
		"name",
	)
	if not cl_name:
		return

	cl = frappe.get_doc("Credit Limit", cl_name)
	cl.recalculate_balance()
	cl.save(ignore_permissions=True)

	# Check if alert threshold exceeded
	_check_alert_threshold(cl)


def _get_customer_from_doc(doc):
	"""Extract customer from various document types."""
	if hasattr(doc, "customer") and doc.customer:
		return doc.customer

	# Payment Entry may have party instead of customer
	if hasattr(doc, "party_type") and doc.party_type == "Customer":
		return doc.party

	return None


def _check_alert_threshold(cl):
	"""Generate alert if usage exceeds threshold."""
	settings = frappe.get_single("Credit Settings")
	threshold_pct = settings.alert_threshold_pct or 80

	if cl.usage_percentage >= 100:
		# Credit limit exceeded
		_create_alert_if_not_exists(
			customer=cl.customer,
			company=cl.company,
			alert_type="限度額超過",
			severity="Critical",
			message=_("取引先 {0} の与信使用額が限度額を超過しています。使用額: {1}、限度額: {2}").format(
				cl.customer_name or cl.customer, cl.used_amount, cl.credit_limit_amount
			),
			threshold_value=cl.credit_limit_amount,
			current_value=cl.used_amount,
			credit_limit=cl.name,
		)
	elif cl.usage_percentage >= threshold_pct:
		_create_alert_if_not_exists(
			customer=cl.customer,
			company=cl.company,
			alert_type="限度額超過",
			severity="High",
			message=_("取引先 {0} の与信使用率が {1}% に達しています。").format(
				cl.customer_name or cl.customer, round(cl.usage_percentage, 1)
			),
			threshold_value=cl.credit_limit_amount,
			current_value=cl.used_amount,
			credit_limit=cl.name,
		)


def _create_alert_if_not_exists(customer, company, alert_type, severity, message,
								threshold_value=None, current_value=None, credit_limit=None):
	"""Create alert only if no open alert of same type exists for this customer."""
	existing = frappe.db.exists(
		"Credit Alert",
		{
			"customer": customer,
			"alert_type": alert_type,
			"status": "Open",
		},
	)
	if existing:
		return

	frappe.get_doc({
		"doctype": "Credit Alert",
		"customer": customer,
		"company": company,
		"alert_type": alert_type,
		"severity": severity,
		"alert_message": message,
		"threshold_value": threshold_value,
		"current_value": current_value,
		"credit_limit": credit_limit,
	}).insert(ignore_permissions=True)
