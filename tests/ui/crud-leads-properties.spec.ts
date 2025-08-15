import { test, expect } from '@playwright/test';

const DEMO_USER = {
  email: 'demo@mumbai.com',
  password: 'demo123'
};

async function login(page) {
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.fill('input[type=email]', DEMO_USER.email);
  await page.fill('input[type=password]', DEMO_USER.password);
  await page.click('button:has-text("Login to Dashboard")');
  await expect(page.getByText('Dashboard')).toBeVisible({ timeout: 10000 });
}

// Happy-path CRUD smoke checks for Leads & Properties

test.describe('CRUD smoke', () => {
  test('create lead and property via modals', async ({ page }) => {
    await login(page);

    // Add a Lead
    await test.step('Add Lead', async () => {
      await page.click('a:has-text("Leads")');
  await page.click('button:has-text("Add Lead")');
  await expect(page.locator('#addLeadModal')).toBeVisible();
  await page.fill('#addLeadModal input[name="name"]', 'QA Test Lead');
  await page.fill('#addLeadModal input[name="email"]', `qa.lead.${Date.now()}@example.com`);
  await page.fill('#addLeadModal input[name="phone"]', '555-0100');
  await page.click('#addLeadModal button:has-text("Add Lead")');
  await expect(page.locator('#addLeadModal')).toBeHidden();
      await expect(page.getByText('QA Test Lead')).toBeVisible({ timeout: 5000 });
    });

    // Add a Property
    await test.step('Add Property', async () => {
      await page.click('a:has-text("Properties")');
  await page.click('button:has-text("Add Property")');
  await expect(page.locator('#addPropertyModal')).toBeVisible();
  await page.fill('#addPropertyModal input[name="title"]', 'QA Test Property');
  await page.selectOption('#addPropertyModal select[name="property_type"]', 'Residential');
  await page.fill('#addPropertyModal input[name="location"]', '123 Test St');
  await page.fill('#addPropertyModal input[name="price"]', '₹4.5 Cr');
  await page.fill('#addPropertyModal textarea[name="description"]', 'Charming QA property.');
  await page.click('#addPropertyModal button:has-text("Add Property")');
  await expect(page.locator('#addPropertyModal')).toBeHidden();
  await expect(page.getByText('QA Test Property')).toBeVisible({ timeout: 5000 });
    });
  });
});
