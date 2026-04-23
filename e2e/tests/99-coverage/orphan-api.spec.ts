import * as path from 'path';
import { createOrphanApiSpec } from '@lifegence/e2e-common';
import { KNOWN_UNCOVERED_APIS } from '../../fixtures/coverage-allowlist';

createOrphanApiSpec({
  allWhitelistFile: path.resolve(__dirname, '../../fixtures/all-whitelist-apis.json'),
  allowlist: KNOWN_UNCOVERED_APIS,
});
