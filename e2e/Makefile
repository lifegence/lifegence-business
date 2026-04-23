SHELL          := bash
.SHELLFLAGS    := -eu -o pipefail -c

BENCH_ROOT     := $(realpath ../../..)
APP_ROOT       := $(realpath ..)
SITE           := dev.localhost
BASE_URL_LOCAL := http://dev.localhost:8000
TEST_ENV       ?= local

.PHONY: all install ensure-bench seed extract test coverage evidence report clean help

help:
	@echo "Targets: install | ensure-bench | seed | extract | test | coverage | evidence | report | clean | all"

install:
	npm ci --install-links
	npx playwright install --with-deps chromium

ensure-bench:
	@if curl -sf -o /dev/null -m 3 $(BASE_URL_LOCAL)/api/method/ping; then \
		echo "✓ bench reachable"; \
	else \
		echo "⚠ bench not reachable — starting"; \
		cd $(BENCH_ROOT) && nohup bench start > /tmp/bench-e2e.log 2>&1 & \
		for i in $$(seq 1 30); do \
			sleep 2; \
			if curl -sf -o /dev/null $(BASE_URL_LOCAL)/api/method/ping; then break; fi; \
		done; \
		curl -sf -o /dev/null $(BASE_URL_LOCAL)/api/method/ping \
			|| { echo "✗ bench failed to start"; exit 1; }; \
	fi

seed: ensure-bench
	cd $(BENCH_ROOT) && bench --site $(SITE) execute lifegence_business.scripts.seed_e2e.run

extract:
	python3 $(APP_ROOT)/lifegence_business/scripts/extract_whitelist_apis.py

test: ensure-bench
	TEST_ENV=$(TEST_ENV) npx playwright test --project=chromium-$(TEST_ENV)

coverage: ensure-bench extract
	TEST_ENV=$(TEST_ENV) npx playwright test --project=chromium-$(TEST_ENV) tests/99-coverage

evidence: ensure-bench seed extract
	@rm -rf reports/evidence
	@mkdir -p reports/evidence
	EVIDENCE=1 TEST_ENV=$(TEST_ENV) npx playwright test --project=chromium-$(TEST_ENV) || true

report:
	npx playwright show-report reports/html

clean:
	rm -rf coverage-output reports test-results .auth

all: ensure-bench seed extract test
	@echo "✓ E2E run complete"
