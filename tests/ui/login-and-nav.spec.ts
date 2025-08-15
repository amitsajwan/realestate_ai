import { test, expect } from '@playwright/test';

const DEMO_USER = {
  email: 'demo@mumbai.com',
  password: 'demo123'
};

// Small helper to ensure server is up before doing assertions
async function waitForServer(page) {
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  // If redirected to login, the page will contain a login form
  await expect(page.locator('text=Login')).toBeVisible({ timeout: 10000 });
}

// Contract
// - Visits login, logs in with demo user (pre-seeded by server), lands on dashboard
// - Navigates to Leads, Properties, Settings sections
// - Opens and closes Add Lead / Add Property modals

test.describe('Login and basic navigation', () => {
  test('login works and nav sections switch', async ({ page }) => {
    await waitForServer(page);

    await page.fill('input[type=email]', DEMO_USER.email);
    await page.fill('input[type=password]', DEMO_USER.password);
    await page.click('button:has-text("Login to Dashboard")');

    // Expect dashboard to show after login
    await expect(page.getByText('Dashboard')).toBeVisible({ timeout: 10000 });

    // Switch sections via nav (calls showSection)
  await page.click('a:has-text("Leads")');
    await expect(page.getByText('Leads')).toBeVisible();

  await page.click('a:has-text("Properties")');
    await expect(page.getByText('Properties')).toBeVisible();

  await page.click('a:has-text("Settings")');
    await expect(page.getByText('Settings')).toBeVisible();
  });

  test('can open/close Add Lead and Add Property modals', async ({ page }) => {
    // Login first
    await waitForServer(page);
  await page.fill('input[type=email]', DEMO_USER.email);
  await page.fill('input[type=password]', DEMO_USER.password);
  await page.click('button:has-text("Login to Dashboard")');

    // Leads modal
  await page.click('button:has-text("Add Lead")');
  await expect(page.locator('#addLeadModal')).toBeVisible();
  await page.click('#addLeadModal .close');
  await expect(page.locator('#addLeadModal')).toBeHidden();

    // Properties modal
    await page.click('a:has-text("Properties")');
  await page.click('button:has-text("Add Property")');
  await expect(page.locator('#addPropertyModal')).toBeVisible();
  await page.click('#addPropertyModal .close');
  await expect(page.locator('#addPropertyModal')).toBeHidden();
  });
});
