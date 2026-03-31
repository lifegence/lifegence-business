"""Tests for budget_vs_actual report — get_columns and get_data."""

import unittest
from unittest.mock import patch, MagicMock
from frappe.utils import flt


MODULE = "lifegence_business.budget.report.budget_vs_actual.budget_vs_actual"


class TestBudgetVsActualReport(unittest.TestCase):
    """Tests for the Budget vs Actual report."""

    def test_get_columns(self):
        """get_columns should return 8 columns with correct fieldnames."""
        from lifegence_business.budget.report.budget_vs_actual.budget_vs_actual import get_columns
        columns = get_columns()

        self.assertEqual(len(columns), 8)
        fieldnames = [c["fieldname"] for c in columns]
        self.assertIn("department", fieldnames)
        self.assertIn("budget_amount", fieldnames)
        self.assertIn("actual_amount", fieldnames)
        self.assertIn("variance_amount", fieldnames)
        self.assertIn("variance_pct", fieldnames)
        self.assertIn("consumption_pct", fieldnames)

    @patch(f"{MODULE}.get_actuals_for_accounts")
    @patch(f"{MODULE}.frappe")
    def test_get_data_basic(self, mock_frappe, mock_actuals):
        """Basic get_data call should produce rows with budget, actual, variance."""
        mock_frappe.db.sql.return_value = [
            MagicMock(
                department="Sales",
                cost_center="Main - TC",
                fiscal_year="FY-2026",
                company="Test Co",
                account="Office Expenses - TC",
                account_name="Office Expenses",
                annual_total=500000,
            ),
        ]
        mock_actuals.return_value = {"Office Expenses - TC": 200000}

        from lifegence_business.budget.report.budget_vs_actual.budget_vs_actual import get_data
        data = get_data({"company": "Test Co", "fiscal_year": "FY-2026"})

        self.assertEqual(len(data), 1)
        row = data[0]
        self.assertEqual(row["budget_amount"], 500000)
        self.assertEqual(row["actual_amount"], 200000)
        self.assertEqual(row["variance_amount"], 300000)
        self.assertAlmostEqual(row["variance_pct"], 60.0)
        self.assertAlmostEqual(row["consumption_pct"], 40.0)

    @patch(f"{MODULE}.get_actuals_for_accounts")
    @patch(f"{MODULE}.frappe")
    def test_get_data_zero_budget(self, mock_frappe, mock_actuals):
        """Zero budget should result in 0% variance and consumption."""
        mock_frappe.db.sql.return_value = [
            MagicMock(
                department="HR",
                cost_center="Main - TC",
                fiscal_year="FY-2026",
                company="Test Co",
                account="Training - TC",
                account_name="Training",
                annual_total=0,
            ),
        ]
        mock_actuals.return_value = {"Training - TC": 5000}

        from lifegence_business.budget.report.budget_vs_actual.budget_vs_actual import get_data
        data = get_data({})

        row = data[0]
        self.assertEqual(row["variance_pct"], 0)
        self.assertEqual(row["consumption_pct"], 0)

    @patch(f"{MODULE}.get_actuals_for_accounts")
    @patch(f"{MODULE}.frappe")
    def test_get_data_no_results(self, mock_frappe, mock_actuals):
        """Empty SQL result should return empty data list."""
        mock_frappe.db.sql.return_value = []

        from lifegence_business.budget.report.budget_vs_actual.budget_vs_actual import get_data
        data = get_data({})

        self.assertEqual(data, [])

    @patch(f"{MODULE}.get_actuals_for_accounts")
    @patch(f"{MODULE}.frappe")
    def test_get_data_groups_by_cost_center(self, mock_frappe, mock_actuals):
        """Multiple accounts under same cost_center should use one batch call."""
        mock_frappe.db.sql.return_value = [
            MagicMock(department="Sales", cost_center="Main - TC", fiscal_year="FY-2026",
                      company="Test Co", account="Office - TC", account_name="Office", annual_total=200000),
            MagicMock(department="Sales", cost_center="Main - TC", fiscal_year="FY-2026",
                      company="Test Co", account="Travel - TC", account_name="Travel", annual_total=100000),
        ]
        mock_actuals.return_value = {"Office - TC": 50000, "Travel - TC": 30000}

        from lifegence_business.budget.report.budget_vs_actual.budget_vs_actual import get_data
        data = get_data({})

        self.assertEqual(len(data), 2)
        # Only one batch call for both accounts
        mock_actuals.assert_called_once()
        call_args = mock_actuals.call_args[0]
        self.assertEqual(len(call_args[1]), 2)  # Two accounts in batch

    @patch(f"{MODULE}.get_actuals_for_accounts")
    @patch(f"{MODULE}.frappe")
    def test_get_data_no_filters(self, mock_frappe, mock_actuals):
        """Should work with None filters."""
        mock_frappe.db.sql.return_value = []

        from lifegence_business.budget.report.budget_vs_actual.budget_vs_actual import get_data
        data = get_data(None)

        self.assertEqual(data, [])

    def test_execute_returns_columns_and_data(self):
        """execute() should return (columns, data) tuple."""
        with patch(f"{MODULE}.get_columns") as mock_cols, \
             patch(f"{MODULE}.get_data") as mock_data:
            mock_cols.return_value = [{"fieldname": "test"}]
            mock_data.return_value = [{"test": 1}]

            from lifegence_business.budget.report.budget_vs_actual.budget_vs_actual import execute
            columns, data = execute({"company": "Test"})

            self.assertEqual(columns, [{"fieldname": "test"}])
            self.assertEqual(data, [{"test": 1}])


if __name__ == "__main__":
    unittest.main()
