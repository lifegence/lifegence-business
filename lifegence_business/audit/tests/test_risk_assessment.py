# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestRiskAssessment(FrappeTestCase):
	"""Test cases for Risk Assessment DocType."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for role_name in ("Audit Manager", "Auditor", "Risk Manager"):
			if not frappe.db.exists("Role", role_name):
				frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)
		frappe.db.commit()

	def _get_test_company(self):
		return frappe.db.get_value("Company", {}, "name") or "_Test Company"

	def _create_risk(self):
		company = self._get_test_company()
		doc = frappe.get_doc({
			"doctype": "Risk Register",
			"risk_title": "テストアセスメント用リスク",
			"risk_category": "財務リスク",
			"department": frappe.db.get_value("Department", {"company": company}, "name") or "",
			"risk_description": "<p>テスト</p>",
			"likelihood": "3",
			"impact": "3",
			"risk_owner": frappe.session.user,
		})
		doc.insert(ignore_permissions=True)
		return doc

	def _create_assessment(self, risk_register, **kwargs):
		defaults = {
			"doctype": "Risk Assessment",
			"risk_register": risk_register,
			"likelihood_score": "3",
			"impact_score": "4",
			"assessment_type": "定期評価",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def test_create_assessment(self):
		"""Test basic assessment creation."""
		risk = self._create_risk()
		assessment = self._create_assessment(risk.name)
		self.assertEqual(assessment.risk_score, 12)
		self.assertEqual(assessment.risk_level, "High")
		self.assertIsNotNone(assessment.assessor)

	def test_assessment_updates_risk(self):
		"""Test that assessment updates the risk register."""
		risk = self._create_risk()
		self._create_assessment(risk.name, likelihood_score="5", impact_score="4")
		risk.reload()
		self.assertEqual(int(risk.likelihood), 5)
		self.assertEqual(int(risk.impact), 4)

	def test_score_trend_up(self):
		"""Test score trend detection - increase."""
		risk = self._create_risk()
		self._create_assessment(risk.name, likelihood_score="2", impact_score="2")
		a2 = self._create_assessment(risk.name, likelihood_score="4", impact_score="4")
		self.assertEqual(a2.score_trend, "上昇")

	def test_score_trend_down(self):
		"""Test score trend detection - decrease."""
		risk = self._create_risk()
		self._create_assessment(risk.name, likelihood_score="4", impact_score="4")
		a2 = self._create_assessment(risk.name, likelihood_score="2", impact_score="2")
		self.assertEqual(a2.score_trend, "下降")

	def test_api_create_assessment(self):
		"""Test create_risk_assessment API."""
		risk = self._create_risk()
		from lifegence_audit.api.risk import create_risk_assessment

		result = create_risk_assessment(
			risk_register=risk.name,
			likelihood_score="4",
			impact_score="5",
			overall_assessment="テスト評価",
		)
		self.assertTrue(result["success"])
		self.assertEqual(result["data"]["risk_level"], "Critical")
