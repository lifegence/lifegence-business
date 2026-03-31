"""Tests for check_budget_availability and check_budget_alerts in budget/utils.py.

Supplements existing test_budget_utils.py which covers get_actuals_for_accounts.
"""

import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from frappe.utils import flt


MODULE = "lifegence_business.budget.utils"


class TestCheckBudgetAvailability(unittest.TestCase):
    """Tests for check_budget_availability hook."""

    def _make_po_doc(self, items=None):
        """Create a mock Purchase Order doc."""
        doc = MagicMock()
        doc.doctype = "Purchase Order"
        doc.company = "Test Company"
        doc.transaction_date = "2026-03-15"
        if items is None:
            item = MagicMock()
            item.cost_center = "Main - TC"
            item.expense_account = "Office Expenses - TC"
            item.amount = 50000
            items = [item]
        doc.items = items
        return doc

    def _make_je_doc(self, accounts=None):
        """Create a mock Journal Entry doc."""
        doc = MagicMock()
        doc.doctype = "Journal Entry"
        doc.company = "Test Company"
        doc.posting_date = "2026-03-15"
        if accounts is None:
            entry = MagicMock()
            entry.cost_center = "Main - TC"
            entry.account = "Office Expenses - TC"
            entry.debit_in_account_currency = 30000
            accounts = [entry]
        doc.accounts = accounts
        return doc

    @patch(f"{MODULE}._get_fiscal_year", return_value="FY-2026")
    @patch(f"{MODULE}._get_actual_for_account", return_value=40000)
    @patch(f"{MODULE}._get_budget_for_account", return_value={"annual_total": 100000})
    @patch(f"{MODULE}.frappe")
    def test_po_within_budget_no_action(self, mock_frappe, mock_budget, mock_actual, mock_fy):
        """PO within budget should not throw or warn."""
        mock_settings = MagicMock()
        mock_settings.check_budget_on_purchase_order = True
        mock_settings.variance_action = "Stop"
        mock_frappe.get_single.return_value = mock_settings

        from lifegence_business.budget.utils import check_budget_availability
        doc = self._make_po_doc()
        # remaining = 100000 - 40000 - 50000 = 10000 >= 0 → no throw
        check_budget_availability(doc, "on_submit")

        mock_frappe.throw.assert_not_called()
        mock_frappe.msgprint.assert_not_called()

    @patch(f"{MODULE}._get_fiscal_year", return_value="FY-2026")
    @patch(f"{MODULE}._get_actual_for_account", return_value=70000)
    @patch(f"{MODULE}._get_budget_for_account", return_value={"annual_total": 100000})
    @patch(f"{MODULE}.frappe")
    def test_po_exceeds_budget_stop(self, mock_frappe, mock_budget, mock_actual, mock_fy):
        """PO exceeding budget with Stop action should throw."""
        mock_settings = MagicMock()
        mock_settings.check_budget_on_purchase_order = True
        mock_settings.variance_action = "Stop"
        mock_frappe.get_single.return_value = mock_settings
        mock_frappe.ValidationError = Exception

        from lifegence_business.budget.utils import check_budget_availability
        doc = self._make_po_doc()
        # remaining = 100000 - 70000 - 50000 = -20000 < 0
        check_budget_availability(doc, "on_submit")

        mock_frappe.throw.assert_called_once()

    @patch(f"{MODULE}._get_fiscal_year", return_value="FY-2026")
    @patch(f"{MODULE}._get_actual_for_account", return_value=70000)
    @patch(f"{MODULE}._get_budget_for_account", return_value={"annual_total": 100000})
    @patch(f"{MODULE}.frappe")
    def test_po_exceeds_budget_warn(self, mock_frappe, mock_budget, mock_actual, mock_fy):
        """PO exceeding budget with Warn action should msgprint."""
        mock_settings = MagicMock()
        mock_settings.check_budget_on_purchase_order = True
        mock_settings.variance_action = "Warn"
        mock_frappe.get_single.return_value = mock_settings

        from lifegence_business.budget.utils import check_budget_availability
        doc = self._make_po_doc()
        check_budget_availability(doc, "on_submit")

        mock_frappe.msgprint.assert_called_once()
        mock_frappe.throw.assert_not_called()

    @patch(f"{MODULE}.frappe")
    def test_po_check_disabled_returns_early(self, mock_frappe):
        """When check_budget_on_purchase_order is false, skip."""
        mock_settings = MagicMock()
        mock_settings.check_budget_on_purchase_order = False
        mock_frappe.get_single.return_value = mock_settings

        from lifegence_business.budget.utils import check_budget_availability
        doc = self._make_po_doc()
        check_budget_availability(doc, "on_submit")

        mock_frappe.throw.assert_not_called()

    @patch(f"{MODULE}.frappe")
    def test_je_check_disabled_returns_early(self, mock_frappe):
        """When check_budget_on_journal_entry is false, skip."""
        mock_settings = MagicMock()
        mock_settings.check_budget_on_journal_entry = False
        mock_frappe.get_single.return_value = mock_settings

        from lifegence_business.budget.utils import check_budget_availability
        doc = self._make_je_doc()
        check_budget_availability(doc, "on_submit")

        mock_frappe.throw.assert_not_called()

    @patch(f"{MODULE}._get_fiscal_year", return_value="FY-2026")
    @patch(f"{MODULE}._get_actual_for_account", return_value=0)
    @patch(f"{MODULE}._get_budget_for_account", return_value=None)
    @patch(f"{MODULE}.frappe")
    def test_no_budget_record_skipped(self, mock_frappe, mock_budget, mock_actual, mock_fy):
        """When no budget exists for the account, no action taken."""
        mock_settings = MagicMock()
        mock_settings.check_budget_on_purchase_order = True
        mock_frappe.get_single.return_value = mock_settings

        from lifegence_business.budget.utils import check_budget_availability
        doc = self._make_po_doc()
        check_budget_availability(doc, "on_submit")

        mock_frappe.throw.assert_not_called()
        mock_frappe.msgprint.assert_not_called()

    @patch(f"{MODULE}._get_fiscal_year", return_value="FY-2026")
    @patch(f"{MODULE}._get_actual_for_account", return_value=60000)
    @patch(f"{MODULE}._get_budget_for_account", return_value={"annual_total": 100000})
    @patch(f"{MODULE}.frappe")
    def test_je_exceeds_budget_stop(self, mock_frappe, mock_budget, mock_actual, mock_fy):
        """JE exceeding budget with Stop action should throw."""
        mock_settings = MagicMock()
        mock_settings.check_budget_on_journal_entry = True
        mock_settings.variance_action = "Stop"
        mock_frappe.get_single.return_value = mock_settings
        mock_frappe.ValidationError = Exception

        from lifegence_business.budget.utils import check_budget_availability
        doc = self._make_je_doc()
        # remaining = 100000 - 60000 - 30000 = 10000 >= 0 → actually passes
        # Let's adjust actual to 80000 to exceed
        mock_actual.return_value = 80000
        check_budget_availability(doc, "on_submit")

        mock_frappe.throw.assert_called_once()

    @patch(f"{MODULE}._get_fiscal_year", return_value="FY-2026")
    @patch(f"{MODULE}._get_actual_for_account", return_value=0)
    @patch(f"{MODULE}._get_budget_for_account", return_value={"annual_total": 100000})
    @patch(f"{MODULE}.frappe")
    def test_po_item_without_cost_center_skipped(self, mock_frappe, mock_budget, mock_actual, mock_fy):
        """PO items without cost_center should be skipped."""
        mock_settings = MagicMock()
        mock_settings.check_budget_on_purchase_order = True
        mock_settings.variance_action = "Stop"
        mock_frappe.get_single.return_value = mock_settings

        item = MagicMock()
        item.cost_center = None
        item.expense_account = "Office Expenses - TC"
        item.amount = 50000

        from lifegence_business.budget.utils import check_budget_availability
        doc = self._make_po_doc(items=[item])
        check_budget_availability(doc, "on_submit")

        # _get_budget_for_account should not be called since item is skipped
        mock_budget.assert_not_called()


