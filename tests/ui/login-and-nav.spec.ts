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

  // Expect dashboard to show after login (prefer unique heading)
  await expect(page.locator('h1:has-text("Dashboard")')).toBeVisible({ timeout: 10000 });

    // Switch sections via nav (calls showSection)
  await page.click('a.nav-item:has-text("👥 Leads")');
  await expect(page.locator('#leadsSection')).toBeVisible();

  await page.click('a.nav-item:has-text("🤖 Smart Properties")');
  await expect(page.locator('#smart-propertiesSection')).toBeVisible();

  await page.click('a.nav-item:has-text("⚙️ Settings")');
  await expect(page.locator('#settingsSection')).toBeVisible();
  });

  test('can open/close Add Lead and Add Property modals', async ({ page }) => {
    // Login first
    await waitForServer(page);
  await page.fill('input[type=email]', DEMO_USER.email);
  await page.fill('input[type=password]', DEMO_USER.password);
  await page.click('button:has-text("Login to Dashboard")');

  // Leads modal (button text can be "Add Lead" or "Add New Lead")
  await page.click('a.nav-item:has-text("👥 Leads")');
  await expect(page.locator('#leadsSection')).toBeVisible();
  const addLeadBtn = page.locator('#leadsSection button:has-text("Add New Lead"), #leadsSection button:has-text("Add Lead")').first();
  await addLeadBtn.waitFor({ state: 'visible', timeout: 10000 });
  await addLeadBtn.scrollIntoViewIfNeeded();
  await addLeadBtn.click();
  await expect(page.locator('#addLeadModal')).toBeVisible();
  await page.click('#addLeadModal .close');
  await expect(page.locator('#addLeadModal')).toBeHidden();

  // Smart Property modal (new flow)
  await page.click('a.nav-item:has-text("🤖 Smart Properties")');
  await expect(page.locator('#smart-propertiesSection')).toBeVisible();
  const addSmartBtn = page.locator('#smart-propertiesSection button:has-text("Add Smart Property"), #smart-propertiesSection button:has-text("Create First Property")').first();
  await addSmartBtn.waitFor({ state: 'visible', timeout: 10000 });
  await addSmartBtn.click();
  await expect(page.locator('#smartPropertyModal')).toBeVisible();
  await page.click('#smartPropertyModal .close');
  await expect(page.locator('#smartPropertyModal')).toBeHidden();
  });
});
