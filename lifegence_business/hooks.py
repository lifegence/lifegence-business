app_name = "lifegence_business"
app_title = "Lifegence Business"
app_publisher = "Lifegence"
app_description = "Business apps for Lifegence Company OS (Contract, Credit, Budget, Helpdesk, DMS)"
app_email = "info@lifegence.co.jp"
app_license = "mit"

required_apps = ["frappe", "erpnext"]

export_python_type_annotations = True

# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------
after_install = "lifegence_business.install.after_install"
after_migrate = "lifegence_business.install.after_migrate"

# ---------------------------------------------------------------------------
# Apps screen entries (5 modules)
# ---------------------------------------------------------------------------
add_to_apps_screen = [
	{
		"name": "lifegence_contract_approval",
		"logo": "/assets/lifegence_business/images/contract-approval-logo.svg",
		"title": "契約管理",
		"route": "/app/contract-approval",
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
]

# ---------------------------------------------------------------------------
# DocType events (credit, budget)
# ---------------------------------------------------------------------------
doc_events = {
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
}

# ---------------------------------------------------------------------------
# Scheduled tasks (credit, budget)
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
	],
}

# ---------------------------------------------------------------------------
# Fixtures (credit, budget, helpdesk, dms)
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
