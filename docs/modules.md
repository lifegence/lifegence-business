# Lifegence Business -- Module Reference

This document covers all 7 modules included in the lifegence_business app.

---

## Table of Contents

1. [Contract Approval](#contract-approval)
2. [Compliance](#compliance)
3. [Credit Management](#credit-management)
4. [Budget Management](#budget-management)
5. [Helpdesk](#helpdesk)
6. [DMS (Document Management)](#dms-document-management)
7. [Audit](#audit)

---

## Contract Approval

**Japanese name**: 契約管理

Contract lifecycle management with configurable approval workflows and e-signature integration.

### DocTypes (7)

| DocType | Purpose |
|---|---|
| Contract | Core contract record with lifecycle status tracking |
| Contract Template | Reusable contract templates |
| Contract Approval Rule | Rules for automatic approval routing by type/amount |
| Contract Approval Log | Audit trail for all approval actions |
| E-Signature Provider Settings | CloudSign/DocuSign provider configuration |
| E-Signature Request | Tracks signature requests and signer status |
| E-Signature Log | Event log for signature activities |

### Contract Lifecycle

```
Draft --> Pending Approval --> Approved --> Active --> Expired
                          \-> Rejected         \-> Terminated
```

### Contract Types

- 業務委託 (Service Agreement)
- 売買 (Sales/Purchase)
- 賃貸借 (Lease)
- NDA (Non-Disclosure Agreement)
- 雇用 (Employment)
- ライセンス (License)
- その他 (Other)

### Approval Routing

When a contract is submitted for approval, the system evaluates **Contract Approval Rule** records in order. Rules can match on:

- **Contract type** -- restrict to a specific type (or match all)
- **Amount range** -- `min_amount` / `max_amount` thresholds
- **Approver** -- a specific user or the first user holding a specified role

The first matching active rule determines the approver.

### E-Signature Integration

The e-signature subsystem supports CloudSign and DocuSign through the **E-Signature Provider Settings** DocType. The workflow is:

1. Create a provider settings record with API credentials and default expiry
2. Call `create_signature_request` with signer details
3. The system creates an E-Signature Request and sends it to the provider
4. Webhook callbacks update signer status via `callback_signature_complete`
5. When all signers have signed, the request status changes to "Completed"

**Webhook endpoint** (allow_guest):

```
POST /api/method/lifegence_business.contract_approval.api.esignature.callback_signature_complete
```

Expected JSON payload:

| Field | Required | Description |
|---|---|---|
| envelope_id | Yes | Provider's envelope/document ID |
| event_type | Yes | Sent, Viewed, Signed, Declined, Expired, Cancelled, Error |
| signer_email | No | Email of the signer |
| signer_name | No | Name of the signer |
| ip_address | No | Signer's IP address |
| certificate_data | No | Digital certificate data |
| provider_event_id | No | Provider's unique event ID (for deduplication) |

### API Reference

#### `submit_for_approval`

Submit a draft contract for approval.

```
POST /api/method/lifegence_business.contract_approval.api.approval.submit_for_approval
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| contract_name | string | Yes | Contract document name |

Returns: `{ success, approver }`

#### `approve_contract`

Approve a pending contract.

```
POST /api/method/lifegence_business.contract_approval.api.approval.approve_contract
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| contract_name | string | Yes | Contract document name |
| comments | string | No | Approval comments |

Returns: `{ success }`

#### `reject_contract`

Reject a pending contract.

```
POST /api/method/lifegence_business.contract_approval.api.approval.reject_contract
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| contract_name | string | Yes | Contract document name |
| comments | string | No | Rejection reason |

Returns: `{ success }`

#### `create_signature_request`

Create an e-signature request for an approved or active contract.

```
POST /api/method/lifegence_business.contract_approval.api.esignature.create_signature_request
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| contract_name | string | Yes | Contract document name |
| signers | JSON string | Yes | Array of `{name, email, order}` |
| provider_name | string | No | E-Signature Provider Settings name (defaults to first enabled) |
| expiry_days | int | No | Override default expiry days |

Returns: `{ success, signature_request, envelope_id, expiry_date }`

#### `check_signature_status`

Check the current status of an e-signature request.

```
POST /api/method/lifegence_business.contract_approval.api.esignature.check_signature_status
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| signature_request_name | string | No* | E-Signature Request document name |
| contract_name | string | No* | Contract name (finds latest request) |

*At least one parameter is required.

Returns: `{ success, found, signature_request, status, signers, logs }`

---

## Compliance

**Japanese name**: コンプライアンス

Third-party committee report analysis with AI-powered classification and RAG (Retrieval-Augmented Generation) search.

### DocTypes (6)

| DocType | Purpose |
|---|---|
| Committee Report | Third-party committee investigation reports |
| Classification Category | 39 pre-seeded categories in 3 layers |
| Report Classification | Child table linking reports to categories |
| Report Chunk | Text chunks extracted from reports for search |
| Indexing Log | Tracks PDF processing and indexing operations |
| Compliance Settings | Gemini API, Qdrant, and search configuration |

### Classification Taxonomy (39 Categories)

**Layer A -- Incident Types (不正類型)**: 14 categories

| Code | Category |
|---|---|
| A01 | 会計不正・粉飾決算 (Accounting Fraud) |
| A02 | 横領・着服 (Embezzlement) |
| A03 | 贈収賄 (Bribery) |
| A04 | 品質偽装 (Quality Fraud) |
| A05 | データ改ざん (Data Falsification) |
| A06 | 情報漏洩 (Information Leak) |
| A07 | ハラスメント (Harassment) |
| A08 | 独占禁止法違反 (Antitrust Violation) |
| A09 | インサイダー取引 (Insider Trading) |
| A10 | 利益相反 (Conflict of Interest) |
| A11 | 環境違反 (Environmental Violation) |
| A12 | 労働法違反 (Labor Violation) |
| A13 | 知的財産侵害 (IP Infringement) |
| A14 | その他 (Other Incident) |

**Layer B -- Organizational Mechanisms (組織メカニズム)**: 15 categories (B01-B15)

Covers audit dysfunction, whistleblower issues, board oversight, risk management, internal controls, compliance frameworks, disclosure, HR evaluation, training, IT systems, subsidiary management, outsourcing, document management, authority management, and other mechanisms.

**Layer C -- Corporate Culture (組織文化)**: 10 categories (C01-C10)

Covers conformity pressure, authority gradient, results-over-process culture, closed culture, personality-dependent management, precedent-following, silo mentality, insufficient ethics, management-field gap, and other culture issues.

### RAG Search Pipeline

1. **PDF Processing**: Reports are uploaded as Committee Report documents
2. **Extraction**: Text is extracted from attached PDF files
3. **Chunking**: Text is split into chunks with configurable size and overlap
4. **Embedding**: Chunks are embedded using Google Gemini API
5. **Storage**: Vectors are stored in Qdrant; chunks are saved as Report Chunk records
6. **Search**: Hybrid search combines vector similarity and MySQL FULLTEXT scoring

### Roles

| Role | Permissions |
|---|---|
| Compliance Manager | Full CRUD on all Compliance DocTypes |
| Compliance User | Read access to reports, categories, chunks, logs, settings |

### Dashboard

A custom page at `/app/compliance-dashboard` provides the RAG search interface.

### API Reference

#### Classification

**`get_taxonomy`** -- Get the full 3-layer classification taxonomy.

```
GET /api/method/lifegence_business.compliance.api.classification.get_taxonomy
```

**`get_stats`** -- Get classification statistics and category distribution.

```
GET /api/method/lifegence_business.compliance.api.classification.get_stats
```

**`analyze_text`** -- Classify arbitrary text using AI.

```
POST /api/method/lifegence_business.compliance.api.classification.analyze_text
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| text | string | Yes | Text to classify |

**`get_report_classification`** -- Get classification results for a specific report.

```
GET /api/method/lifegence_business.compliance.api.classification.get_report_classification
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| report_name | string | Yes | Committee Report document name |

#### Indexing

**`index_report`** -- Index a single report (extract, chunk, embed, store).

```
POST /api/method/lifegence_business.compliance.api.indexing.index_report
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| report_name | string | Yes | Committee Report document name |

**`index_batch`** -- Index a batch of pending reports.

```
POST /api/method/lifegence_business.compliance.api.indexing.index_batch
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| limit | int | No | Number of reports to process (default: 10) |

**`reindex_report`** -- Force reindex an already-indexed report.

```
POST /api/method/lifegence_business.compliance.api.indexing.reindex_report
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| report_name | string | Yes | Committee Report document name |

#### Search

**`hybrid_search`** -- Combined vector + full-text search.

```
POST /api/method/lifegence_business.compliance.api.search.hybrid_search
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| query | string | Yes | Search query text |
| limit | int | No | Maximum results |
| year | int | No | Filter by report year |
| company_name | string | No | Filter by company name |
| classification | string | No | Filter by classification category |
| vector_weight | float | No | Weight for vector scores |
| fulltext_weight | float | No | Weight for full-text scores |
| group_by_report | string | No | Group results by report ("0" to disable) |

**`vector_search`** -- Vector similarity search only.

```
POST /api/method/lifegence_business.compliance.api.search.vector_search
```

Parameters: Same as `hybrid_search` except no weight parameters.

**`fulltext_search`** -- MySQL FULLTEXT search only.

```
POST /api/method/lifegence_business.compliance.api.search.fulltext_search
```

Parameters: Same as `vector_search`.

**`find_similar`** -- Find reports similar to a given report.

```
POST /api/method/lifegence_business.compliance.api.search.find_similar
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| report_name | string | Yes | Committee Report document name |
| limit | int | No | Maximum results (default: 5) |

---

## Credit Management

**Japanese name**: 与信管理

Per-customer credit limit management with automated checks on Sales Order submission, risk scoring, and anti-social forces verification.

### DocTypes (6)

| DocType | Purpose |
|---|---|
| Credit Limit | Per-customer credit limit with usage tracking |
| Credit Assessment | Risk scoring with 5-factor evaluation |
| Credit Alert | Alerts for expiry, threshold, overdue invoices |
| Credit Limit History | Change history for credit limit amounts |
| Anti-Social Check | Anti-social forces verification records |
| Credit Settings | Default periods, thresholds, grade scores, API config |

### Credit Check on Sales Order

When a Sales Order is submitted, a `before_submit` hook automatically:

1. Looks up the customer's Credit Limit
2. Compares the order total against available credit
3. Blocks submission if `auto_block_on_exceed` is enabled and credit would be exceeded
4. Records check result in the `credit_check_passed` and `credit_check_note` custom fields

Customer balances are recalculated on submit/cancel of Sales Orders, Sales Invoices, and Payment Entries.

### Risk Scoring

Credit Assessments evaluate 5 factors (total: 100 points):

| Factor | Max Points |
|---|---|
| Financial health | 30 |
| Transaction history | 15 |
| Capital adequacy | 15 |
| Payment record | 25 |
| Transaction volume | 15 |

**Risk Grades**:

| Grade | Score Range |
|---|---|
| A | 80+ |
| B | 60-79 |
| C | 40-59 |
| D | 20-39 |
| E | Below 20 |

### Custom Fields on ERPNext DocTypes

**Customer**:

| Field | Type | Description |
|---|---|---|
| risk_grade | Data (read-only) | Current risk grade (A-E) |
| credit_status | Data (read-only) | Current credit status |
| anti_social_check_result | Data (read-only) | Latest anti-social check result |

**Sales Order**:

| Field | Type | Description |
|---|---|---|
| credit_check_passed | Check (read-only) | Whether credit check passed on submit |
| credit_check_note | Small Text (read-only) | Credit check details |

### Scheduled Tasks (Daily)

- Credit limit expiry check
- Review due date reminders
- Overdue invoice alerts
- Anti-social check expiry alerts

### API Reference

#### `get_credit_status`

Get credit status for a customer.

```
GET /api/method/lifegence_business.credit.api.credit_status.get_credit_status
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| customer | string | Yes | Customer document name |
| company | string | No | Company filter |

Returns: `{ success, credit_status: { credit_limit_amount, used_amount, available_amount, usage_percentage, risk_grade, anti_social_check, open_alerts } }`

#### `update_credit_limit`

Update credit limit amount with history recording.

```
POST /api/method/lifegence_business.credit.api.credit_limit.update_credit_limit
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| customer | string | Yes | Customer document name |
| new_amount | float | Yes | New credit limit amount |
| change_reason | string | Yes | Reason for change |
| company | string | No | Company (defaults to site default) |
| change_detail | string | No | Additional details |

Returns: `{ success, previous_amount, new_amount, history }`

#### `create_assessment`

Create a new credit assessment.

```
POST /api/method/lifegence_business.credit.api.assessment.create_assessment
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| customer | string | Yes | Customer document name |
| requested_amount | float | Yes | Requested credit amount |
| assessment_type | string | No | Default: "新規取引" |
| revenue | float | No | Customer revenue |
| profit | float | No | Customer profit |
| capital | float | No | Customer capital |
| years_in_business | int | No | Years in operation |

Returns: `{ success, assessment, risk_score, risk_grade, recommended_limit }`

#### `run_anti_social_check`

Create a new anti-social forces check record.

```
POST /api/method/lifegence_business.credit.api.anti_social.run_anti_social_check
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| customer | string | Yes | Customer document name |
| check_source | string | Yes | Data source (e.g., TDB, TSR) |
| result | string | Yes | Check result |
| result_detail | string | No | Detailed findings |

Returns: `{ success, check, result, valid_until }`

---

## Budget Management

**Japanese name**: 予算管理

Annual budget planning by department/cost center with monthly breakdown, variance checking, and year-end forecasting.

### DocTypes (7)

| DocType | Purpose |
|---|---|
| Budget Plan | Annual budget with monthly line items |
| Budget Plan Item | Child: per-account monthly amounts |
| Budget Revision | Revisions to approved budget plans |
| Budget Revision Item | Child: revised amounts per account |
| Budget Forecast | Year-end forecasting by period |
| Budget Forecast Item | Child: per-account forecast details |
| Budget Settings | Fiscal year, currency, approval, variance config |

### Budget Lifecycle

```
Draft --> Submitted --> Approved --> Revised (via Budget Revision)
                   \-> Rejected
```

### Variance Checking

On Purchase Order and Journal Entry submission, a `before_submit` hook checks budget availability:

- **Warn**: Displays a warning but allows submission
- **Stop**: Blocks submission if budget would be exceeded
- **Ignore**: No check is performed

The threshold is configurable as a percentage in Budget Settings.

### Forecasting Methods

| Method | Description |
|---|---|
| Linear | Linear projection based on actual spending to date |
| Average | Monthly average extrapolation |
| Trend | Trend-based projection using historical patterns |
| Manual | User-specified forecast amounts |

### Scheduled Tasks (Daily)

- Budget threshold alert notifications

### API Reference

#### `get_budget_vs_actual`

Get budget vs actual comparison data.

```
GET /api/method/lifegence_business.budget.api.budget_actual.get_budget_vs_actual
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| company | string | Yes | Company name |
| fiscal_year | string | Yes | Fiscal Year name |
| department | string | No | Filter by department |
| cost_center | string | No | Filter by cost center |
| budget_type | string | No | Filter by budget type |
| as_of_date | string | No | Cut-off date (default: today) |
| period | string | No | "Cumulative" (default) |

Returns: `{ success, data: { summary, by_department, by_account } }`

#### `submit_budget_plan`

Transition a Budget Plan through its workflow.

```
POST /api/method/lifegence_business.budget.api.budget_plan.submit_budget_plan
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| budget_plan | string | Yes | Budget Plan document name |
| action | string | Yes | "submit", "approve", or "reject" |
| comment | string | No* | Required when action is "reject" |

Returns: `{ success, data: { budget_plan, previous_status, new_status } }`

#### `create_revision`

Create a Budget Revision for an approved plan.

```
POST /api/method/lifegence_business.budget.api.budget_plan.create_revision
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| budget_plan | string | Yes | Budget Plan document name |
| reason | string | Yes | Reason for revision |
| revision_type | string | Yes | Type of revision |
| revised_items | JSON string | No | Array of revised line items |

Returns: `{ success, data: { revision, revision_number, total_change_amount } }`

#### `update_forecast`

Update or create a budget forecast.

```
POST /api/method/lifegence_business.budget.api.forecast.update_forecast
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| budget_forecast | string | No* | Existing forecast name |
| budget_plan | string | No* | Budget Plan (for new forecast) |
| forecast_month | string | No | Month for new forecast |
| method | string | No | Forecast method override |

*Either `budget_forecast` or `budget_plan` is required.

Returns: `{ success, data: { budget_forecast, approved_budget, actual_to_date, forecast_to_year_end, variance_from_budget } }`

### Script Report

**Budget vs Actual** -- Available under Reports, provides department-level and account-level budget comparison with consumption percentages.

---

## Helpdesk

**Japanese name**: ヘルプデスク

Internal and external support ticket management with SLA tracking and knowledge base.

### DocTypes (6)

| DocType | Purpose |
|---|---|
| HD Ticket | Support tickets with priority and SLA tracking |
| HD Ticket Comment | Child: comments/replies on tickets |
| HD Category | Ticket categories (IT, HR, Accounting, etc.) |
| HD SLA Policy | Response and resolution time targets by priority |
| HD SLA Timer | SLA timer state tracking |
| HD Knowledge Base | Searchable knowledge base articles |

### Ticket Workflow

```
Open --> In Progress --> Waiting for Customer --> Resolved --> Closed
```

### Pre-Installed Data

**Categories**:

| Category | Description | Type |
|---|---|---|
| IT | IT-related inquiries | Internal |
| HR | HR/labor inquiries | Internal |
| 経理 | Accounting inquiries | Internal |
| 顧客サポート | Customer inquiries | External |

**Default SLA Policy** ("標準SLA"):

| Priority | Response Time | Resolution Time |
|---|---|---|
| Low | 24 hours | 72 hours |
| Medium | 8 hours | 24 hours |
| High | 4 hours | 8 hours |
| Urgent | 1 hour | 4 hours |

Business hours: 09:00 - 18:00

### Knowledge Base

Articles support:

- Category-based organization
- Visibility control (internal only, external, both)
- Helpfulness tracking with vote counts
- Keyword search across title, content, and tags

### API Reference

#### `create_ticket`

Create a new helpdesk ticket.

```
POST /api/method/lifegence_business.helpdesk.api.ticket.create_ticket
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| subject | string | Yes | Ticket subject |
| description | string | Yes | Ticket description |
| category | string | No | HD Category name |
| priority | string | No | Low, Medium (default), High, Urgent |
| ticket_type | string | No | "社内" (default) or "外部" |
| raised_by_name | string | No | Reporter name (defaults to current user) |
| raised_by_email | string | No | Reporter email (defaults to current user) |

Returns: `{ success, ticket, status, assigned_to, sla_policy, response_due, resolution_due }`

#### `update_ticket_status`

Update ticket status.

```
POST /api/method/lifegence_business.helpdesk.api.ticket.update_ticket_status
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| ticket | string | Yes | HD Ticket document name |
| status | string | Yes | New status |
| resolution | string | No | Resolution description (for resolved/closed) |

#### `add_comment`

Add a comment to a ticket.

```
POST /api/method/lifegence_business.helpdesk.api.ticket.add_comment
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| ticket | string | Yes | HD Ticket document name |
| comment | string | Yes | Comment text |
| is_internal | int | No | 1 for internal-only comment (default: 0) |

#### `get_helpdesk_dashboard`

Get dashboard summary with ticket counts, SLA compliance, category and priority breakdowns.

```
GET /api/method/lifegence_business.helpdesk.api.dashboard.get_helpdesk_dashboard
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| company | string | No | Filter by company |

#### `search_knowledge_base`

Search knowledge base articles.

```
GET /api/method/lifegence_business.helpdesk.api.knowledge_base.search_knowledge_base
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| query | string | No | Search keywords |
| category | string | No | Filter by category |
| visibility | string | No | "外部公開" or "内部のみ" |

---

## DMS (Document Management)

**Japanese name**: 文書管理

Document management with version control, access logging, retention policies, and E-Book Preservation Law compliance.

### DocTypes (10)

| DocType | Purpose |
|---|---|
| Managed Document | Core document record with versioning |
| Document Version | Child: individual versions of a document |
| Document Folder | Hierarchical folder structure |
| Document Access Rule | Per-document access control rules |
| Document Access Log | Tracks who accessed which documents |
| Document Review | Document review workflow records |
| Document Template | Reusable document templates |
| Retention Policy | Configurable retention period rules |
| E-Book Preservation Log | Compliance logging for E-Book Preservation Law |
| DMS Settings | Version control, access logging, file size config |

### Pre-Installed Retention Policies

| Policy | Period | Action on Expiry |
|---|---|---|
| 法定7年保存 | 7 years | Notify |
| 法定10年保存 | 10 years | Notify |
| 永久保存 | Permanent (0) | Notify |
| 3年保存 | 3 years | Archive |

### Document Lifecycle

1. Upload a document (auto-generates content hash and version 1)
2. Create new versions as the document evolves
3. Optionally finalize to make the document immutable
4. Retention policy tracks when the document can be archived or deleted

### Folder Structure

Documents are organized in a hierarchical folder tree. Each folder can:

- Belong to a department
- Be marked as private
- Contain sub-folders and documents

### Access Control

Document Access Rules support:

| Rule Type | Description |
|---|---|
| User | Grant access to a specific user |
| Role | Grant access to all users with a role |
| Department | Grant access to all users in a department |

Access levels: Read, Write, Full Access

### API Reference

#### `upload_document`

Upload a new managed document.

```
POST /api/method/lifegence_business.dms.api.document.upload_document
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| document_name | string | Yes | Display name for the document |
| file | string | Yes | File URL or attachment |
| folder | string | No | Document Folder name |
| document_type | string | No | Default: "その他" |
| tags | string | No | Comma-separated tags |
| description | string | No | Document description |
| retention_policy | string | No | Retention Policy name |
| company | string | No | Company |

Returns: `{ success, document, status, current_version, content_hash, retention_until }`

#### `create_new_version`

Add a new version to an existing document.

```
POST /api/method/lifegence_business.dms.api.document.create_new_version
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| document | string | Yes | Managed Document name |
| file | string | Yes | New file URL |
| change_summary | string | No | Description of changes |

#### `finalize_document`

Finalize a document, making it immutable.

```
POST /api/method/lifegence_business.dms.api.document.finalize_document
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| document | string | Yes | Managed Document name |

#### `get_folder_tree`

Get the folder hierarchy.

```
GET /api/method/lifegence_business.dms.api.folder.get_folder_tree
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| parent_folder | string | No | Parent folder name (omit for root folders) |

Returns each folder with `child_count` and `document_count`.

#### `search_documents`

Search documents by keyword, folder, type, and tags.

```
GET /api/method/lifegence_business.dms.api.search.search_documents
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| query | string | No | Search keywords |
| folder | string | No | Filter by folder |
| document_type | string | No | Filter by document type |
| tags | string | No | Filter by tags |

---

## Audit

**Japanese name**: 内部監査

Internal audit management with audit plans, engagements, findings, corrective actions, risk register, and J-SOX support.

### DocTypes (10)

| DocType | Purpose |
|---|---|
| Audit Plan | Annual/periodic audit plans |
| Audit Engagement | Individual audit engagements under a plan |
| Audit Finding | Issues discovered during audits |
| Audit Checklist | Audit checklists with scoring |
| Audit Checklist Item | Child: individual checklist items |
| Corrective Action | Actions to address audit findings |
| Risk Register | Organizational risk catalog |
| Risk Assessment | Risk evaluations with likelihood x impact scoring |
| Control Activity | Internal control documentation and testing |
| Audit Settings | J-SOX, risk matrix, reminder configuration |

### Risk Matrix

The risk matrix uses a configurable grid (default 5x5) of likelihood and impact scores:

```
Impact
  5 |  5  10  15  20  25
  4 |  4   8  12  16  20
  3 |  3   6   9  12  15
  2 |  2   4   6   8  10
  1 |  1   2   3   4   5
    +--------------------
       1   2   3   4   5
                Likelihood
```

Risk levels are derived from the score:

| Score Range | Risk Level |
|---|---|
| 1-4 | Low |
| 5-9 | Medium |
| 10-15 | High |
| 16-25 | Critical |

### Risk Categories

- 戦略 (Strategic)
- 財務 (Financial)
- 業務 (Operational)
- コンプライアンス (Compliance)
- IT (Information Technology)
- 災害 (Disaster)
- レピュテーション (Reputation)
- その他 (Other)

### J-SOX Support

When enabled in Audit Settings, audit-related DocTypes include additional fields for:

- Financial statement assertions
- Process categories
- Control effectiveness ratings

### Doc Events

| Event | Behavior |
|---|---|
| Corrective Action `on_update` | Cascades status changes to the linked Audit Finding |
| Audit Checklist Item `on_update` | Recalculates the parent checklist summary scores |

### Scheduled Tasks

**Daily**:
- Check for overdue corrective actions
- Send due date reminders

**Weekly**:
- Check risk register review dates

### API Reference

#### `get_audit_dashboard`

Get comprehensive audit dashboard data.

```
GET /api/method/lifegence_business.audit.api.audit.get_audit_dashboard
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| fiscal_year | string | No | Filter by fiscal year |

Returns: `{ success, data: { plan_summary, findings_summary, corrective_actions_summary, risk_summary } }`

#### `create_finding`

Create a new audit finding.

```
POST /api/method/lifegence_business.audit.api.finding.create_finding
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| audit_engagement | string | Yes | Audit Engagement name |
| finding_title | string | Yes | Title of the finding |
| severity | string | Yes | Severity level |
| category | string | Yes | Finding category |
| description | string | Yes | Detailed description |
| recommendation | string | Yes | Recommended action |

#### `create_corrective_action`

Create a corrective action for a finding.

```
POST /api/method/lifegence_business.audit.api.corrective_action.create_corrective_action
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| audit_finding | string | Yes | Audit Finding name |
| action_title | string | Yes | Action title |
| action_description | string | Yes | Description of the action |
| responsible_person | string | Yes | User responsible for execution |
| due_date | string | Yes | Due date (YYYY-MM-DD) |
| priority | string | No | Default: "Normal" |

#### `get_risk_matrix`

Get risk matrix heatmap data.

```
GET /api/method/lifegence_business.audit.api.risk.get_risk_matrix
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| department | string | No | Filter by department |
| risk_category | string | No | Filter by risk category |
| jsox_only | bool | No | Show only J-SOX related risks |

#### `get_risk_trend`

Get risk score trend data for a specific risk.

```
GET /api/method/lifegence_business.audit.api.risk.get_risk_trend
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| risk_register | string | Yes | Risk Register document name |
| period | string | No | Time period filter |

Returns: `{ success, data: { risk_register, assessments, total_assessments } }`

---

## ERPNext Dependencies

The following ERPNext DocTypes are referenced across modules:

| ERPNext DocType | Used By |
|---|---|
| Customer | Credit Management (custom fields added) |
| Sales Order | Credit Management (custom fields added, doc events) |
| Sales Invoice | Credit Management (doc events) |
| Payment Entry | Credit Management (doc events) |
| Purchase Order | Budget Management (doc events) |
| Journal Entry | Budget Management (doc events) |
| GL Entry | Budget Management (actual amount queries) |
| Fiscal Year | Budget Management |
| Company | Budget, Credit, Helpdesk, DMS |
| Department | Budget Management |
| Cost Center | Budget Management |
| Account | Budget Management |
