# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, nowdate


class AntiSocialCheck(Document):
	def before_save(self):
		if not self.valid_until and self.check_date:
			self.valid_until = add_days(self.check_date, 365)

	def after_insert(self):
		self._update_customer_field()

	def on_update(self):
		self._update_customer_field()
		if self.result == "該当あり":
			self._suspend_credit_limits()
			self._create_alert()

	def _update_customer_field(self):
		"""Update Customer.anti_social_check_result with latest result."""
		frappe.db.set_value(
			"Customer", self.customer,
			"anti_social_check_result", self.result,
			update_modified=False,
		)

	def _suspend_credit_limits(self):
		"""Suspend all credit limits for this customer if result is 該当あり."""
		credit_limits = frappe.get_all(
			"Credit Limit",
			filters={"customer": self.customer, "status": ["!=", "Suspended"]},
			pluck="name",
		)
		for cl_name in credit_limits:
			frappe.db.set_value("Credit Limit", cl_name, {
				"status": "Suspended",
				"suspension_reason": _("反社チェックで「該当あり」の結果が確認されたため停止"),
			})

	def _create_alert(self):
		"""Create a Critical alert when anti-social check result is 該当あり."""
		frappe.get_doc({
			"doctype": "Credit Alert",
			"customer": self.customer,
			"company": self.company,
			"alert_type": "反社チェック期限",
			"severity": "Critical",
			"alert_message": _("取引先 {0} の反社チェックで「該当あり」が確認されました。取引を停止してください。").format(
				self.customer_name or self.customer
			),
			"anti_social_check": self.name,
		}).insert(ignore_permissions=True)
