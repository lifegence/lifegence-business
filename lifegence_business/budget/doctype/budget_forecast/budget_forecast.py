# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class BudgetForecast(Document):
	def before_save(self):
		if not self.prepared_by:
			self.prepared_by = frappe.session.user
		self._load_budget_data()

	def _load_budget_data(self):
		"""Load approved budget amount from Budget Plan."""
		if self.budget_plan:
			bp = frappe.get_doc("Budget Plan", self.budget_plan)
			self.approved_budget_amount = flt(bp.total_annual_amount)
			if not self.fiscal_year:
				self.fiscal_year = bp.fiscal_year
			if not self.department:
				self.department = bp.department
			if not self.cost_center:
				self.cost_center = bp.cost_center

	def calculate_forecast(self):
		"""Calculate forecast based on selected method."""
		forecast_month = int(self.forecast_month or 0)
		if forecast_month <= 0:
			return

		# Get actual to date from GL Entry
		self._update_actual_to_date(forecast_month)

		remaining_months = 12 - forecast_month

		if remaining_months <= 0:
			self.forecast_remaining = 0
		elif self.forecast_method == "Linear":
			monthly_avg = flt(self.actual_to_date) / forecast_month if forecast_month else 0
			self.forecast_remaining = monthly_avg * remaining_months
		elif self.forecast_method == "Average":
			recent_avg = self._get_recent_monthly_average(forecast_month, months=3)
			self.forecast_remaining = recent_avg * remaining_months
		elif self.forecast_method == "Trend":
			# Simple trend: use weighted recent months
			recent_avg = self._get_recent_monthly_average(forecast_month, months=3)
			overall_avg = flt(self.actual_to_date) / forecast_month if forecast_month else 0
			# Weighted: 70% recent trend, 30% overall average
			trend_avg = (recent_avg * 0.7) + (overall_avg * 0.3)
			self.forecast_remaining = trend_avg * remaining_months
		# Manual: user sets forecast_remaining directly

		self.forecast_to_year_end = flt(self.actual_to_date) + flt(self.forecast_remaining)
		self.variance_from_budget = flt(self.approved_budget_amount) - flt(self.forecast_to_year_end)
		if flt(self.approved_budget_amount):
			self.variance_pct = (flt(self.variance_from_budget) / flt(self.approved_budget_amount)) * 100
		else:
			self.variance_pct = 0

	def _update_actual_to_date(self, forecast_month):
		"""Get actual amount from GL Entry up to forecast_month."""
		if not self.budget_plan:
			return

		bp = frappe.get_doc("Budget Plan", self.budget_plan)
		result = frappe.db.sql("""
			SELECT SUM(debit - credit) as net_amount
			FROM `tabGL Entry`
			WHERE cost_center = %s
			  AND fiscal_year = %s
			  AND company = %s
			  AND is_cancelled = 0
		""", (bp.cost_center, bp.fiscal_year, bp.company))
		self.actual_to_date = flt(result[0][0]) if result and result[0][0] else 0

	def _get_recent_monthly_average(self, forecast_month, months=3):
		"""Get average of recent months' actuals."""
		if not self.budget_plan:
			return 0

		bp = frappe.get_doc("Budget Plan", self.budget_plan)
		settings = frappe.get_single("Budget Settings")
		start_month_num = int(settings.fiscal_year_start_month or 4)

		total = 0
		count = 0
		for i in range(max(1, forecast_month - months + 1), forecast_month + 1):
			calendar_month = ((start_month_num - 1 + i - 1) % 12) + 1
			result = frappe.db.sql("""
				SELECT SUM(debit - credit) as net_amount
				FROM `tabGL Entry`
				WHERE cost_center = %s
				  AND fiscal_year = %s
				  AND company = %s
				  AND MONTH(posting_date) = %s
				  AND is_cancelled = 0
			""", (bp.cost_center, bp.fiscal_year, bp.company, calendar_month))
			val = flt(result[0][0]) if result and result[0][0] else 0
			total += val
			count += 1

		return total / count if count else 0
