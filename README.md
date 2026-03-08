# Lifegence Business

Business management modules for [Frappe](https://frappeframework.com/) / [ERPNext](https://erpnext.com/).

Provides contract approval, credit management, budgeting, helpdesk, and document management capabilities.

## Migrated Modules

> **Note**: The following modules have been extracted to dedicated apps:
> - **Compliance (コンプライアンス)** → [lifegence_governance](https://github.com/lifegence/lifegence-governance)
> - **Audit (内部監査)** → [lifegence_governance](https://github.com/lifegence/lifegence-governance)

## Modules

### Contract Approval (契約管理)
Contract lifecycle management with approval workflows.

### Credit Management (与信管理)
Customer credit limit management with automated checks on sales orders, invoice tracking, and expiry alerts.

### Budget Management (予算管理)
Budget planning and control with automatic availability checks on purchase orders and journal entries.

### Helpdesk (ヘルプデスク)
Internal support ticket management with category-based routing.

### DMS (文書管理)
Document management system with retention policies and e-signature support.

## Prerequisites

- Python 3.10+
- Frappe Framework v16+
- ERPNext v16+

## Installation

```bash
bench get-app https://github.com/lifegence/lifegence-business.git
bench --site your-site install-app lifegence_business
bench --site your-site migrate
```

## License

MIT - see [LICENSE](LICENSE)

## Contributing

Contributions are welcome. Please open an issue or pull request on [GitHub](https://github.com/lifegence/lifegence-business).
