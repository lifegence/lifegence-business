import * as path from 'path';
import { createOrphanDocTypeSpec } from '@lifegence/e2e-common';
import { KNOWN_UI_HIDDEN_DOCTYPES } from '../../fixtures/coverage-allowlist';

createOrphanDocTypeSpec({
  modules: ['Contract Approval', 'Credit', 'Budget', 'Helpdesk', 'DMS'],
  appRoot: path.resolve(__dirname, '../../../lifegence_business'),
  entryPoints: [
    '/desk',
    '/desk/contract-approval',
    '/desk/budget',
    '/desk/dms',
    '/desk/credit-management',
    '/desk/helpdesk',
  ],
  allowlist: KNOWN_UI_HIDDEN_DOCTYPES,
});
