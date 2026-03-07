# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, today


@frappe.whitelist()
def get_budget_vs_actual(
	company,
	fiscal_year,
	department=None,
	cost_center=None,
	budget_type=None,
	as_of_date=None,
	period="Cumulative",
):
	"""Get budget vs actual data."""
	try:
		filters = {
			"company": company,
			"fiscal_year": fiscal_year,
			"docstatus": 1,
			"status": ["in", ["Approved", "Revised"]],
		}
		if department:
			filters["department"] = department
		if cost_center:
			filters["cost_center"] = cost_center
		if budget_type:
			filters["budget_type"] = budget_type

		plans = frappe.get_all(
			"Budget Plan",
			filters=filters,
			fields=["name", "department", "cost_center", "total_annual_amount"],
		)

		total_budget = 0
		total_actual = 0
		by_department = []
		by_account = []

		for plan in plans:
			items = frappe.get_all(
				"Budget Plan Item",
				filters={"parent": plan.name},
				fields=["account", "account_name", "annual_total"],
			)
			plan_actual = 0
			for item in items:
				actual = _get_actual(plan.cost_center, item.account, fiscal_year, company)
				plan_actual += actual
				budget_amt = flt(item.annual_total)
				total_budget += budget_amt
				total_actual += actual
				variance = budget_amt - actual
				by_account.append({
					"department": plan.department,
					"account": item.account,
					"budget": budget_amt,
					"actual": actual,
					"variance": variance,
					"variance_pct": (variance / budget_amt * 100) if budget_amt else 0,
					"consumption_pct": (actual / budget_amt * 100) if budget_amt else 0,
				})

			dept_budget = flt(plan.total_annual_amount)
			dept_variance = dept_budget - plan_actual
			by_department.append({
				"department": plan.department,
				"cost_center": plan.cost_center,
				"budget": dept_budget,
				"actual": plan_actual,
				"variance": dept_variance,
				"variance_pct": (dept_variance / dept_budget * 100) if dept_budget else 0,
				"consumption_pct": (plan_actual / dept_budget * 100) if dept_budget else 0,
			})

		total_variance = total_budget - total_actual
		return {
			"success": True,
			"data": {
				"summary": {
					"total_budget": total_budget,
					"total_actual": total_actual,
					"total_variance": total_variance,
					"consumption_pct": (total_actual / total_budget * 100) if total_budget else 0,
					"as_of_date": as_of_date or today(),
				},
				"by_department": by_department,
				"by_account": by_account,
			},
		}
	except Exception as e:
		frappe.log_error(f"get_budget_vs_actual error: {e}")
		return {"success": False, "error": str(e)}


def _get_actual(cost_center, account, fiscal_year, company):
	"""Get actual amount from GL Entry."""
	result = frappe.db.sql("""
		SELECT SUM(debit - credit)
		FROM `tabGL Entry`
		WHERE cost_center = %s AND account = %s
		  AND fiscal_year = %s AND company = %s AND is_cancelled = 0
	""", (cost_center, account, fiscal_year, company))
	return flt(result[0][0]) if result and result[0][0] else 0
