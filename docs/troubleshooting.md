# Lifegence Business -- Troubleshooting Guide

Solutions for common issues encountered when using lifegence_business modules.

---

## Table of Contents

1. [Credit Check Blocking Sales Orders](#credit-check-blocking-sales-orders)
2. [Budget Check Errors on Purchase Orders](#budget-check-errors-on-purchase-orders)
3. [Compliance Indexing Failures](#compliance-indexing-failures)
4. [E-Signature Webhook Not Receiving](#e-signature-webhook-not-receiving)
5. [DMS File Size Limits](#dms-file-size-limits)
6. [Audit Overdue Notifications Not Sending](#audit-overdue-notifications-not-sending)
7. [General Troubleshooting](#general-troubleshooting)

---

## Credit Check Blocking Sales Orders

### Symptom

Sales Order submission fails with a credit-related error message, such as "Credit limit exceeded" or "Credit check failed."

### Possible Causes and Solutions

#### 1. Customer has no Credit Limit record

**Diagnosis**: Check if a Credit Limit record exists for the customer.

```bash
bench --site your-site console
```

```python
frappe.get_all("Credit Limit", filters={"customer": "CUST-0001"}, fields=["name", "credit_limit_amount", "used_amount", "available_amount"])
```

**Solution**: Create a Credit Limit record for the customer with an appropriate credit limit amount.

#### 2. Credit limit is genuinely exceeded

**Diagnosis**: Compare the order total with the available credit amount.

```python
# In bench console
from lifegence_business.credit.api.credit_status import get_credit_status
print(get_credit_status("CUST-0001"))
```

**Solution**: Either increase the credit limit via `update_credit_limit` API or reduce the order amount.

#### 3. Balance is stale after cancelled transactions

**Diagnosis**: The `used_amount` on the Credit Limit record does not match actual open receivables.

**Solution**: Trigger a balance recalculation by submitting and cancelling a zero-value Payment Entry, or run the recalculation service directly:

```python
from lifegence_business.credit.services.balance_calculator import recalculate_customer_balance
recalculate_customer_balance("CUST-0001", "Your Company Name")
```

#### 4. Auto-block is enabled when it should not be

**Diagnosis**: Check Credit Settings.

**Solution**: Navigate to **Credit Settings** and uncheck `auto_block_on_exceed`. With auto-block disabled, the system records the check result but does not block submission.

---

## Budget Check Errors on Purchase Orders

### Symptom

Purchase Order or Journal Entry submission fails with a budget availability error.

### Possible Causes and Solutions

#### 1. No approved Budget Plan exists

**Diagnosis**: Check for approved plans for the relevant fiscal year and cost center.

```python
frappe.get_all("Budget Plan", filters={"fiscal_year": "2025-2026", "status": "Approved", "docstatus": 1}, fields=["name", "cost_center", "total_annual_amount"])
```

**Solution**: Create and approve a Budget Plan that covers the cost center and accounts used in the Purchase Order.

#### 2. Budget is exhausted

**Diagnosis**: Use the budget vs actual API to check consumption.

```python
from lifegence_business.budget.api.budget_actual import get_budget_vs_actual
result = get_budget_vs_actual(company="Your Company", fiscal_year="2025-2026")
print(result)
```

**Solution**: Create a Budget Revision to increase the budget allocation, or adjust the Purchase Order amount.

#### 3. Variance action is set to "Stop" when "Warn" is more appropriate

**Diagnosis**: Check Budget Settings.

**Solution**: Navigate to **Budget Settings** and change `variance_action` from "Stop" to "Warn". This allows submission while still displaying a warning.

#### 4. Wrong cost center mapping

**Diagnosis**: The Purchase Order's cost center does not match any Budget Plan.

**Solution**: Verify that the cost center on the Purchase Order matches the cost center on the relevant approved Budget Plan.

---

## Compliance Indexing Failures

### Symptom

Calling `index_report` or `index_batch` fails or reports are not searchable after indexing.

### Qdrant Connection Issues

#### Symptom

Error messages containing "Connection refused", "ConnectionError", or "Qdrant" in the error log.

#### Diagnosis

```bash
# Check if Qdrant is running
curl -s http://localhost:6333/dashboard/ | head -5

# Check from bench console
bench --site your-site console
```

```python
settings = frappe.get_single("Compliance Settings")
print(f"URL: {settings.qdrant_url}")
print(f"Collection: {settings.qdrant_collection_name}")
```

#### Solutions

1. **Qdrant is not running**: Start the Qdrant service.

   ```bash
   # Docker
   docker start qdrant

   # Or start a new container
   docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
   ```

2. **Wrong URL in settings**: Update `qdrant_url` in Compliance Settings to the correct address and port.

3. **Qdrant Cloud authentication failure**: Verify the `qdrant_api_key` is correct and the cluster is active.

4. **Collection does not exist**: The collection is normally created automatically. If it was deleted, re-index a report to recreate it:

   ```python
   from lifegence_business.compliance.api.indexing import index_report
   index_report("REPORT-0001")
   ```

### Gemini API Issues

#### Symptom

Error messages containing "API key", "quota", "model not found", or "embedding" in the error log.

#### Diagnosis

```python
settings = frappe.get_single("Compliance Settings")
print(f"API Key set: {bool(settings.gemini_api_key)}")
print(f"Model: {settings.gemini_model}")
```

#### Solutions

1. **Invalid API key**: Go to [Google AI Studio](https://aistudio.google.com/) and regenerate the API key. Update it in Compliance Settings.

2. **Quota exceeded**: Check your Google Cloud billing dashboard. Free tier limits may be reached. Wait for the quota to reset or upgrade to a paid plan.

3. **Model not found**: Verify the model name in Compliance Settings. Use `text-embedding-004` for embeddings and `gemini-1.5-flash` for classification.

4. **Network connectivity**: Ensure the Frappe server can reach `generativelanguage.googleapis.com` on port 443.

### PDF Processing Issues

#### Symptom

The report is indexed but search returns no results, or indexing completes with zero chunks.

#### Solutions

1. **PDF has no extractable text** (scanned documents): The current implementation requires text-based PDFs. OCR processing is not built in. Use an external OCR tool to convert scanned documents before uploading.

2. **PDF is encrypted or password-protected**: Remove the password before uploading.

3. **Chunk size is too large**: If chunks are too large for the embedding model, reduce `chunk_size` in Compliance Settings (recommended: 500-1000 characters).

---

## E-Signature Webhook Not Receiving

### Symptom

E-signature request status does not update after signers take action in CloudSign or DocuSign.

### Possible Causes and Solutions

#### 1. Webhook URL not registered with the provider

**Diagnosis**: Check the provider's developer console for registered webhook endpoints.

**Solution**: Register the correct webhook URL:

```
https://your-site.example.com/api/method/lifegence_business.contract_approval.api.esignature.callback_signature_complete
```

#### 2. Webhook URL is not publicly accessible

**Diagnosis**: The webhook endpoint must be reachable from the internet. Local development environments (`localhost`) cannot receive webhooks.

**Solutions**:

- For production: Ensure the site is accessible via HTTPS on a public domain.
- For development: Use a tunneling service (e.g., ngrok) to expose your local environment:

  ```bash
  ngrok http 8000
  ```

  Then register the ngrok URL with the provider.

#### 3. SSL certificate issues

**Diagnosis**: Many webhook providers require a valid SSL certificate.

**Solution**: Ensure your site uses a valid SSL certificate (not self-signed for production). Check with:

```bash
curl -I https://your-site.example.com/api/method/lifegence_business.contract_approval.api.esignature.callback_signature_complete
```

#### 4. Firewall blocking incoming requests

**Diagnosis**: Check server firewall rules.

**Solution**: Allow inbound HTTPS traffic on port 443 from the provider's IP ranges. Consult the provider's documentation for their IP allowlist.

#### 5. Guest access not enabled

**Diagnosis**: The callback endpoint uses `@frappe.whitelist(allow_guest=True)`. If Frappe's guest access is restricted at the server level (e.g., nginx config), callbacks will be rejected.

**Solution**: Ensure the API endpoint path is not blocked by nginx or other reverse proxy rules. The endpoint must be accessible without authentication.

#### 6. Duplicate event suppression

**Diagnosis**: If the same `provider_event_id` is sent twice, the system silently ignores the duplicate.

**Solution**: This is expected behavior. Check the E-Signature Log for the event. If the initial event was processed but the request status was not updated, investigate the `_update_request_status` logic.

---

## DMS File Size Limits

### Symptom

Document upload fails with a file size error.

### Possible Causes and Solutions

#### 1. DMS Settings file size limit

**Diagnosis**: Check the configured maximum.

```python
settings = frappe.get_single("DMS Settings")
print(f"Max file size: {settings.max_file_size_mb} MB")
```

**Solution**: Increase `max_file_size_mb` in DMS Settings.

#### 2. Frappe framework file size limit

**Diagnosis**: Frappe has its own maximum file size setting.

**Solution**: In the Frappe **System Settings**, increase the `max_file_size` field (in MB).

#### 3. Nginx request body size limit

**Diagnosis**: Nginx returns a "413 Request Entity Too Large" error.

**Solution**: Edit your nginx configuration:

```nginx
# In your site's nginx config
client_max_body_size 100m;
```

Then restart nginx:

```bash
sudo systemctl restart nginx
```

#### 4. MariaDB packet size limit

**Diagnosis**: Very large files may exceed MariaDB's `max_allowed_packet` setting.

**Solution**: Edit `/etc/mysql/mariadb.conf.d/50-server.cnf`:

```ini
[mysqld]
max_allowed_packet = 256M
```

Then restart MariaDB:

```bash
sudo systemctl restart mariadb
```

---

## Audit Overdue Notifications Not Sending

### Symptom

Corrective actions past their due date do not generate notifications, and the audit dashboard does not show overdue items.

### Possible Causes and Solutions

#### 1. Scheduler is not running

**Diagnosis**: Check if the Frappe scheduler is active.

```bash
bench --site your-site scheduler status
```

**Solution**: Enable and start the scheduler:

```bash
bench --site your-site scheduler enable
bench --site your-site scheduler resume
```

#### 2. Scheduled tasks are not registered

**Diagnosis**: Verify the tasks are listed in the scheduler.

```bash
bench --site your-site show-pending-jobs
```

Look for entries from `lifegence_business.audit.services.corrective_action_service.check_overdue_actions` and `lifegence_business.audit.services.notification_service.send_due_reminders`.

**Solution**: Run `bench migrate` to ensure hooks are registered:

```bash
bench --site your-site migrate
```

#### 3. Overdue check frequency mismatch

**Diagnosis**: Check Audit Settings.

```python
settings = frappe.get_single("Audit Settings")
print(f"Overdue check frequency: {settings.overdue_check_frequency}")
print(f"Auto reminder days: {settings.auto_reminder_days}")
```

**Solution**: Ensure `overdue_check_frequency` is set to "Daily" and `auto_reminder_days` is greater than 0.

#### 4. Email is not configured

**Diagnosis**: Notifications require a working email setup in Frappe.

**Solution**: Configure an outgoing email account in **Email Account** settings. Verify with:

```bash
bench --site your-site send-test-email user@example.com
```

#### 5. Corrective actions have wrong status

**Diagnosis**: Only actions with status "Open" or "In Progress" that are past due are flagged.

```python
from frappe.utils import today
overdue = frappe.get_all("Corrective Action", filters={
    "status": ["in", ["Open", "In Progress"]],
    "due_date": ["<", today()],
}, fields=["name", "action_title", "due_date", "status"])
print(overdue)
```

**Solution**: Verify that the corrective actions have the correct status and due dates.

---

## General Troubleshooting

### Checking Error Logs

Frappe records errors in the **Error Log** DocType. Review recent errors:

```bash
bench --site your-site console
```

```python
errors = frappe.get_all("Error Log", filters={"seen": 0}, fields=["name", "method", "error"], order_by="creation desc", limit=10)
for e in errors:
    print(f"{e.name}: {e.method}")
    print(e.error[:200])
    print("---")
```

### Verifying Hooks Registration

Confirm that doc_events and scheduler_events are registered:

```bash
bench --site your-site console
```

```python
import lifegence_business.hooks as hooks
print("Doc events:", list(hooks.doc_events.keys()))
print("Daily tasks:", hooks.scheduler_events.get("daily", []))
print("Weekly tasks:", hooks.scheduler_events.get("weekly", []))
```

### Clearing Cache

If settings changes are not taking effect:

```bash
bench --site your-site clear-cache
bench --site your-site clear-website-cache
```

### Running Migrations

After updating the app, always run migrations:

```bash
bench --site your-site migrate
```

### Rebuilding Assets

If CSS changes (e.g., compliance.css) are not visible:

```bash
bench build --app lifegence_business
```

---

## Related Documentation

- [Setup Guide](setup.md) -- Installation and initial configuration
- [Module Reference](modules.md) -- Detailed module and API documentation
- [Configuration Reference](configuration.md) -- Settings, roles, and external services
