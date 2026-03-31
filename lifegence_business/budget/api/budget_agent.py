# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from typing import Dict, Any, Optional

from lifegence_business.budget.utils import get_actuals_for_accounts


@frappe.whitelist()
def get_budget_variance(
	department: Optional[str] = None,
	fiscal_year: Optional[str] = None,
) -> Dict[str, Any]:
	"""Check budget variance for department."""
	if not fiscal_year:
		fiscal_year = frappe.db.get_value(
			"Fiscal Year", {"disabled": 0}, "name", order_by="year_start_date desc"
		)

	company = frappe.db.get_value("Company", {}, "name")
	if not company:
		frappe.throw("会社データが見つかりません。", frappe.ValidationError)

	filters = {
		"fiscal_year": fiscal_year,
		"docstatus": 1,
		"status": ["in", ["Approved", "Revised"]],
		"company": company,
	}
	if department:
		filters["department"] = department

	plans = frappe.get_all(
		"Budget Plan",
		filters=filters,
		fields=["name", "department", "cost_center", "total_annual_amount"],
	)

	if not plans:
		frappe.throw(f"{fiscal_year}の承認済み予算計画が見つかりません。", frappe.ValidationError)

	departments = []
	for plan in plans:
		items = frappe.get_all(
			"Budget Plan Item",
			filters={"parent": plan.name},
			fields=["account", "account_name", "annual_total"],
		)
		accounts = [item.account for item in items]
		actuals_map = get_actuals_for_accounts(
			plan.cost_center, accounts, fiscal_year, company
		)
		total_actual = 0
		alerts = []
		for item in items:
			actual = actuals_map.get(item.account, 0)
			total_actual += actual
			budget = flt(item.annual_total)
			if budget and actual > budget:
				alerts.append({
					"account_name": item.account_name,
					"budget": budget,
					"actual": actual,
				})

		budget_total = flt(plan.total_annual_amount)
		pct = (total_actual / budget_total * 100) if budget_total else 0
		departments.append({
			"department": plan.department,
			"budget_total": budget_total,
			"actual_total": total_actual,
			"variance": budget_total - total_actual,
			"utilization_pct": round(pct, 1),
			"alerts": alerts,
		})

	return {
		"success": True,
		"fiscal_year": fiscal_year,
		"departments": departments,
	}


@frappe.whitelist()
def get_forecast_landing(
	department: Optional[str] = None,
	fiscal_year: Optional[str] = None,
) -> Dict[str, Any]:
	"""Generate forecast landing estimate."""
	if not fiscal_year:
		fiscal_year = frappe.db.get_value(
			"Fiscal Year", {"disabled": 0}, "name", order_by="year_start_date desc"
		)

	filters = {"budget_plan": ["like", "%"], "status": ["in", ["Draft", "Final"]]}
	forecasts = frappe.get_all(
		"Budget Forecast",
		filters=filters,
		fields=[
			"name", "budget_plan", "department", "approved_budget_amount",
			"actual_to_date", "forecast_to_year_end", "variance_from_budget",
			"forecast_method",
		],
		order_by="forecast_date desc",
		limit=20,
	)

	if department:
		forecasts = [f for f in forecasts if f.department == department]

	if not forecasts:
		frappe.throw("着地見込みデータが見つかりません。", frappe.ValidationError)

	items = []
	for fc in forecasts:
		items.append({
			"department": fc.department,
			"budget": flt(fc.approved_budget_amount),
			"landing": flt(fc.forecast_to_year_end),
			"variance": flt(fc.variance_from_budget),
			"forecast_method": fc.forecast_method,
		})

	return {
		"success": True,
		"fiscal_year": fiscal_year,
		"forecasts": items,
	}


@frappe.whitelist()
def create_budget_plan_draft(
	department: str,
	fiscal_year: str,
	adjustment_pct: float = 0,
) -> Dict[str, Any]:
	"""Draft a budget plan based on previous year actuals."""
	company = frappe.db.get_value("Company", {}, "name")
	if not company:
		frappe.throw("会社データが見つかりません。", frappe.ValidationError)

	cost_center = frappe.db.get_value("Department", department, "cost_center")
	if not cost_center:
		frappe.throw(f"部門 '{department}' に原価センターが設定されていません。", frappe.ValidationError)

	# Get previous year fiscal year
	prev_fy = frappe.db.get_value(
		"Fiscal Year",
		{"name": ["!=", fiscal_year], "disabled": 0},
		"name",
		order_by="year_start_date desc",
	)
	if not prev_fy:
		frappe.throw("前年度の会計年度が見つかりません。", frappe.ValidationError)

	# Get previous year actuals
	actuals = frappe.db.sql("""
		SELECT account, SUM(debit - credit) as total
		FROM `tabGL Entry`
		WHERE cost_center = %s AND fiscal_year = %s AND company = %s AND is_cancelled = 0
		GROUP BY account
		HAVING total > 0
	""", (cost_center, prev_fy, company), as_dict=True)

	if not actuals:
		frappe.throw(f"前年度（{prev_fy}）の実績データが見つかりません。", frappe.ValidationError)

	adjustment = 1 + (flt(adjustment_pct) / 100)
	items = []
	total = 0
	for row in actuals:
		amount = flt(row.total) * adjustment
		total += amount
		account_name = frappe.db.get_value("Account", row.account, "account_name") or row.account
		items.append({
			"account": row.account,
			"account_name": account_name,
			"previous_actual": flt(row.total),
			"proposed_amount": round(amount),
		})

	return {
		"success": True,
		"department": department,
		"fiscal_year": fiscal_year,
		"adjustment_pct": adjustment_pct,
		"previous_fiscal_year": prev_fy,
		"items": items,
		"total": round(total),
	}
