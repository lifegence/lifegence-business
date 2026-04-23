# lifegence_crm E2E Tests

See `docs/e2e/lifegence-crm-e2e-guide.md` in the `company-os` repo for the
full operational guide. Quick commands:

```bash
make install   # npm ci + playwright browser
make seed      # bench --site dev.localhost execute lifegence_crm.scripts.seed_e2e.run
make test      # all tests against local
make coverage  # orphan detection only
make report    # open HTML report
```
