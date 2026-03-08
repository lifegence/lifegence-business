# Lifegence Business

Business management modules for [Frappe](https://frappeframework.com/) / [ERPNext](https://erpnext.com/).

Provides contract approval, compliance, credit management, budgeting, helpdesk, document management, and internal audit capabilities.

## Modules

### Contract Approval (契約管理)
Contract lifecycle management with approval workflows.

### Compliance (コンプライアンス)
Compliance management with committee reporting and document tracking.

### Credit Management (与信管理)
Customer credit limit management with automated checks on sales orders, invoice tracking, and expiry alerts.

### Budget Management (予算管理)
Budget planning and control with automatic availability checks on purchase orders and journal entries.

### Helpdesk (ヘルプデスク)
Internal support ticket management with category-based routing.

### DMS (文書管理)
Document management system with retention policies and e-signature support.

### Audit (内部監査)
Internal audit management with checklists, risk assessment, corrective actions, and overdue tracking.

## Prerequisites

- Python 3.10+
- Frappe Framework v15+
- ERPNext v15+

## Installation

```bash
bench get-app https://github.com/lifegence/lifegence-business.git
bench --site your-site install-app lifegence_business
```

## After Installation

Run migrations to set up fixtures (roles, helpdesk categories, retention policies):

```bash
bench --site your-site migrate
```

## License

MIT - see [LICENSE](LICENSE)

## Contributing

Contributions are welcome. Please open an issue or pull request on [GitHub](https://github.com/lifegence/lifegence-business).
