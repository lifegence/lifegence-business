# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# ---------------------------------------------------------------------------
# Classification Categories (Compliance module) - 39 entries
# ---------------------------------------------------------------------------
CLASSIFICATION_CATEGORIES = [
	# Layer A: Incident Types (不正類型) - 14 categories
	{"category_code": "A01", "category_name": "会計不正・粉飾決算", "category_name_en": "Accounting Fraud", "layer": "A", "description": "財務諸表の虚偽記載、売上の水増し、費用の過少計上など"},
	{"category_code": "A02", "category_name": "横領・着服", "category_name_en": "Embezzlement", "layer": "A", "description": "会社資産の不正流用、横領、キックバックなど"},
	{"category_code": "A03", "category_name": "贈収賄", "category_name_en": "Bribery", "layer": "A", "description": "公務員への贈賄、民間での贈収賄、便宜供与など"},
	{"category_code": "A04", "category_name": "品質偽装", "category_name_en": "Quality Fraud", "layer": "A", "description": "製品品質データの改ざん、検査不正、性能偽装など"},
	{"category_code": "A05", "category_name": "データ改ざん", "category_name_en": "Data Falsification", "layer": "A", "description": "試験データ、検査記録、報告書の改ざん・捏造など"},
	{"category_code": "A06", "category_name": "情報漏洩", "category_name_en": "Information Leak", "layer": "A", "description": "個人情報漏洩、営業秘密の流出、機密情報の不正提供など"},
	{"category_code": "A07", "category_name": "ハラスメント", "category_name_en": "Harassment", "layer": "A", "description": "パワーハラスメント、セクシャルハラスメント、いじめなど"},
	{"category_code": "A08", "category_name": "独占禁止法違反", "category_name_en": "Antitrust Violation", "layer": "A", "description": "カルテル、入札談合、優越的地位の濫用など"},
	{"category_code": "A09", "category_name": "インサイダー取引", "category_name_en": "Insider Trading", "layer": "A", "description": "内部者取引、未公開重要情報の利用など"},
	{"category_code": "A10", "category_name": "利益相反", "category_name_en": "Conflict of Interest", "layer": "A", "description": "自己取引、関連当事者取引の不正、利益相反行為など"},
	{"category_code": "A11", "category_name": "環境違反", "category_name_en": "Environmental Violation", "layer": "A", "description": "環境基準違反、不法投棄、排出規制違反など"},
	{"category_code": "A12", "category_name": "労働法違反", "category_name_en": "Labor Violation", "layer": "A", "description": "不当労働行為、賃金未払い、過重労働など"},
	{"category_code": "A13", "category_name": "知的財産侵害", "category_name_en": "IP Infringement", "layer": "A", "description": "特許侵害、商標権侵害、著作権違反など"},
	{"category_code": "A14", "category_name": "その他", "category_name_en": "Other Incident", "layer": "A", "description": "上記に分類されないその他の不正行為"},
	# Layer B: Organizational Mechanisms (組織メカニズム) - 15 categories
	{"category_code": "B01", "category_name": "監査機能不全", "category_name_en": "Audit Dysfunction", "layer": "B", "description": "内部監査・外部監査の機能不全、監査の形骸化など"},
	{"category_code": "B02", "category_name": "内部通報制度の問題", "category_name_en": "Whistleblower Issues", "layer": "B", "description": "内部通報制度の未整備、通報者への不利益措置など"},
	{"category_code": "B03", "category_name": "取締役会の監督不足", "category_name_en": "Board Oversight Failure", "layer": "B", "description": "取締役会の監督機能不全、社外取締役の不足など"},
	{"category_code": "B04", "category_name": "リスク管理体制の不備", "category_name_en": "Risk Management Failure", "layer": "B", "description": "リスク管理体制の不備、リスクの見逃しなど"},
	{"category_code": "B05", "category_name": "内部統制の不備", "category_name_en": "Internal Control Failure", "layer": "B", "description": "内部統制の設計・運用の不備、承認プロセスの不備など"},
	{"category_code": "B06", "category_name": "コンプライアンス体制の不備", "category_name_en": "Compliance Framework Failure", "layer": "B", "description": "コンプライアンス体制の未整備、形骸化など"},
	{"category_code": "B07", "category_name": "情報開示の不備", "category_name_en": "Disclosure Failure", "layer": "B", "description": "適時開示の遅延、重要情報の非開示など"},
	{"category_code": "B08", "category_name": "人事評価制度の問題", "category_name_en": "HR Evaluation Issues", "layer": "B", "description": "不公正な人事評価、過度な業績圧力、報酬制度の問題など"},
	{"category_code": "B09", "category_name": "教育研修の不足", "category_name_en": "Training Inadequacy", "layer": "B", "description": "コンプライアンス教育の不足、倫理研修の形骸化など"},
	{"category_code": "B10", "category_name": "ITシステムの不備", "category_name_en": "IT System Failure", "layer": "B", "description": "IT統制の不備、システムセキュリティの脆弱性など"},
	{"category_code": "B11", "category_name": "子会社管理の不備", "category_name_en": "Subsidiary Management Failure", "layer": "B", "description": "子会社・関連会社のガバナンス不全、監視不足など"},
	{"category_code": "B12", "category_name": "外部委託管理の不備", "category_name_en": "Outsourcing Management Failure", "layer": "B", "description": "外部委託先の管理不足、委託先での不正の見逃しなど"},
	{"category_code": "B13", "category_name": "文書管理の不備", "category_name_en": "Document Management Failure", "layer": "B", "description": "文書管理体制の不備、記録の不備・改ざんなど"},
	{"category_code": "B14", "category_name": "権限管理の不備", "category_name_en": "Authority Management Failure", "layer": "B", "description": "権限の集中、職務分掌の不備、承認権限の不備など"},
	{"category_code": "B15", "category_name": "その他", "category_name_en": "Other Mechanism", "layer": "B", "description": "上記に分類されないその他の組織メカニズムの問題"},
	# Layer C: Corporate Culture (組織文化) - 10 categories
	{"category_code": "C01", "category_name": "同調圧力", "category_name_en": "Conformity Pressure", "layer": "C", "description": "組織内の同調圧力、異論を許さない雰囲気など"},
	{"category_code": "C02", "category_name": "権威勾配", "category_name_en": "Authority Gradient", "layer": "C", "description": "上下関係の厳格さ、上意下達の文化、物言えない雰囲気など"},
	{"category_code": "C03", "category_name": "業績至上主義", "category_name_en": "Results-over-Process", "layer": "C", "description": "過度な業績目標、数字至上主義、プロセス軽視など"},
	{"category_code": "C04", "category_name": "閉鎖的組織文化", "category_name_en": "Closed Culture", "layer": "C", "description": "外部との交流不足、閉鎖的な情報共有、排他的な文化など"},
	{"category_code": "C05", "category_name": "属人的経営", "category_name_en": "Personality-dependent Management", "layer": "C", "description": "特定個人への依存、ワンマン経営、属人的な業務運営など"},
	{"category_code": "C06", "category_name": "前例踏襲主義", "category_name_en": "Precedent-following", "layer": "C", "description": "前例踏襲の慣行、変化への抵抗、イノベーション阻害など"},
	{"category_code": "C07", "category_name": "縦割り組織", "category_name_en": "Silo Mentality", "layer": "C", "description": "部門間の壁、情報の縦割り、横断的連携の不足など"},
	{"category_code": "C08", "category_name": "不十分な倫理観", "category_name_en": "Insufficient Ethics", "layer": "C", "description": "倫理意識の低さ、コンプライアンス意識の不足など"},
	{"category_code": "C09", "category_name": "現場と経営の乖離", "category_name_en": "Management-field Gap", "layer": "C", "description": "経営層と現場の認識ギャップ、現場の声が届かない構造など"},
	{"category_code": "C10", "category_name": "その他", "category_name_en": "Other Culture", "layer": "C", "description": "上記に分類されないその他の組織文化の問題"},
]


