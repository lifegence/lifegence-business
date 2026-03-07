app_name = "lifegence_business"
app_title = "Lifegence Business"
app_publisher = "Lifegence"
app_description = "Business apps for Lifegence Company OS (Contract, Compliance, Credit, Budget, Helpdesk, DMS, Audit)"
app_email = "masakazu@lifegence.co.jp"
app_license = "mit"

required_apps = ["frappe", "erpnext"]

export_python_type_annotations = True

# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------
after_install = "lifegence_business.install.after_install"
after_migrate = "lifegence_business.install.after_migrate"

# ---------------------------------------------------------------------------
# Includes in <head>
# ---------------------------------------------------------------------------
app_include_css = "/assets/lifegence_business/css/compliance.css"

# ---------------------------------------------------------------------------
# Apps screen entries (7 modules)
# ---------------------------------------------------------------------------
add_to_apps_screen = [
	{
		"name": "lifegence_contract_approval",
		"logo": "/assets/lifegence_business/images/contract-approval-logo.svg",
		"title": "契約管理",
		"route": "/app/contract-approval",
	},
	{
		"name": "lifegence_compliance",
		"logo": "/assets/lifegence_business/images/compliance-icon.svg",
		"title": "コンプライアンス",
		"route": "/app/compliance",
		"has_permission": "lifegence_business.compliance.api.has_compliance_access",
	},
	{
		"name": "lifegence_credit",
		"logo": "/assets/lifegence_business/images/credit-logo.svg",
		"title": "与信管理",
		"route": "/app/credit-management",
	},
	{
		"name": "lifegence_budget",
		"logo": "/assets/lifegence_business/images/budget-logo.svg",
		"title": "予算管理",
		"route": "/app/budget",
	},
	{
		"name": "lifegence_helpdesk",
		"logo": "/assets/lifegence_business/images/helpdesk-logo.svg",
		"title": "ヘルプデスク",
		"route": "/app/helpdesk",
	},
	{
		"name": "lifegence_dms",
		"logo": "/assets/lifegence_business/images/dms-logo.svg",
		"title": "文書管理",
		"route": "/app/dms",
	},
	{
		"name": "lifegence_audit",
		"logo": "/assets/lifegence_business/images/audit-logo.svg",
		"title": "内部監査",
		"route": "/app/audit",
	},
]

# ---------------------------------------------------------------------------
# DocType events (merged from compliance, credit, budget, audit)
# ---------------------------------------------------------------------------
doc_events = {
	# Compliance
	"Committee Report": {
		"on_trash": "lifegence_business.compliance.services.qdrant_service.on_report_delete",
	},
	# Credit
	"Sales Order": {
		"before_submit": "lifegence_business.credit.services.credit_check.check_credit_on_sales_order",
		"on_submit": "lifegence_business.credit.services.balance_calculator.recalculate_customer_balance_from_doc",
		"on_cancel": "lifegence_business.credit.services.balance_calculator.recalculate_customer_balance_from_doc",
	},
	"Sales Invoice": {
		"on_submit": "lifegence_business.credit.services.balance_calculator.recalculate_customer_balance_from_doc",
		"on_cancel": "lifegence_business.credit.services.balance_calculator.recalculate_customer_balance_from_doc",
	},
	"Payment Entry": {
		"on_submit": "lifegence_business.credit.services.balance_calculator.recalculate_customer_balance_from_doc",
		"on_cancel": "lifegence_business.credit.services.balance_calculator.recalculate_customer_balance_from_doc",
	},
	# Budget
	"Purchase Order": {
		"before_submit": "lifegence_business.budget.utils.check_budget_availability",
	},
	"Journal Entry": {
		"before_submit": "lifegence_business.budget.utils.check_budget_availability",
	},
	# Audit
	"Corrective Action": {
		"on_update": "lifegence_business.audit.services.corrective_action_service.on_corrective_action_update",
	},
	"Audit Checklist Item": {
		"on_update": "lifegence_business.audit.services.audit_service.on_checklist_item_update",
	},
}

# ---------------------------------------------------------------------------
# Scheduled tasks (merged from credit, budget, audit)
# ---------------------------------------------------------------------------
scheduler_events = {
	"daily": [
		# Credit alerts
		"lifegence_business.credit.services.alert_generator.check_credit_expiry",
		"lifegence_business.credit.services.alert_generator.check_review_due",
		"lifegence_business.credit.services.alert_generator.check_overdue_invoices",
		"lifegence_business.credit.services.alert_generator.check_anti_social_expiry",
		# Budget alerts
		"lifegence_business.budget.utils.check_budget_alerts",
		# Audit daily
		"lifegence_business.audit.services.corrective_action_service.check_overdue_actions",
		"lifegence_business.audit.services.notification_service.send_due_reminders",
	],
	"weekly": [
		# Audit weekly
		"lifegence_business.audit.services.risk_service.check_risk_review_dates",
	],
}

# ---------------------------------------------------------------------------
# Fixtures (merged from credit, budget, helpdesk, dms, audit)
# ---------------------------------------------------------------------------
fixtures = [
	{
		"dt": "Role",
		"filters": [
			[
				"name",
				"in",
				[
					# Credit
					"Credit Manager",
					"Credit Approver",
					# Budget
					"Budget Manager",
					# Helpdesk
					"Support Manager",
					"Support Agent",
					# DMS
					"DMS Manager",
					"DMS User",
					# Audit
					"Audit Manager",
					"Auditor",
					"Risk Manager",
				],
			]
		],
	},
	{
		"dt": "HD Category",
		"filters": [["category_name", "like", "%"]],
	},
	{
		"dt": "Retention Policy",
		"filters": [["policy_name", "like", "%"]],
	},
]
