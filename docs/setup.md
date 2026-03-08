# Lifegence Business -- Setup Guide

Business management modules for [Frappe](https://frappeframework.com/) / [ERPNext](https://erpnext.com/).

**License**: MIT -- see [LICENSE](../LICENSE)

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10 or later |
| Frappe Framework | v15 or later |
| ERPNext | v15 or later |
| MariaDB / MySQL | 10.6 or later |
| Node.js | 18 or later |

A working Frappe Bench environment is required. Refer to the [Frappe installation guide](https://frappeframework.com/docs/user/en/installation) if you do not have one.

---

## Installation

### 1. Download the app

```bash
bench get-app https://github.com/lifegence/lifegence-business.git
```

### 2. Install on your site

```bash
bench --site your-site install-app lifegence_business
```

### 3. Run migrations

```bash
bench --site your-site migrate
```

### 4. Build assets

```bash
bench build --app lifegence_business
```

---

## What `after_install` Creates

When the app is installed, the `after_install` hook automatically sets up six of the seven modules (Contract Approval requires no install-time setup). The following resources are created:

### Compliance

- **Roles**: Compliance Manager, Compliance User (created via `insert`, not fixtures)
- **Permissions**: Custom DocPerm entries for Committee Report, Classification Category, Report Chunk, Indexing Log, Compliance Settings
- **Classification Categories**: 39 categories across 3 layers (A: Incident Types, B: Organizational Mechanisms, C: Corporate Culture)

### Credit Management

- **Roles**: Credit Manager, Credit Approver
- **Custom fields** on existing ERPNext DocTypes:
  - **Customer**: risk_grade, credit_status, anti_social_check_result (in a collapsible "Credit Management" section)
  - **Sales Order**: credit_check_passed, credit_check_note (in a collapsible "Credit Check" section)
- **Default settings**: Credit period 365 days, auto-block on exceed, alert threshold 80%, review cycle 12 months, grade thresholds A(80)/B(60)/C(40)/D(20)

### Budget Management

- **Roles**: Budget Manager
- **Default settings**: Fiscal year start April, currency JPY, rounding to thousands, approval workflow enabled, variance threshold 10% (Warn), forecast enabled (Linear method)

### Helpdesk

- **Roles**: Support Manager, Support Agent
- **Default categories**: IT, HR, Accounting, Customer Support
- **Default SLA policy** ("Standard SLA"): Low 24h/72h, Medium 8h/24h, High 4h/8h, Urgent 1h/4h, business hours 09:00-18:00

### DMS (Document Management)

- **Roles**: DMS Manager, DMS User
- **Default retention policies**: 7-year statutory, 10-year statutory, Permanent, 3-year archive

### Audit

- **Roles**: Audit Manager, Auditor, Risk Manager
- **Default settings**: Risk matrix 5x5, review cycle 90 days, auto-reminder 7 days, daily overdue check

---

## What `after_migrate` Creates

Each time `bench migrate` runs, the following idempotent operations execute:

- Compliance roles and permissions are ensured
- 39 classification categories are seeded (skips existing)
- FULLTEXT index on `Report Chunk.content` is created if missing
- Compliance sidebar items are configured
- Audit roles are ensured

---

## Roles Summary

| Role | Module | Source |
|---|---|---|
| Compliance Manager | Compliance | `after_install` / `after_migrate` |
| Compliance User | Compliance | `after_install` / `after_migrate` |
| Credit Manager | Credit | Fixtures |
| Credit Approver | Credit | Fixtures |
| Budget Manager | Budget | Fixtures |
| Support Manager | Helpdesk | Fixtures |
| Support Agent | Helpdesk | Fixtures |
| DMS Manager | DMS | Fixtures |
| DMS User | DMS | Fixtures |
| Audit Manager | Audit | Fixtures + `after_migrate` |
| Auditor | Audit | Fixtures + `after_migrate` |
| Risk Manager | Audit | Fixtures + `after_migrate` |

---

## Post-Install Configuration

After installation, configure each module according to your requirements. Listed below is the recommended order.

### 1. Credit Management

Navigate to **Credit Settings** and review:

- Default credit period and alert threshold
- Grade score thresholds
- Auto-block behavior
- TDB/TSR API credentials (if using external credit data providers)

### 2. Budget Management

Navigate to **Budget Settings** and review:

- Fiscal year start month (default: April)
- Currency and rounding settings
- Approval workflow configuration
- Variance threshold and action
- Forecast method and schedule

### 3. Helpdesk

Review the pre-installed categories and SLA policy:

- **HD Category** list: Add or modify categories as needed
- **HD SLA Policy**: Adjust response and resolution times to match your service levels

### 4. DMS

Navigate to **DMS Settings** and configure:

- Version control and access logging toggles
- E-Book Preservation Law compliance setting
- Default retention period and maximum file size

### 5. Compliance (optional)

If using the Compliance module's RAG search capabilities, navigate to **Compliance Settings** and configure:

- Gemini API key and model
- Qdrant connection URL and collection name
- Chunking parameters (chunk size, overlap)
- Search weight defaults (vector vs. full-text)

### 6. Contract Approval (optional)

If using e-signature integration:

- Create an **E-Signature Provider Settings** record with your CloudSign or DocuSign credentials
- Set up **Contract Approval Rules** for automatic approval routing

### 7. Audit

Navigate to **Audit Settings** and review:

- J-SOX toggle (enable if required)
- Risk matrix size and review cycle
- Reminder and overdue check settings

---

## Optional External Dependencies

These services are not required for basic operation but enable additional features.

| Service | Module | Purpose | Configuration |
|---|---|---|---|
| Qdrant | Compliance | Vector database for RAG search | Compliance Settings |
| Google Gemini API | Compliance | Text embedding and AI classification | Compliance Settings |
| CloudSign | Contract Approval | Japanese e-signature service | E-Signature Provider Settings |
| DocuSign | Contract Approval | International e-signature service | E-Signature Provider Settings |
| TDB API | Credit | Tokyo Shoko Research credit data | Credit Settings |
| TSR API | Credit | Teikoku Databank credit data | Credit Settings |

---

## Updating

### Standard update

```bash
cd /path/to/frappe-bench
bench update --pull --apps lifegence_business
bench --site your-site migrate
bench build --app lifegence_business
```

### Update app only (without updating Frappe/ERPNext)

```bash
cd /path/to/frappe-bench/apps/lifegence_business
git pull
cd /path/to/frappe-bench
bench --site your-site migrate
bench build --app lifegence_business
```

---

## Uninstalling

```bash
bench --site your-site uninstall-app lifegence_business
bench remove-app lifegence_business
```

Note: Custom fields added to Customer and Sales Order by the Credit module are not automatically removed on uninstall. Remove them manually from **Customize Form** if needed.

---

## Related Documentation

- [Module Reference](modules.md) -- Detailed documentation for all 7 modules
- [Configuration Reference](configuration.md) -- Settings, roles, and external services
- [Troubleshooting](troubleshooting.md) -- Common issues and solutions
