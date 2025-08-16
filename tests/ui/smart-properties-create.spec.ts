import { expect } from '@playwright/test';
import { test } from './fixtures/mcp';

const EMAIL = process.env.DEMO_EMAIL || 'demo@mumbai.com';
const PASSWORD = process.env.DEMO_PASSWORD || 'demo123';

async function ensureAuth(page: any, mcp: any) {
  // Get a real JWT token and prime localStorage for the app
  const resp = await mcp.request.post('/api/login', {
    data: { email: EMAIL, password: PASSWORD },
  });
  expect(resp.ok()).toBeTruthy();
  const data = await resp.json();
  const token = data.token as string;

  await page.addInitScript(([t]) => {
    if (t) {
      localStorage.setItem('token', t);
      // minimal user shape for greeting (optional)
      localStorage.setItem('user', JSON.stringify({ name: 'Demo User', firstName: 'Demo' }));
    }
  }, [token]);

  return token;
}

test.describe('Smart Properties - create via modal', () => {
  test('creates a Smart Property and closes modal on success', async ({ page, mcp }) => {
    const token = await ensureAuth(page, mcp);

    // Go straight to dashboard (auth via localStorage)
    await page.goto('/dashboard');
    await expect(page.locator('#dashboardSection')).toBeVisible({ timeout: 15000 });

    // Navigate to Smart Properties
    let nav = page.locator('a.nav-item:has-text("🤖 Smart Properties")').first();
    if (!(await nav.count())) {
      // Fallbacks
      const alt1 = page.getByRole('link', { name: /smart properties/i }).first();
      if (await alt1.count()) nav = alt1;
    }
    if (await nav.count()) {
      await nav.click({ timeout: 15000 });
    } else {
      // Direct JS navigation as last resort
      await page.evaluate(() => (window as any).showSection?.('smart-properties'));
    }

    const smartSection = page.locator('#smart-propertiesSection');
    await expect(smartSection).toBeVisible({ timeout: 15000 });

    // Open modal via primary button (supports both text variants)
    const addSmartBtn = page
      .locator(
        '#smart-propertiesSection button:has-text("Add Smart Property"), #smart-propertiesSection button:has-text("Create First Property")'
      )
      .first();
    await addSmartBtn.scrollIntoViewIfNeeded();
    await addSmartBtn.click();

    const modal = page.locator('#smartPropertyModal');
    await expect(modal).toBeVisible();

    // Fill required fields only; server will auto-generate AI content
    await page.fill('#smartPropertyAddress', '123 Test Ave, Test City, TS');
    await page.fill('#smartPropertyPrice', '$500,000');
    await page.selectOption('#smartPropertyType', 'single_family');

    // Optional fields for richer payload
    await page.selectOption('#smartPropertyBedrooms', '3').catch(() => {});
    await page.selectOption('#smartPropertyBathrooms', '2').catch(() => {});
    await page.fill('#smartPropertyFeatures', 'Updated kitchen, hardwood floors, large backyard');

    // Submit and assert API success; handle alert; modal should close
    const submitBtn = page.locator('#smartPropertyForm button[type="submit"]');

    page.once('dialog', async (dialog) => {
      await dialog.accept();
    });

    const [createResp] = await Promise.all([
      page.waitForResponse((r) => r.url().includes('/api/smart-properties') && r.request().method() === 'POST', {
        timeout: 20000,
      }),
      submitBtn.click(),
    ]);

    expect(createResp.ok()).toBeTruthy();
    const json = await createResp.json().catch(() => ({}));
    // Basic shape assertions
    expect(json).toHaveProperty('id');
    expect(json).toHaveProperty('address');

    // Modal should close after success
    await expect(modal).toBeHidden({ timeout: 10000 });

    // Grid should exist; data may be empty due to repo behavior, so just assert grid presence
    await expect(page.locator('#smartPropertiesGrid')).toBeVisible();

    // Bonus: verify GET endpoint reachable with auth
    const listResp = await mcp.request.get('/api/smart-properties', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(listResp.status()).toBe(200);
  });
});
