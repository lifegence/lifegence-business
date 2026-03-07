# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class RiskRegister(Document):
	def before_save(self):
		self._calculate_risk_score()
		self._calculate_residual_risk()

	def _calculate_risk_score(self):
		likelihood = int(self.likelihood or 3)
		impact = int(self.impact or 3)
		self.risk_score = likelihood * impact
		self.risk_level = self._get_risk_level(self.risk_score)

	def _calculate_residual_risk(self):
		if self.residual_likelihood and self.residual_impact:
			self.residual_risk_score = int(self.residual_likelihood) * int(self.residual_impact)
			self.residual_risk_level = self._get_risk_level(self.residual_risk_score)

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