class TestCheckBudgetAlerts(unittest.TestCase):
    """Tests for check_budget_alerts daily scheduler."""

    @patch(f"{MODULE}.get_actuals_for_accounts")
    @patch(f"{MODULE}.frappe")
    def test_alerts_for_high_consumption(self, mock_frappe, mock_actuals):
        """Should log warning when consumption exceeds threshold."""
        mock_settings = MagicMock()
        mock_settings.variance_threshold_pct = 10  # Alert at 90%+
        mock_frappe.get_single.return_value = mock_settings

        mock_frappe.get_all.side_effect = [
            # Plans
            [MagicMock(name="BP-001", cost_center="Main - TC", fiscal_year="FY-2026",
                       company="Test Co", total_annual_amount=1000000, department="Sales")],
            # Plan items
            [MagicMock(account="Office Expenses - TC", annual_total=500000)],
        ]

        mock_actuals.return_value = {"Office Expenses - TC": 480000}  # 96% consumption

        mock_logger = MagicMock()
        mock_frappe.logger.return_value = mock_logger

        from lifegence_business.budget.utils import check_budget_alerts
        check_budget_alerts()

        mock_logger.warning.assert_called_once()
        self.assertIn("96.0%", mock_logger.warning.call_args[0][0])

    @patch(f"{MODULE}.get_actuals_for_accounts")
    @patch(f"{MODULE}.frappe")
    def test_no_alert_below_threshold(self, mock_frappe, mock_actuals):
        """Should not log when consumption is below threshold."""
        mock_settings = MagicMock()
        mock_settings.variance_threshold_pct = 10
        mock_frappe.get_single.return_value = mock_settings

        mock_frappe.get_all.side_effect = [
            [MagicMock(name="BP-001", cost_center="Main - TC", fiscal_year="FY-2026",
                       company="Test Co", total_annual_amount=1000000, department="Sales")],
            [MagicMock(account="Office Expenses - TC", annual_total=500000)],
        ]

        mock_actuals.return_value = {"Office Expenses - TC": 200000}  # 40% consumption

        mock_logger = MagicMock()
        mock_frappe.logger.return_value = mock_logger

        from lifegence_business.budget.utils import check_budget_alerts
        check_budget_alerts()

        mock_logger.warning.assert_not_called()

    @patch(f"{MODULE}.get_actuals_for_accounts")
    @patch(f"{MODULE}.frappe")
    def test_skip_plan_with_zero_total(self, mock_frappe, mock_actuals):
        """Plans with total_annual_amount = 0 should be skipped."""
        mock_settings = MagicMock()
        mock_settings.variance_threshold_pct = 10
        mock_frappe.get_single.return_value = mock_settings

        mock_frappe.get_all.side_effect = [
            [MagicMock(name="BP-001", cost_center="Main - TC", fiscal_year="FY-2026",
                       company="Test Co", total_annual_amount=0, department="Sales")],
        ]

        from lifegence_business.budget.utils import check_budget_alerts
        check_budget_alerts()

        mock_actuals.assert_not_called()

    @patch(f"{MODULE}.get_actuals_for_accounts")
    @patch(f"{MODULE}.frappe")
    def test_skip_item_with_zero_annual_total(self, mock_frappe, mock_actuals):
        """Items with annual_total = 0 should be skipped (no div by zero)."""
        mock_settings = MagicMock()
        mock_settings.variance_threshold_pct = 10
        mock_frappe.get_single.return_value = mock_settings

        mock_frappe.get_all.side_effect = [
            [MagicMock(name="BP-001", cost_center="Main - TC", fiscal_year="FY-2026",
                       company="Test Co", total_annual_amount=1000000, department="Sales")],
            [MagicMock(account="Office Expenses - TC", annual_total=0)],
        ]

        mock_actuals.return_value = {"Office Expenses - TC": 0}

        mock_logger = MagicMock()
        mock_frappe.logger.return_value = mock_logger

        from lifegence_business.budget.utils import check_budget_alerts
        check_budget_alerts()

        mock_logger.warning.assert_not_called()

    @patch(f"{MODULE}.get_actuals_for_accounts")
    @patch(f"{MODULE}.frappe")
    def test_default_threshold_10_when_not_set(self, mock_frappe, mock_actuals):
        """When variance_threshold_pct is 0/None, defaults to 10."""
        mock_settings = MagicMock()
        mock_settings.variance_threshold_pct = 0  # falsy
        mock_frappe.get_single.return_value = mock_settings

        mock_frappe.get_all.side_effect = [
            [MagicMock(name="BP-001", cost_center="Main - TC", fiscal_year="FY-2026",
                       company="Test Co", total_annual_amount=1000000, department="Sales")],
            [MagicMock(account="Office Expenses - TC", annual_total=100000)],
        ]
        # 91% consumption should trigger at 10% threshold (100-10=90)
        mock_actuals.return_value = {"Office Expenses - TC": 91000}

        mock_logger = MagicMock()
        mock_frappe.logger.return_value = mock_logger

        from lifegence_business.budget.utils import check_budget_alerts
        check_budget_alerts()

        mock_logger.warning.assert_called_once()


if __name__ == "__main__":
    unittest.main()
