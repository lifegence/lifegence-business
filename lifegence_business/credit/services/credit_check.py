# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, nowdate


def check_credit_on_sales_order(doc, method=None):
	"""Check credit limit before Sales Order submit.

	Called from hooks.py doc_events: Sales Order.before_submit
	"""
	if not doc.customer or not doc.company:
		return

	settings = frappe.get_single("Credit Settings")

	# Get Credit Limit for this customer/company
	cl_name = frappe.db.get_value(
		"Credit Limit",
		{"customer": doc.customer, "company": doc.company},
		"name",
	)

	if not cl_name:
		# No credit limit set - pass if auto_block is off
		if not settings.auto_block_on_exceed:
			doc.credit_check_passed = 1
			doc.credit_check_note = _("与信枠が未設定です。")
			return
		doc.credit_check_passed = 1
		doc.credit_check_note = _("与信枠が未設定のため、与信チェックをスキップしました。")
		return

	cl = frappe.get_doc("Credit Limit", cl_name)

	# Check status
	if cl.status == "Suspended":
		frappe.throw(
			_("取引先 {0} の与信枠が停止されています。理由: {1}").format(
				doc.customer, cl.suspension_reason or "不明"
			)
		)

	if cl.status == "Under Review":
		doc.credit_check_note = _("取引先の与信枠は審査中です。")

	# Check validity
	if cl.valid_until and getdate(cl.valid_until) < getdate(nowdate()):
		if settings.auto_block_on_exceed:
			frappe.throw(
				_("取引先 {0} の与信枠が期限切れです（有効期限: {1}）。").format(
					doc.customer, cl.valid_until
				)
			)

	# Check anti-social status
	_check_anti_social(doc)

	# Calculate balance including this SO
	cl.recalculate_balance()
	total_after = cl.used_amount + doc.grand_total

	if total_after > cl.credit_limit_amount:
		excess = total_after - cl.credit_limit_amount
		if settings.auto_block_on_exceed:
			frappe.throw(
				_("与信限度額を超過しています。限度額: {0}、現在使用額: {1}、今回受注額: {2}、超過額: {3}").format(
					cl.credit_limit_amount, cl.used_amount, doc.grand_total, excess
				)
			)
		else:
			# Auto block off - create alert but allow submit
			from lifegence_business.credit.services.balance_calculator import _create_alert_if_not_exists

			_create_alert_if_not_exists(
				customer=doc.customer,
				company=doc.company,
				alert_type="限度額超過",
				severity="Critical",
				message=_("受注 {0} により与信限度額を超過。超過額: {1}").format(doc.name, excess),
				threshold_value=cl.credit_limit_amount,
				current_value=total_after,
				credit_limit=cl.name,
			)
			doc.credit_check_note = _("与信限度額を超過していますが、自動ブロックが無効のため受注を許可しました。")

	doc.credit_check_passed = 1


def _check_anti_social(doc):
	"""Check anti-social check result for the customer."""
	result = frappe.db.get_value("Customer", doc.customer, "anti_social_check_result")
	if result == "該当あり":
		frappe.throw(
			_("取引先 {0} は反社チェックで「該当あり」と判定されています。取引を行えません。").format(doc.customer)
		)
