# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt
from unittest.mock import patch, MagicMock


class TestGetActualsForAccounts(FrappeTestCase):
	"""Tests for the shared get_actuals_for_accounts utility."""

	def test_empty_accounts_returns_empty_dict(self):
		from lifegence_business.budget.utils import get_actuals_for_accounts

		result = get_actuals_for_accounts("CC-001", [], "2026", "Test Company")
		self.assertEqual(result, {})

	def test_none_accounts_returns_empty_dict(self):
		from lifegence_business.budget.utils import get_actuals_for_accounts

		result = get_actuals_for_accounts("CC-001", None, "2026", "Test Company")
		self.assertEqual(result, {})

	def test_no_fiscal_year_returns_empty_dict(self):
		from lifegence_business.budget.utils import get_actuals_for_accounts

		result = get_actuals_for_accounts("CC-001", ["Acc-1"], None, "Test Company")
		self.assertEqual(result, {})

	@patch("lifegence_business.budget.utils.frappe")
	def test_single_account_query(self, mock_frappe):
		"""Test that a single account returns correct mapping."""
		mock_frappe.db.sql.return_value = [
			MagicMock(account="Office Expenses - TC", actual=50000.0)
		]

		from lifegence_business.budget import utils
		# Temporarily replace frappe reference in the module
		original_frappe = utils.frappe
		utils.frappe = mock_frappe

		# Mock flt to behave like real flt
		original_flt = utils.flt
		utils.flt = flt

		try:
			result = utils.get_actuals_for_accounts(
				"Main - TC", ["Office Expenses - TC"], "2026", "_Test Company"
			)
			self.assertEqual(result, {"Office Expenses - TC": 50000.0})
			mock_frappe.db.sql.assert_called_once()

			# Verify the SQL uses IN and GROUP BY
			call_args = mock_frappe.db.sql.call_args
			sql = call_args[0][0]
			self.assertIn("IN %s", sql)
			self.assertIn("GROUP BY account", sql)
		finally:
			utils.frappe = original_frappe
			utils.flt = original_flt

	@patch("lifegence_business.budget.utils.frappe")
	def test_multiple_accounts_single_query(self, mock_frappe):
		"""Test that multiple accounts are fetched in ONE query."""
		mock_frappe.db.sql.return_value = [
			MagicMock(account="Office Expenses - TC", actual=50000.0),
			MagicMock(account="Travel Expenses - TC", actual=30000.0),
		]

		from lifegence_business.budget import utils
		original_frappe = utils.frappe
		utils.frappe = mock_frappe
		original_flt = utils.flt
		utils.flt = flt

		try:
			accounts = ["Office Expenses - TC", "Travel Expenses - TC", "Rent - TC"]
			result = utils.get_actuals_for_accounts(
				"Main - TC", accounts, "2026", "_Test Company"
			)

			# Only one SQL call for all accounts
			self.assertEqual(mock_frappe.db.sql.call_count, 1)

			# Accounts with GL entries return values
			self.assertEqual(result["Office Expenses - TC"], 50000.0)
			self.assertEqual(result["Travel Expenses - TC"], 30000.0)

			# Account with no GL entries is absent from dict
			self.assertNotIn("Rent - TC", result)
		finally:
			utils.frappe = original_frappe
			utils.flt = original_flt

	@patch("lifegence_business.budget.utils.frappe")
	def test_missing_account_defaults_to_zero(self, mock_frappe):
		"""Test that .get(account, 0) returns 0 for accounts without GL entries."""
		mock_frappe.db.sql.return_value = []

		from lifegence_business.budget import utils
		original_frappe = utils.frappe
		utils.frappe = mock_frappe
		original_flt = utils.flt
		utils.flt = flt

		try:
			result = utils.get_actuals_for_accounts(
				"Main - TC", ["Office Expenses - TC"], "2026", "_Test Company"
			)
			self.assertEqual(result.get("Office Expenses - TC", 0), 0)
		finally:
			utils.frappe = original_frappe
			utils.flt = original_flt

	def test_get_actual_for_account_wrapper(self):
		"""Test that _get_actual_for_account delegates to get_actuals_for_accounts."""
		from lifegence_business.budget import utils

		with patch.object(utils, "get_actuals_for_accounts", return_value={"Acc-1": 12345.0}) as mock_batch:
			result = utils._get_actual_for_account("CC-1", "Acc-1", "2026", "Company")
			self.assertEqual(result, 12345.0)
			mock_batch.assert_called_once_with("CC-1", ["Acc-1"], "2026", "Company")

	def test_get_actual_for_account_wrapper_missing(self):
		"""Test wrapper returns 0 when account not in result."""
		from lifegence_business.budget import utils

		with patch.object(utils, "get_actuals_for_accounts", return_value={}) as mock_batch:
			result = utils._get_actual_for_account("CC-1", "Acc-1", "2026", "Company")
			self.assertEqual(result, 0)
