# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class RiskAssessment(Document):
	def before_save(self):
		if self.is_new():
			self.assessor = self.assessor or frappe.session.user
			self.assessment_date = self.assessment_date or today()
		self._calculate_score()
		self._calculate_trend()

	def after_insert(self):
		self._update_risk_register()

	def _calculate_score(self):
		likelihood = int(self.likelihood_score or 3)
		impact = int(self.impact_score or 3)
		self.risk_score = likelihood * impact
		self.risk_level = self._get_risk_level(self.risk_score)

	def _calculate_trend(self):
		previous = frappe.get_all(
			"Risk Assessment",
			filters={"risk_register": self.risk_register, "name": ["!=", self.name or ""]},
			fields=["risk_score"],
			order_by="assessment_date desc",
			limit=1,
		)
		if previous:
			self.previous_risk_score = previous[0].risk_score
			if self.risk_score > self.previous_risk_score:
				self.score_trend = "上昇"
			elif self.risk_score < self.previous_risk_score:
				self.score_trend = "下降"
			else:
				self.score_trend = "横ばい"

	def _update_risk_register(self):
		risk = frappe.get_doc("Risk Register", self.risk_register)
		risk.likelihood = self.likelihood_score
		risk.impact = self.impact_score
		risk.save(ignore_permissions=True)

	@staticmethod
	def _get_risk_level(score):
		if score >= 20:
			return "Critical"
		elif score >= 12:
			return "High"
		elif score >= 6:
			return "Medium"
		else:
			return "Low"
