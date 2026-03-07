# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestRiskRegister(FrappeTestCase):
	"""Test cases for Risk Register DocType."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for role_name in ("Audit Manager", "Auditor", "Risk Manager"):
			if not frappe.db.exists("Role", role_name):
				frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)
		frappe.db.commit()

	def _get_test_company(self):
		return frappe.db.get_value("Company", {}, "name") or "_Test Company"

	def _create_risk(self, **kwargs):
		company = self._get_test_company()
		defaults = {
			"doctype": "Risk Register",
			"risk_title": "テストリスク",
			"risk_category": "業務リスク",
			"department": frappe.db.get_value("Department", {"company": company}, "name") or "",
			"risk_description": "<p>テスト用リスク説明</p>",
			"likelihood": "3",
			"impact": "3",
			"risk_owner": frappe.session.user,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def test_create_risk(self):
		"""Test basic risk creation."""
		risk = self._create_risk()
		self.assertEqual(risk.status, "Active")
		self.assertEqual(risk.risk_category, "業務リスク")

	def test_risk_score_calculation(self):
		"""Test automatic risk score calculation."""
		risk = self._create_risk(likelihood="4", impact="5")
		self.assertEqual(risk.risk_score, 20)
		self.assertEqual(risk.risk_level, "Critical")

	def test_risk_level_critical(self):
		"""Test Critical risk level (20-25)."""
		risk = self._create_risk(likelihood="5", impact="5")
		self.assertEqual(risk.risk_score, 25)
		self.assertEqual(risk.risk_level, "Critical")

	def test_risk_level_high(self):
		"""Test High risk level (12-19)."""
		risk = self._create_risk(likelihood="4", impact="4")
		self.assertEqual(risk.risk_score, 16)
		self.assertEqual(risk.risk_level, "High")

	def test_risk_level_medium(self):
		"""Test Medium risk level (6-11)."""
		risk = self._create_risk(likelihood="3", impact="3")
		self.assertEqual(risk.risk_score, 9)
		self.assertEqual(risk.risk_level, "Medium")

	def test_risk_level_low(self):
		"""Test Low risk level (1-5)."""
		risk = self._create_risk(likelihood="1", impact="2")
		self.assertEqual(risk.risk_score, 2)
		self.assertEqual(risk.risk_level, "Low")

	def test_residual_risk_calculation(self):
		"""Test residual risk calculation."""
		risk = self._create_risk(
			likelihood="4", impact="5",
			residual_likelihood="2", residual_impact="3",
		)
		self.assertEqual(risk.residual_risk_score, 6)
		self.assertEqual(risk.residual_risk_level, "Medium")

	def test_jsox_risk(self):
		"""Test J-SOX relevant risk."""
		risk = self._create_risk(
			jsox_relevant=1,
			jsox_assertion="実在性",
		)
		self.assertEqual(risk.jsox_relevant, 1)
		self.assertEqual(risk.jsox_assertion, "実在性")
