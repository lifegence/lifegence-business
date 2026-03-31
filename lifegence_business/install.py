# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


# ===========================================================================
# Public entry points
# ===========================================================================

def after_install():
	"""Run after app installation -- sets up all 5 modules."""
	_install_contract_approval()
	_install_credit()
	_install_budget()
	_install_helpdesk()
	_install_dms()
	frappe.db.commit()
	print("Lifegence Business: Installation complete.")


def after_migrate():
	"""Run after bench migrate -- idempotent setup."""
	frappe.db.commit()


# ===========================================================================
# Per-module install functions
# ===========================================================================

def _install_credit():
	"""Credit module: roles, custom fields, default settings."""
	try:
		_create_credit_roles()
		_create_credit_custom_fields()
		_init_credit_settings()
		frappe.msgprint("Lifegence Business [Credit]: Setup complete.")
	except Exception:
		frappe.log_error("Lifegence Business [Credit]: Error during setup")
		raise


def _install_budget():
	"""Budget module: roles, default settings."""
	try:
		_create_budget_roles()
		_init_budget_settings()
		frappe.msgprint("Lifegence Business [Budget]: Setup complete.")
	except Exception:
		frappe.log_error("Lifegence Business [Budget]: Error during setup")
		raise


def _install_helpdesk():
	"""Helpdesk module: roles, default categories, default SLA policy."""
	try:
		_create_helpdesk_roles()
		_create_default_hd_categories()
		_create_default_sla_policy()
		frappe.msgprint("Lifegence Business [Helpdesk]: Setup complete.")
	except Exception:
		frappe.log_error("Lifegence Business [Helpdesk]: Error during setup")
		raise


def _install_dms():
	"""DMS module: roles, default retention policies."""
	try:
		_create_dms_roles()
		_create_default_retention_policies()
		frappe.msgprint("Lifegence Business [DMS]: Setup complete.")
	except Exception:
		frappe.log_error("Lifegence Business [DMS]: Error during setup")
		raise


# ===========================================================================
# Contract Approval helpers
# ===========================================================================

def _install_contract_approval():
	"""Contract Approval module: roles."""
	try:
		_create_contract_approval_roles()
		frappe.msgprint("Lifegence Business [Contract Approval]: Setup complete.")
	except Exception:
		frappe.log_error("Lifegence Business [Contract Approval]: Error during setup")
		raise


def _create_contract_approval_roles():
	"""Create Contract Manager and Contract Approver roles."""
	for role_name in ("Contract Manager", "Contract Approver"):
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
			}).insert(ignore_permissions=True)
			frappe.logger().info(f"Business [Contract Approval]: Created role '{role_name}'")



# ===========================================================================
# Credit helpers
# ===========================================================================

def _create_credit_roles():
	"""Create Credit Manager and Credit Approver roles."""
	for role_name in ("Credit Manager", "Credit Approver"):
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
			}).insert(ignore_permissions=True)
			frappe.logger().info(f"Business [Credit]: Created role '{role_name}'")


def _create_credit_custom_fields():
	"""Add custom fields to Customer and Sales Order."""
	custom_fields = {
		"Customer": [
			{
				"fieldname": "credit_section_break",
				"fieldtype": "Section Break",
				"label": "与信管理",
				"insert_after": "default_currency",
				"collapsible": 1,
			},
			{
				"fieldname": "risk_grade",
				"fieldtype": "Data",
				"label": "リスクグレード",
				"insert_after": "credit_section_break",
				"read_only": 1,
				"description": "与信審査に基づくリスクグレード（A〜E）",
			},
			{
				"fieldname": "credit_status",
				"fieldtype": "Data",
				"label": "与信ステータス",
				"insert_after": "risk_grade",
				"read_only": 1,
				"description": "与信枠の現在ステータス",
			},
			{
				"fieldname": "anti_social_check_result",
				"fieldtype": "Data",
				"label": "反社チェック結果",
				"insert_after": "credit_status",
				"read_only": 1,
				"description": "最新の反社チェック結果",
			},
		],
		"Sales Order": [
			{
				"fieldname": "credit_check_section_break",
				"fieldtype": "Section Break",
				"label": "与信チェック",
				"insert_after": "terms",
				"collapsible": 1,
			},
			{
				"fieldname": "credit_check_passed",
				"fieldtype": "Check",
				"label": "与信チェック合格",
				"insert_after": "credit_check_section_break",
				"read_only": 1,
				"description": "Submit時の与信チェック結果",
			},
			{
				"fieldname": "credit_check_note",
				"fieldtype": "Small Text",
				"label": "与信チェック備考",
				"insert_after": "credit_check_passed",
				"read_only": 1,
			},
		],
	}
	create_custom_fields(custom_fields)
	frappe.logger().info("Business [Credit]: Created custom fields on Customer and Sales Order")


