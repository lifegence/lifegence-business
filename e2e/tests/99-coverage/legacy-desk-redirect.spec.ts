import { createLegacyRedirectSpec } from '@lifegence/e2e-common';

createLegacyRedirectSpec({
  paths: [
    { legacy: '/app/contract-approval', canonical: '/desk/contract-approval' },
    { legacy: '/app/budget', canonical: '/desk/budget' },
    { legacy: '/app/dms', canonical: '/desk/dms' },
    { legacy: '/app/helpdesk', canonical: '/desk/helpdesk' },
  ],
});