# ===========================================================================
# Public entry points
# ===========================================================================

def after_install():
	"""Run after app installation -- sets up all 6 modules."""
	_install_compliance()
	_install_credit()
	_install_budget()
	_install_helpdesk()
	_install_dms()
	_install_audit()
	frappe.db.commit()
	print("Lifegence Business: Installation complete.")


def after_migrate():
	"""Run after bench migrate -- idempotent setup for compliance + audit."""
	# Compliance: roles, categories, fulltext index, sidebar
	_create_compliance_roles()
	_seed_classification_categories()
	_ensure_fulltext_index()
	_ensure_sidebar_items()
	# Audit: roles
	_create_audit_roles()
	frappe.db.commit()


# ===========================================================================
# Per-module install functions
# ===========================================================================

def _install_compliance():
	"""Compliance module: roles, permissions, classification categories."""
	_create_compliance_roles()
	_seed_classification_categories()
	print("Lifegence Business [Compliance]: Setup complete.")


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


def _install_audit():
	"""Audit module: roles, default settings."""
	_create_audit_roles()
	_init_audit_settings()


# ===========================================================================
# Compliance helpers
# ===========================================================================

def _create_compliance_roles():
	"""Create Compliance Manager and Compliance User roles."""
	roles = [
		{
			"role_name": "Compliance Manager",
			"desk_access": 1,
			"is_custom": 1,
		},
		{
			"role_name": "Compliance User",
			"desk_access": 1,
			"is_custom": 1,
		},
	]

	for role_data in roles:
		if not frappe.db.exists("Role", role_data["role_name"]):
			doc = frappe.get_doc({
				"doctype": "Role",
				**role_data,
			})
			doc.insert(ignore_permissions=True)
			print(f"Lifegence Business [Compliance]: Role '{role_data['role_name']}' created.")

	_add_compliance_permissions()
	frappe.db.commit()


