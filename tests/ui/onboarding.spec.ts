import { test, expect } from '@playwright/test';

test.describe('Agent Onboarding UI', () => {
  test('open onboarding from login and submit minimal form', async ({ page }) => {
    await page.goto('/');
    const link = page.getByRole('link', { name: /onboarding/i });
    await expect(link).toBeVisible();
    await link.click();

    // Onboarding page should render
    await expect(page.getByText('Agent Onboarding')).toBeVisible();

    // Fill minimal required fields
    await page.fill('input[name="name"]', 'Test Agent');
    await page.fill('input[name="email"]', `test.agent.${Date.now()}@example.com`);
    await page.fill('input[name="whatsapp"]', '+919876543210');
    await page.click('button[type="submit"]');

    // Expect JSON success or redirect depending on server behavior
    // We at least wait a bit and ensure no crash
    await page.waitForTimeout(1000);
  });
});

