import { test, expect } from '@playwright/test';

test.describe('Business — Auth + landing (P0) @smoke', () => {
  test('authenticated session reaches /desk', async ({ page }) => {
    await page.goto('/desk');
    await expect(page).toHaveURL(/\/desk/);
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('Contract list loads', async ({ page }) => {
    await page.goto('/desk/contract');
    await expect(page).toHaveURL(/\/desk\/contract/);
  });

  test('Budget Plan list loads', async ({ page }) => {
    await page.goto('/desk/budget-plan');
    await expect(page).toHaveURL(/\/desk\/budget-plan/);
  });

  test('Managed Document list loads', async ({ page }) => {
    await page.goto('/desk/managed-document');
    await expect(page).toHaveURL(/\/desk\/managed-document/);
  });

  test('HD Ticket list loads', async ({ page }) => {
    await page.goto('/desk/hd-ticket');
    await expect(page).toHaveURL(/\/desk\/hd-ticket/);
  });
});
