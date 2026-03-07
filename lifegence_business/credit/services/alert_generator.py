# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate


def check_credit_expiry():
	"""Daily: Check for credit limits expiring within 30 days."""
	settings = frappe.get_single("Credit Settings")
	reminder_days = settings.send_review_reminder_days or 30
	threshold_date = add_days(nowdate(), reminder_days)

	expiring = frappe.get_all(
		"Credit Limit",
		filters={
			"status": "Active",
			"valid_until": ["between", [nowdate(), threshold_date]],
		},
		fields=["name", "customer", "customer_name", "company", "valid_until"],
	)

	for cl in expiring:
		_create_alert_if_not_exists(
			customer=cl.customer,
			company=cl.company,
			alert_type="期限切れ間近",
			severity="High",
			message=_("取引先 {0} の与信枠が {1} に期限切れとなります。").format(
				cl.customer_name or cl.customer, cl.valid_until
			),
			credit_limit=cl.name,
		)


def check_review_due():
	"""Daily: Check for credit limits with upcoming review dates."""
	settings = frappe.get_single("Credit Settings")
	reminder_days = settings.send_review_reminder_days or 30
	threshold_date = add_days(nowdate(), reminder_days)

	due_for_review = frappe.get_all(
		"Credit Limit",
		filters={
			"status": "Active",
			"next_review_date": ["between", [nowdate(), threshold_date]],
		},
		fields=["name", "customer", "customer_name", "company", "next_review_date"],
	)

	for cl in due_for_review:
		_create_alert_if_not_exists(
			customer=cl.customer,
			company=cl.company,
			alert_type="審査期限",
			severity="Medium",
			message=_("取引先 {0} の与信見直し期限が {1} に到来します。").format(
				cl.customer_name or cl.customer, cl.next_review_date
			),
			credit_limit=cl.name,
		)


def check_overdue_invoices():
	"""Daily: Check for overdue Sales Invoices."""
	today = nowdate()
	overdue = frappe.db.sql(
		"""
		SELECT si.customer, si.customer_name, si.company, si.name,
			   si.due_date, si.outstanding_amount,
			   DATEDIFF(%s, si.due_date) as overdue_days
		FROM `tabSales Invoice` si
		WHERE si.docstatus = 1
		AND si.outstanding_amount > 0
		AND si.due_date < %s
		ORDER BY overdue_days DESC
		""",
		(today, today),
		as_dict=True,
	)

	for inv in overdue:
		_create_alert_if_not_exists(
			customer=inv.customer,
			company=inv.company,
			alert_type="支払遅延",
			severity="High" if inv.overdue_days > 30 else "Medium",
			message=_("取引先 {0} の請求書 {1} が {2} 日間支払遅延しています。残高: {3}").format(
				inv.customer_name or inv.customer, inv.name,
				inv.overdue_days, inv.outstanding_amount
			),
			overdue_days=inv.overdue_days,
		)


def check_anti_social_expiry():
	"""Daily: Check for anti-social checks expiring within 30 days."""
	settings = frappe.get_single("Credit Settings")
	reminder_days = settings.send_review_reminder_days or 30
	threshold_date = add_days(nowdate(), reminder_days)

	expiring = frappe.get_all(
		"Anti-Social Check",
		filters={
			"valid_until": ["between", [nowdate(), threshold_date]],
			"result": ["!=", "該当あり"],
		},
		fields=["name", "customer", "customer_name", "company", "valid_until"],
	)

	for asc in expiring:
		_create_alert_if_not_exists(
			customer=asc.customer,
			company=asc.company,
			alert_type="反社チェック期限",
			severity="Medium",
			message=_("取引先 {0} の反社チェック結果が {1} に期限切れとなります。更新が必要です。").format(
				asc.customer_name or asc.customer, asc.valid_until
			),
			anti_social_check=asc.name,
		)


def _create_alert_if_not_exists(customer, company=None, alert_type=None, severity="Medium",
								message="", credit_limit=None, anti_social_check=None,
								overdue_days=None):
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

	doc = frappe.get_doc({
		"doctype": "Credit Alert",
		"customer": customer,
		"company": company,
		"alert_type": alert_type,
		"severity": severity,
		"alert_message": message,
		"credit_limit": credit_limit,
		"anti_social_check": anti_social_check,
		"overdue_days": overdue_days,
	})
	doc.insert(ignore_permissions=True)
