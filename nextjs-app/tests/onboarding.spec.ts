import { test, expect } from '@playwright/test';

test.describe('Onboarding Flow', () => {
  test('should progress through onboarding steps', async ({ page }) => {
    await page.goto('/onboarding');

    // Step 1: Personal Information
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.click('button:has-text("Next")');

    // Step 2: Company Details
    await page.fill('input[name="company"]', 'Real Estate Pro');
    await page.fill('input[name="position"]', 'Senior Agent');
    await page.click('button:has-text("Next")');

    // Step 3: Preferences
    await page.selectOption('select[name="aiStyle"]', 'Professional');
    await page.selectOption('select[name="aiTone"]', 'Friendly');
    await page.click('button:has-text("Next")');

    // Step 5: Review & Submit
    await page.check('input[name="termsAccepted"]');
    await page.check('input[name="privacyAccepted"]');
    await page.click('button:has-text("Complete")');

    // Verify completion
    await expect(page).toHaveURL('/dashboard');
  });
});