def _add_compliance_permissions():
	"""Add permissions for Compliance roles to relevant DocTypes."""
	doctypes_permissions = {
		"Committee Report": {
			"Compliance Manager": {"read": 1, "write": 1, "create": 1, "delete": 1, "export": 1, "report": 1, "print": 1, "email": 1, "share": 1},
			"Compliance User": {"read": 1, "export": 1, "report": 1, "print": 1},
		},
		"Classification Category": {
			"Compliance Manager": {"read": 1, "write": 1, "create": 1, "delete": 1},
			"Compliance User": {"read": 1},
		},
		"Report Chunk": {
			"Compliance Manager": {"read": 1, "write": 1, "create": 1, "delete": 1},
			"Compliance User": {"read": 1},
		},
		"Indexing Log": {
			"Compliance Manager": {"read": 1, "write": 1, "create": 1, "delete": 1},
			"Compliance User": {"read": 1},
		},
		"Compliance Settings": {
			"Compliance Manager": {"read": 1, "write": 1, "create": 1},
			"Compliance User": {"read": 1},
		},
	}

	for doctype, roles in doctypes_permissions.items():
		if not frappe.db.exists("DocType", doctype):
			continue

		for role, perms in roles.items():
			existing = frappe.db.exists("Custom DocPerm", {
				"parent": doctype,
				"role": role,
			})
			if not existing:
				doc = frappe.get_doc({
					"doctype": "Custom DocPerm",
					"parent": doctype,
					"parenttype": "DocType",
					"parentfield": "permissions",
					"role": role,
					**perms,
				})
				doc.insert(ignore_permissions=True)
				print(f"Lifegence Business [Compliance]: Permission added for {role} on {doctype}")


def _seed_classification_categories():
	"""Create or update the 39 classification categories."""
	for cat in CLASSIFICATION_CATEGORIES:
		if not frappe.db.exists("Classification Category", cat["category_code"]):
			doc = frappe.get_doc({
				"doctype": "Classification Category",
				**cat,
			})
			doc.insert(ignore_permissions=True)

	frappe.db.commit()
	print(f"Lifegence Business [Compliance]: {len(CLASSIFICATION_CATEGORIES)} classification categories seeded.")


def _ensure_sidebar_items():
	"""Ensure Compliance sidebar has RAG Search page link."""
	if not frappe.db.exists("Workspace Sidebar", "Compliance"):
		return

	doc = frappe.get_doc("Workspace Sidebar", "Compliance")
	doc.app = "lifegence_business"

	has_rag = any(item.link_to == "compliance-dashboard" for item in doc.items)
	if not has_rag:
		doc.append("items", {
			"type": "Link",
			"label": "RAG Search",
			"link_to": "compliance-dashboard",
			"link_type": "Page",
			"child": 0,
		})
		items = list(doc.items)
		new_item = items.pop()
		items.insert(1, new_item)
		for i, item in enumerate(items):
			item.idx = i + 1
		doc.items = items
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		print("Lifegence Business [Compliance]: RAG Search added to sidebar")


def _ensure_fulltext_index():
	"""Create FULLTEXT index on Report Chunk content if not exists."""
	try:
		indexes = frappe.db.sql(
			"SHOW INDEX FROM `tabReport Chunk` WHERE Key_name = 'idx_content_fulltext'",
			as_dict=True,
		)
		if not indexes:
			frappe.db.sql(
				"ALTER TABLE `tabReport Chunk` ADD FULLTEXT INDEX `idx_content_fulltext` (`content`)"
			)
			frappe.db.commit()
			print("Lifegence Business [Compliance]: FULLTEXT index created on Report Chunk.content")
		else:
			print("Lifegence Business [Compliance]: FULLTEXT index already exists")
	except Exception as e:
		print(f"Lifegence Business [Compliance]: Could not create FULLTEXT index: {e}")


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


# ===========================================================================
# Audit helpers
# ===========================================================================

def _create_audit_roles():
	"""Create Audit Manager, Auditor, and Risk Manager roles."""
	for role_name in ("Audit Manager", "Auditor", "Risk Manager"):
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
			}).insert(ignore_permissions=True)


def _init_audit_settings():
	"""Initialize Audit Settings with default values."""
	settings = frappe.get_single("Audit Settings")
	if not settings.risk_review_cycle_days:
		settings.risk_matrix_enabled = 1
		settings.risk_matrix_size = "5x5"
		settings.risk_review_cycle_days = 90
		settings.auto_reminder_days = 7
		settings.overdue_check_frequency = "Daily"
		settings.save(ignore_permissions=True)