def _init_credit_settings():
	"""Initialize Credit Settings with default values."""
	settings = frappe.get_single("Credit Settings")
	if not settings.default_credit_period_days:
		settings.default_credit_period_days = 365
		settings.auto_block_on_exceed = 1
		settings.alert_threshold_pct = 80
		settings.review_cycle_months = 12
		settings.grade_a_min_score = 80
		settings.grade_b_min_score = 60
		settings.grade_c_min_score = 40
		settings.grade_d_min_score = 20
		settings.send_review_reminder_days = 30
		settings.save(ignore_permissions=True)
		frappe.logger().info("Business [Credit]: Initialized default settings")


# ===========================================================================
# Budget helpers
# ===========================================================================

def _create_budget_roles():
	"""Create Budget Manager role."""
	for role_name in ("Budget Manager",):
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
			}).insert(ignore_permissions=True)
			frappe.logger().info(f"Business [Budget]: Created role '{role_name}'")


def _init_budget_settings():
	"""Initialize Budget Settings with default values."""
	settings = frappe.get_single("Budget Settings")
	if not settings.fiscal_year_start_month:
		settings.fiscal_year_start_month = "4"
		settings.budget_currency = "JPY"
		settings.amount_rounding = "千円"
		settings.approval_workflow_enabled = 1
		settings.require_department_head_approval = 1
		settings.require_cfo_approval = 1
		settings.revision_approval_required = 1
		settings.max_revision_count = 3
		settings.variance_threshold_pct = 10
		settings.variance_action = "Warn"
		settings.check_budget_on_purchase_order = 1
		settings.forecast_enabled = 1
		settings.forecast_method = "Linear"
		settings.forecast_update_day = 5
		settings.save(ignore_permissions=True)
		frappe.logger().info("Business [Budget]: Initialized default settings")


# ===========================================================================
# Helpdesk helpers
# ===========================================================================

def _create_helpdesk_roles():
	"""Create Support Manager and Support Agent roles."""
	for role_name in ("Support Manager", "Support Agent"):
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
			}).insert(ignore_permissions=True)
			frappe.logger().info(f"Business [Helpdesk]: Created role '{role_name}'")


def _create_default_hd_categories():
	"""Create default ticket categories."""
	categories = [
		{"category_name": "IT", "description": "IT関連の問い合わせ", "is_external": 0},
		{"category_name": "HR", "description": "人事・労務の問い合わせ", "is_external": 0},
		{"category_name": "経理", "description": "経理・会計の問い合わせ", "is_external": 0},
		{"category_name": "顧客サポート", "description": "顧客からの問い合わせ", "is_external": 1},
	]
	for cat in categories:
		if not frappe.db.exists("HD Category", cat["category_name"]):
			frappe.get_doc({"doctype": "HD Category", **cat}).insert(ignore_permissions=True)
			frappe.logger().info(f"Business [Helpdesk]: Created category '{cat['category_name']}'")


def _create_default_sla_policy():
	"""Create default SLA policy."""
	if not frappe.db.exists("HD SLA Policy", "標準SLA"):
		frappe.get_doc({
			"doctype": "HD SLA Policy",
			"policy_name": "標準SLA",
			"is_default": 1,
			"enabled": 1,
			"low_response_time": 24,
			"low_resolution_time": 72,
			"medium_response_time": 8,
			"medium_resolution_time": 24,
			"high_response_time": 4,
			"high_resolution_time": 8,
			"urgent_response_time": 1,
			"urgent_resolution_time": 4,
			"business_hours_start": "09:00:00",
			"business_hours_end": "18:00:00",
		}).insert(ignore_permissions=True)
		frappe.logger().info("Business [Helpdesk]: Created default SLA policy")


# ===========================================================================
# DMS helpers
# ===========================================================================

def _create_dms_roles():
	"""Create DMS Manager and DMS User roles."""
	for role_name in ("DMS Manager", "DMS User"):
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
			}).insert(ignore_permissions=True)
			frappe.logger().info(f"Business [DMS]: Created role '{role_name}'")


def _create_default_retention_policies():
	"""Create default retention policies."""
	policies = [
		{
			"policy_name": "法定7年保存",
			"retention_years": 7,
			"description": "税法等で定められた7年間の保存義務",
			"action_on_expiry": "Notify",
			"enabled": 1,
		},
		{
			"policy_name": "法定10年保存",
			"retention_years": 10,
			"description": "会社法等で定められた10年間の保存義務",
			"action_on_expiry": "Notify",
			"enabled": 1,
		},
		{
			"policy_name": "永久保存",
			"retention_years": 0,
			"description": "永久に保存する文書（定款・登記等）",
			"action_on_expiry": "Notify",
			"enabled": 1,
		},
		{
			"policy_name": "3年保存",
			"retention_years": 3,
			"description": "3年間の保存後にアーカイブ",
			"action_on_expiry": "Archive",
			"enabled": 1,
		},
	]
	for policy in policies:
		if not frappe.db.exists("Retention Policy", policy["policy_name"]):
			frappe.get_doc({"doctype": "Retention Policy", **policy}).insert(
				ignore_permissions=True
			)
			frappe.logger().info(f"Business [DMS]: Created retention policy '{policy['policy_name']}'")
