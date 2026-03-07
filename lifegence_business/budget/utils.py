# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def check_budget_availability(doc, method):
	"""Check budget availability before PO/JE submit."""
	settings = frappe.get_single("Budget Settings")

	if doc.doctype == "Purchase Order" and not settings.check_budget_on_purchase_order:
		return
	if doc.doctype == "Journal Entry" and not settings.check_budget_on_journal_entry:
		return

	items_to_check = _get_budget_items(doc)

	for item in items_to_check:
		budget_data = _get_budget_for_account(
			item["cost_center"], item["account"], item["fiscal_year"], doc.company
		)
		if not budget_data:
			continue

		actual = _get_actual_for_account(
			item["cost_center"], item["account"], item["fiscal_year"], doc.company
		)
		remaining = flt(budget_data.get("annual_total", 0)) - flt(actual) - flt(item["amount"])

		if remaining < 0:
			variance_action = settings.variance_action or "Warn"
			if variance_action == "Stop":
				frappe.throw(
					f"予算超過: {item['account']} の予算残高が不足しています。"
					f"（予算: {budget_data.get('annual_total', 0):,.0f}、"
					f"実績+今回: {flt(actual) + flt(item['amount']):,.0f}）",
					frappe.ValidationError,
				)
			elif variance_action == "Warn":
				frappe.msgprint(
					f"予算超過警告: {item['account']} の予算を超過します。",
					alert=True,
					indicator="orange",
				)


def _get_budget_items(doc):
	"""Extract cost_center, account, amount tuples from doc."""
	items = []
	if doc.doctype == "Purchase Order":
		for item in doc.items:
			if item.cost_center and item.expense_account:
				items.append({
					"cost_center": item.cost_center,
					"account": item.expense_account,
					"amount": item.amount,
					"fiscal_year": _get_fiscal_year(doc.transaction_date, doc.company),
				})
	elif doc.doctype == "Journal Entry":
		for entry in doc.accounts:
			if entry.cost_center and entry.debit_in_account_currency > 0:
				items.append({
					"cost_center": entry.cost_center,
					"account": entry.account,
					"amount": entry.debit_in_account_currency,
					"fiscal_year": _get_fiscal_year(doc.posting_date, doc.company),
				})
	return items


def _get_fiscal_year(date, company):
	"""Get fiscal year for given date."""
	from erpnext.accounts.utils import get_fiscal_year

	try:
		return get_fiscal_year(date, company=company)[0]
	except Exception:
		return None


def _get_budget_for_account(cost_center, account, fiscal_year, company):
	"""Get approved budget for a specific account."""
	if not fiscal_year:
		return None
	result = frappe.db.sql("""
		SELECT bpi.annual_total
		FROM `tabBudget Plan Item` bpi
		INNER JOIN `tabBudget Plan` bp ON bp.name = bpi.parent
		WHERE bp.cost_center = %s
		  AND bpi.account = %s
		  AND bp.fiscal_year = %s
		  AND bp.company = %s
		  AND bp.status IN ('Approved', 'Revised')
		  AND bp.docstatus = 1
		LIMIT 1
	""", (cost_center, account, fiscal_year, company), as_dict=True)
	return result[0] if result else None


def _get_actual_for_account(cost_center, account, fiscal_year, company):
	"""Get actual amount from GL Entry."""
	if not fiscal_year:
		return 0
	result = frappe.db.sql("""
		SELECT SUM(debit - credit) as net_amount
		FROM `tabGL Entry`
		WHERE cost_center = %s
		  AND account = %s
		  AND fiscal_year = %s
		  AND company = %s
		  AND is_cancelled = 0
	""", (cost_center, account, fiscal_year, company))
	return flt(result[0][0]) if result and result[0][0] else 0


def check_budget_alerts():
	"""Daily scheduler: check for budget threshold breaches."""
	settings = frappe.get_single("Budget Settings")
	threshold = flt(settings.variance_threshold_pct) or 10

	plans = frappe.get_all(
		"Budget Plan",
		filters={"status": ["in", ["Approved", "Revised"]], "docstatus": 1},
		fields=["name", "cost_center", "fiscal_year", "company", "total_annual_amount", "department"],
	)

	for plan in plans:
		if not plan.total_annual_amount:
			continue
		items = frappe.get_all(
			"Budget Plan Item",
			filters={"parent": plan.name},
			fields=["account", "annual_total"],
		)
		for item in items:
			actual = _get_actual_for_account(
				plan.cost_center, item.account, plan.fiscal_year, plan.company
			)
			if not item.annual_total:
				continue
			consumption_pct = (flt(actual) / flt(item.annual_total)) * 100
			if consumption_pct >= (100 - threshold):
				frappe.logger().warning(
					f"Budget alert: {plan.department}/{item.account} "
					f"consumption at {consumption_pct:.1f}%"
				)
