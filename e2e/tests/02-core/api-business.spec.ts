import { test, expect, FrappeClient } from '@lifegence/e2e-common';

test.describe('Business — DocType lists across modules (P1)', () => {
  let client: FrappeClient;

  test.beforeAll(async ({ baseURL }) => {
    client = await FrappeClient.login(
      baseURL!,
      process.env.ADMIN_USR || 'Administrator',
      process.env.ADMIN_PWD || 'admin',
    );
  });
  test.afterAll(async () => await client.dispose());

  for (const entity of [
    // Contract Approval
    'Contract',
    'Contract Template',
    'Contract Approval Rule',
    // Budget
    'Budget Plan',
    'Budget Revision',
    'Budget Forecast',
    // DMS
    'Managed Document',
    'Document Folder',
    'Retention Policy',
    // Credit Management
    'Credit Assessment',
    'Credit Limit',
    'Anti-Social Check',
    // Helpdesk
    'HD Ticket',
    'HD Category',
    'HD Knowledge Base',
  ]) {
    test(`${entity} list is accessible`, async () => {
      const list = await client.getList<{ name: string }>(entity, {
        fields: ['name'], limit_page_length: 5,
      });
      expect(Array.isArray(list)).toBe(true);
    });
  }

  for (const single of ['DMS Settings', 'Budget Settings', 'Credit Settings']) {
    test(`${single} single loads`, async () => {
      const doc = await client.call<{ name: string }>('frappe.client.get', {
        doctype: single, name: single,
      });
      expect(doc.name).toBe(single);
    });
  }
});
