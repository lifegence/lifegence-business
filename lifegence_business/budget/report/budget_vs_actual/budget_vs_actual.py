# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "department", "label": "部門", "fieldtype": "Link", "options": "Department", "width": 150},
		{"fieldname": "cost_center", "label": "原価センター", "fieldtype": "Link", "options": "Cost Center", "width": 150},
		{"fieldname": "account", "label": "勘定科目", "fieldtype": "Link", "options": "Account", "width": 200},
		{"fieldname": "budget_amount", "label": "予算額", "fieldtype": "Currency", "width": 150},
		{"fieldname": "actual_amount", "label": "実績額", "fieldtype": "Currency", "width": 150},
		{"fieldname": "variance_amount", "label": "差異金額", "fieldtype": "Currency", "width": 150},
		{"fieldname": "variance_pct", "label": "差異率(%)", "fieldtype": "Percent", "width": 100},
		{"fieldname": "consumption_pct", "label": "消化率(%)", "fieldtype": "Percent", "width": 100},
	]


def get_data(filters):
	if not filters:
		filters = {}

	conditions = ["bp.docstatus = 1", "bp.status IN ('Approved', 'Revised')"]
	values = {}

	if filters.get("company"):
		conditions.append("bp.company = %(company)s")
		values["company"] = filters["company"]
	if filters.get("fiscal_year"):
		conditions.append("bp.fiscal_year = %(fiscal_year)s")
		values["fiscal_year"] = filters["fiscal_year"]
	if filters.get("department"):
		conditions.append("bp.department = %(department)s")
		values["department"] = filters["department"]
	if filters.get("cost_center"):
		conditions.append("bp.cost_center = %(cost_center)s")
		values["cost_center"] = filters["cost_center"]

	where_clause = " AND ".join(conditions)
	budget_data = frappe.db.sql(f"""
		SELECT
			bp.department, bp.cost_center, bp.fiscal_year, bp.company,
			bpi.account, bpi.account_name, bpi.annual_total
		FROM `tabBudget Plan Item` bpi
		INNER JOIN `tabBudget Plan` bp ON bp.name = bpi.parent
		WHERE {where_clause}
		ORDER BY bp.department, bpi.account
	""", values, as_dict=True)

	data = []
	for row in budget_data:
		actual = _get_actual(row.cost_center, row.account, row.fiscal_year, row.company)
		budget = flt(row.annual_total)
		variance = budget - actual
		data.append({
			"department": row.department,
			"cost_center": row.cost_center,
			"account": row.account,
			"budget_amount": budget,
			"actual_amount": actual,
			"variance_amount": variance,
			"variance_pct": (variance / budget * 100) if budget else 0,
			"consumption_pct": (actual / budget * 100) if budget else 0,
		})
	return data


def _get_actual(cost_center, account, fiscal_year, company):
	result = frappe.db.sql("""
		SELECT SUM(debit - credit) as net
		FROM `tabGL Entry`
		WHERE cost_center = %s AND account = %s
		  AND fiscal_year = %s AND company = %s AND is_cancelled = 0
	""", (cost_center, account, fiscal_year, company))
	return flt(result[0][0]) if result and result[0][0] else 0
