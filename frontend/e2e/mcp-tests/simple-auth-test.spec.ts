import { test, expect } from '@playwright/test';

test.describe('Simple Authentication Test', () => {
  test('Login and access properties page', async ({ page }) => {
    console.log('🚀 Starting simple authentication test...');

    // Navigate to login page
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Fill login form with existing user (from previous test)
    await page.fill('input[name="email"]', 'finaluser1758460345073@propertyai.com');
    await page.fill('input[name="password"]', 'SecurePassword123!');

    // Submit login
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);

    console.log(`📍 After login: ${page.url()}`);

    // Navigate to properties page
    await page.goto('/properties');
    await page.waitForLoadState('networkidle');

    console.log(`📍 Properties page: ${page.url()}`);

    // Check if we can see the properties page content
    const propertiesTitle = page.locator('h1:has-text("Properties")');
    await expect(propertiesTitle).toBeVisible();

    console.log('✅ Successfully accessed properties page after login');
  });
});