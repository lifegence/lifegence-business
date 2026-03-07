# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestControlActivity(FrappeTestCase):
	"""Test cases for Control Activity DocType."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for role_name in ("Audit Manager", "Auditor", "Risk Manager"):
			if not frappe.db.exists("Role", role_name):
				frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)
		frappe.db.commit()

	def _get_test_company(self):
		return frappe.db.get_value("Company", {}, "name") or "_Test Company"

	def _create_control(self, **kwargs):
		company = self._get_test_company()
		defaults = {
			"doctype": "Control Activity",
			"control_name": "テスト統制活動",
			"process_name": "月次決算処理",
			"department": frappe.db.get_value("Department", {"company": company}, "name") or "",
			"control_description": "<p>テスト統制説明</p>",
			"control_type": "Preventive",
			"frequency": "月次",
			"owner": frappe.session.user,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def test_create_control(self):
		"""Test basic control activity creation."""
		ctrl = self._create_control()
		self.assertEqual(ctrl.status, "Active")
		self.assertEqual(ctrl.control_type, "Preventive")
		self.assertEqual(ctrl.test_result, "Not Tested")

	def test_control_types(self):
		"""Test all control types."""
		for ctype in ["Preventive", "Detective", "Corrective"]:
			ctrl = self._create_control(control_type=ctype, control_name=f"テスト {ctype}")
			self.assertEqual(ctrl.control_type, ctype)

	def test_jsox_control(self):
		"""Test J-SOX relevant control activity."""
		ctrl = self._create_control(
			jsox_relevant=1,
			jsox_assertion="網羅性",
			jsox_process_category="業務プロセス",
		)
		self.assertEqual(ctrl.jsox_relevant, 1)
		self.assertEqual(ctrl.jsox_assertion, "網羅性")
		self.assertEqual(ctrl.jsox_process_category, "業務プロセス")

	def test_test_result_update(self):
		"""Test updating test result."""
		ctrl = self._create_control()
		ctrl.test_result = "Effective"
		ctrl.tested_by = frappe.session.user
		ctrl.save(ignore_permissions=True)
		self.assertEqual(ctrl.test_result, "Effective")
