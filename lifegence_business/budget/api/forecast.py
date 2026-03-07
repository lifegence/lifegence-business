# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today


@frappe.whitelist()
def update_forecast(budget_forecast=None, budget_plan=None, forecast_month=None, method=None):
	"""Update or create a Budget Forecast."""
	try:
		if budget_forecast:
			doc = frappe.get_doc("Budget Forecast", budget_forecast)
		elif budget_plan:
			if not forecast_month:
				return {"success": False, "error": "forecast_month is required for new forecast"}
			doc = frappe.get_doc({
				"doctype": "Budget Forecast",
				"budget_plan": budget_plan,
				"forecast_month": str(forecast_month),
				"forecast_date": today(),
			})
			doc.insert(ignore_permissions=True)
		else:
			return {"success": False, "error": "budget_forecast or budget_plan is required"}

		if method:
			doc.forecast_method = method

		doc.calculate_forecast()
		doc.save(ignore_permissions=True)

		return {
			"success": True,
			"data": {
				"budget_forecast": doc.name,
				"budget_plan": doc.budget_plan,
				"forecast_month": doc.forecast_month,
				"approved_budget": doc.approved_budget_amount,
				"actual_to_date": doc.actual_to_date,
				"forecast_to_year_end": doc.forecast_to_year_end,
				"variance_from_budget": doc.variance_from_budget,
				"variance_pct": doc.variance_pct,
				"method": doc.forecast_method,
			},
		}
	except Exception as e:
		frappe.log_error(f"update_forecast error: {e}")
		return {"success": False, "error": str(e)}
