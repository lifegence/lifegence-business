import { defineConfig, devices } from '@playwright/test';
import * as dotenv from 'dotenv';
import * as path from 'path';

const TEST_ENV = process.env.TEST_ENV || 'local';
dotenv.config({ path: path.join(__dirname, `.env.${TEST_ENV}`) });
dotenv.config({ path: path.join(__dirname, '.env') });

const BASE_URL_LOCAL = process.env.LOCAL_BASE_URL || 'http://dev.localhost:8000';
const BASE_URL_SAAS = process.env.SAAS_BASE_URL || 'https://admin.saas.lifegence.com';
const EVIDENCE = process.env.EVIDENCE === '1';

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [
    ['html', { outputFolder: 'reports/html', open: 'never' }],
    ['list'],
    ['junit', { outputFile: 'reports/junit.xml' }],
  ],
  use: {
    trace: EVIDENCE ? 'on' : 'retain-on-failure',
    video: EVIDENCE ? 'on' : 'retain-on-failure',
    screenshot: EVIDENCE ? 'on' : 'only-on-failure',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    ignoreHTTPSErrors: true,
  },
  projects: [
    { name: 'setup-local', testDir: './tests', testMatch: /.*\.setup\.ts$/, use: { baseURL: BASE_URL_LOCAL, ignoreHTTPSErrors: true } },
    { name: 'setup-saas', testDir: './tests', testMatch: /.*\.setup\.ts$/, use: { baseURL: BASE_URL_SAAS } },
    { name: 'chromium-local', use: { ...devices['Desktop Chrome'], baseURL: BASE_URL_LOCAL, storageState: '.auth/admin.local.json' }, dependencies: ['setup-local'] },
    { name: 'chromium-saas', use: { ...devices['Desktop Chrome'], baseURL: BASE_URL_SAAS, storageState: '.auth/admin.saas.json' }, dependencies: ['setup-saas'] },
  ],
});
