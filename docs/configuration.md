# Lifegence Business -- Configuration Reference

Comprehensive reference for all settings, roles, and external service configuration.

---

## Table of Contents

1. [Credit Settings](#credit-settings)
2. [Budget Settings](#budget-settings)
3. [DMS Settings](#dms-settings)
4. [Compliance Settings](#compliance-settings)
5. [Audit Settings](#audit-settings)
6. [E-Signature Provider Settings](#e-signature-provider-settings)
7. [Role Assignments](#role-assignments)
8. [External Service Configuration](#external-service-configuration)

---

## Credit Settings

**Navigation**: Credit Management > Credit Settings

Single DocType that controls credit management behavior system-wide.

### General Settings

| Field | Type | Default | Description |
|---|---|---|---|
| default_credit_period_days | Int | 365 | Default validity period for new credit limits (days) |
| auto_block_on_exceed | Check | 1 | Block Sales Order submission when credit limit is exceeded |
| alert_threshold_pct | Int | 80 | Percentage of credit usage that triggers alerts |
| review_cycle_months | Int | 12 | Months between mandatory credit reviews |
| send_review_reminder_days | Int | 30 | Days before review due date to send reminders |

### Grade Score Thresholds

| Field | Type | Default | Description |
|---|---|---|---|
| grade_a_min_score | Int | 80 | Minimum risk score for Grade A |
| grade_b_min_score | Int | 60 | Minimum risk score for Grade B |
| grade_c_min_score | Int | 40 | Minimum risk score for Grade C |
| grade_d_min_score | Int | 20 | Minimum risk score for Grade D |

Scores below the Grade D threshold are assigned Grade E.

### External API (Optional)

| Field | Type | Description |
|---|---|---|
| tdb_api_url | Data | TDB (Teikoku Databank) API endpoint URL |
| tdb_api_key | Password | TDB API authentication key |
| tsr_api_url | Data | TSR (Tokyo Shoko Research) API endpoint URL |
| tsr_api_key | Password | TSR API authentication key |

---

## Budget Settings

**Navigation**: Budget > Budget Settings

Single DocType that controls budget planning, approval, and variance checking.

### Fiscal Year Settings

| Field | Type | Default | Description |
|---|---|---|---|
| fiscal_year_start_month | Select | 4 | Month the fiscal year begins (1-12) |
| budget_currency | Data | JPY | Default currency for budget amounts |
| amount_rounding | Select | 千円 | Display rounding (千円 = thousands, 百万円 = millions) |

### Approval Workflow

| Field | Type | Default | Description |
|---|---|---|---|
| approval_workflow_enabled | Check | 1 | Enable approval workflow for budget plans |
| require_department_head_approval | Check | 1 | Require department head approval |
| require_cfo_approval | Check | 1 | Require CFO approval |
| revision_approval_required | Check | 1 | Require approval for budget revisions |
| max_revision_count | Int | 3 | Maximum number of revisions per budget plan |

### Variance Checking

| Field | Type | Default | Description |
|---|---|---|---|
| variance_threshold_pct | Int | 10 | Budget variance percentage that triggers action |
| variance_action | Select | Warn | Action on threshold breach: Warn, Stop, or Ignore |
| check_budget_on_purchase_order | Check | 1 | Enable budget check on Purchase Order submit |

### Forecasting

| Field | Type | Default | Description |
|---|---|---|---|
| forecast_enabled | Check | 1 | Enable budget forecasting |
| forecast_method | Select | Linear | Default method: Linear, Average, Trend, Manual |
| forecast_update_day | Int | 5 | Day of month for automatic forecast updates |

---

## DMS Settings

**Navigation**: DMS > DMS Settings

Single DocType that controls document management behavior.

| Field | Type | Default | Description |
|---|---|---|---|
| enable_version_control | Check | 1 | Track document versions automatically |
| enable_access_logging | Check | 1 | Log document access events |
| e_book_preservation_enabled | Check | 0 | Enable E-Book Preservation Law compliance |
| default_retention_years | Int | 7 | Default retention period for new documents (years) |
| max_file_size_mb | Int | 50 | Maximum file upload size in megabytes |

---

## Compliance Settings

**Navigation**: Compliance > Compliance Settings

Single DocType that configures the AI classification and RAG search pipeline.

### Gemini API

| Field | Type | Description |
|---|---|---|
| gemini_api_key | Password | Google Gemini API key |
| gemini_model | Data | Gemini model name for embeddings (e.g., `text-embedding-004`) |
| classification_model | Data | Gemini model for text classification (e.g., `gemini-1.5-flash`) |

### Qdrant Connection

| Field | Type | Description |
|---|---|---|
| qdrant_url | Data | Qdrant server URL (e.g., `http://localhost:6333`) |
| qdrant_api_key | Password | Qdrant API key (if authentication is enabled) |
| qdrant_collection_name | Data | Collection name for storing vectors |

### Chunking Parameters

| Field | Type | Description |
|---|---|---|
| chunk_size | Int | Maximum number of characters per chunk |
| chunk_overlap | Int | Number of overlapping characters between consecutive chunks |

### Search Weights

| Field | Type | Description |
|---|---|---|
| default_vector_weight | Float | Default weight for vector similarity scores (0.0-1.0) |
| default_fulltext_weight | Float | Default weight for full-text search scores (0.0-1.0) |

---

## Audit Settings

**Navigation**: Audit > Audit Settings

Single DocType that configures internal audit behavior.

| Field | Type | Default | Description |
|---|---|---|---|
| jsox_enabled | Check | 0 | Enable J-SOX (Financial Instruments and Exchange Act) fields |
| risk_matrix_enabled | Check | 1 | Enable risk matrix functionality |
| risk_matrix_size | Select | 5x5 | Risk matrix dimensions (3x3, 4x4, or 5x5) |
| risk_review_cycle_days | Int | 90 | Days between mandatory risk reviews |
| auto_reminder_days | Int | 7 | Days before due date to send action reminders |
| overdue_check_frequency | Select | Daily | Frequency for overdue action checks |

---

## E-Signature Provider Settings

**Navigation**: Contract Approval > E-Signature Provider Settings

Standard DocType (multiple records allowed). Create one record per e-signature provider.

| Field | Type | Description |
|---|---|---|
| provider_name | Data | Display name for the provider |
| provider_type | Select | CloudSign or DocuSign |
| enabled | Check | Whether this provider is active |
| api_url | Data | Provider API base URL |
| api_key | Password | API authentication key |
| api_secret | Password | API secret or client secret |
| client_id | Data | OAuth client ID (DocuSign) |
| account_id | Data | Provider account ID |
| default_expiry_days | Int | Default signature request expiry (days) |
| webhook_secret | Password | Secret for webhook payload verification |
| sandbox_mode | Check | Use sandbox/test environment |

### Provider-Specific Notes

**CloudSign**:
- `api_url` typically `https://api.cloudsign.jp`
- `api_key` is the CloudSign client ID
- Webhook URL to register: `https://your-site/api/method/lifegence_business.contract_approval.api.esignature.callback_signature_complete`

**DocuSign**:
- `api_url` for production: `https://na1.docusign.net` (varies by region)
- `api_url` for sandbox: `https://demo.docusign.net`
- Requires `client_id` and `api_secret` for OAuth authentication
- `account_id` is the DocuSign account GUID

---

## Role Assignments

### How Roles Are Created

Roles are created through two mechanisms:

1. **Fixtures** (10 roles): Exported via `bench export-fixtures` and imported on install/migrate. These are defined in `hooks.py` under the `fixtures` key.

2. **Install script** (2 roles): Created programmatically by `after_install` and `after_migrate` in `install.py`.

### Role Permissions by Module

#### Contract Approval

No module-specific roles. Uses standard Frappe permissions on Contract and related DocTypes.

#### Compliance

| Role | Committee Report | Classification Category | Report Chunk | Indexing Log | Compliance Settings |
|---|---|---|---|---|---|
| Compliance Manager | CRUD + Export | CRUD | CRUD | CRUD | Read + Write |
| Compliance User | Read + Export | Read | Read | Read | Read |

#### Credit Management

| Role | Credit Limit | Credit Assessment | Credit Alert | Anti-Social Check | Credit Settings |
|---|---|---|---|---|---|
| Credit Manager | CRUD | CRUD | CRUD | CRUD | Read + Write |
| Credit Approver | Read + Write | Read | Read | Read | Read |

#### Budget Management

| Role | Budget Plan | Budget Revision | Budget Forecast | Budget Settings |
|---|---|---|---|---|
| Budget Manager | CRUD | CRUD | CRUD | Read + Write |

#### Helpdesk

| Role | HD Ticket | HD Category | HD SLA Policy | HD Knowledge Base |
|---|---|---|---|---|
| Support Manager | CRUD | CRUD | CRUD | CRUD |
| Support Agent | Read + Write | Read | Read | Read + Write |

#### DMS

| Role | Managed Document | Document Folder | Document Access Rule | DMS Settings |
|---|---|---|---|---|
| DMS Manager | CRUD | CRUD | CRUD | Read + Write |
| DMS User | Read + Write | Read | Read | Read |

#### Audit

| Role | Audit Plan | Audit Finding | Corrective Action | Risk Register | Audit Settings |
|---|---|---|---|---|---|
| Audit Manager | CRUD | CRUD | CRUD | CRUD | Read + Write |
| Auditor | Read + Write | CRUD | Read + Write | Read | Read |
| Risk Manager | Read | Read | Read | CRUD | Read |

### Assigning Roles to Users

1. Navigate to **User** list
2. Open the user record
3. Scroll to the **Roles** section
4. Add the desired roles from the table above
5. Save

Alternatively, use the bench command:

```bash
bench --site your-site add-user-role user@example.com "Credit Manager"
```

---

## External Service Configuration

### Qdrant (Compliance Module)

Qdrant is a vector database used for semantic similarity search in the Compliance module.

**Setup options**:

1. **Docker** (recommended for development):

```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

2. **Qdrant Cloud** (recommended for production):
   - Create an account at [cloud.qdrant.io](https://cloud.qdrant.io)
   - Create a cluster and obtain the URL and API key

**Configuration in Compliance Settings**:

| Setting | Example Value |
|---|---|
| qdrant_url | `http://localhost:6333` or `https://xxx.cloud.qdrant.io` |
| qdrant_api_key | (leave empty for local, required for cloud) |
| qdrant_collection_name | `compliance_reports` |

The collection is created automatically on first indexing operation if it does not exist.

### Google Gemini API (Compliance Module)

Gemini is used for text embedding (RAG search) and AI-powered classification.

**Setup**:

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create an API key
3. Enter the key in Compliance Settings

**Recommended models**:

| Purpose | Model | Notes |
|---|---|---|
| Embedding | `text-embedding-004` | 768-dimension vectors |
| Classification | `gemini-1.5-flash` | Cost-effective for classification tasks |

### CloudSign (Contract Approval Module)

Japanese e-signature service for domestic contract signing.

**Setup**:

1. Create a CloudSign enterprise account
2. Obtain API credentials from the developer console
3. Register the webhook URL in CloudSign settings
4. Create an E-Signature Provider Settings record with `provider_type = CloudSign`

**Webhook URL format**:

```
https://your-site.example.com/api/method/lifegence_business.contract_approval.api.esignature.callback_signature_complete
```

### DocuSign (Contract Approval Module)

International e-signature service.

**Setup**:

1. Create a DocuSign developer account at [developers.docusign.com](https://developers.docusign.com)
2. Create an integration (app) and obtain client ID and secret
3. Configure OAuth consent and redirect URIs
4. Create an E-Signature Provider Settings record with `provider_type = DocuSign`
5. Enable `sandbox_mode` for testing

### TDB / TSR APIs (Credit Module)

External credit data services for Japanese businesses.

**TDB (Teikoku Databank)**:
- Contact TDB for API access credentials
- Enter the API URL and key in Credit Settings

**TSR (Tokyo Shoko Research)**:
- Contact TSR for API access credentials
- Enter the API URL and key in Credit Settings

These APIs are called by the `run_anti_social_check` API and the credit assessment process. They are optional -- credit management works without them using manual data entry.

---

## Related Documentation

- [Setup Guide](setup.md) -- Installation and initial configuration
- [Module Reference](modules.md) -- Detailed module and API documentation
- [Troubleshooting](troubleshooting.md) -- Common issues and solutions
