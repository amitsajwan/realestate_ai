import { expect } from '@playwright/test';
import { test } from './fixtures/mcp';

const EMAIL = process.env.DEMO_EMAIL || 'demo@mumbai.com';
const PASSWORD = process.env.DEMO_PASSWORD || 'demo123';

async function login(page: any) {
  await page.goto('/');
  // If app redirects to login automatically, handle both cases
  if (await page.getByRole('button', { name: /login/i }).first().isVisible().catch(() => false)) {
    await page.getByRole('button', { name: /login/i }).first().click();
  }
  // Try common selectors
  await page.fill('#email, input[name="email"]', EMAIL);
  await page.fill('#password, input[name="password"]', PASSWORD);
  await page.getByRole('button', { name: /sign in|login/i }).first().click();
  await page.waitForURL('**/dashboard', { timeout: 30000 });
}

// Real system E2E: assumes BASE_URL points to a running instance and AUTH_TOKEN may be absent
// If AUTH_TOKEN is absent, we'll obtain it via /api/login and store in localStorage for UI

test.describe('Real app login + navigation (MCP-style)', () => {
  test('login, navigate, and verify key sections', async ({ page, mcp }) => {
    await mcp.hooks.beforeAuth?.();

    // Prefer obtaining token via /api/login for API calls
    let token: string | undefined = process.env.AUTH_TOKEN;
    if (!token) {
      const resp = await mcp.request.post('/api/login', {
        data: { email: EMAIL, password: PASSWORD },
      });
      expect(resp.ok()).toBeTruthy();
      const data = await resp.json();
      token = data.token;
    }

    await mcp.hooks.afterAuth?.(token);

    // Store token for the web app (localStorage approach)
    await page.addInitScript(([t]) => {
      if (t) localStorage.setItem('authToken', t);
    }, [token]);

    // Now do a UI login flow anyway (to catch regressions in UI auth)
    await login(page);

    // Navigate through sections with resilient selectors
    const sections = [
      { name: 'Dashboard', selector: 'a.nav-item:has-text("📊")' },
      { name: 'Leads', selector: 'a.nav-item:has-text("👥")' },
      { name: 'Smart Properties', selector: 'a.nav-item:has-text("🤖")' },
      { name: 'Settings', selector: 'a.nav-item:has-text("⚙️")' },
    ];

    let okCount = 0;
    for (const s of sections) {
      await mcp.hooks.beforeNavigate?.(s.name);
      let nav = page.locator(s.selector).first();
      // Fallbacks if emoji selector not present
      if (!(await nav.count()) || !(await nav.first().isVisible().catch(() => false))) {
        const alt1 = page.getByRole('link', { name: new RegExp(s.name, 'i') }).first();
        if (await alt1.count()) nav = alt1;
      }
      if (!(await nav.count()) || !(await nav.first().isVisible().catch(() => false))) {
        const alt2 = page.locator(`text=${s.name}`).first();
        if (await alt2.count()) nav = alt2;
      }
      await nav.waitFor({ state: 'visible', timeout: 15000 });
      await nav.click({ timeout: 15000 });
      await page.waitForTimeout(1000);
      okCount++;
    }

    // API sampling: use real profile endpoint with JWT if available; else validate OpenAPI
    if (token) {
      const prof = await mcp.request.get('/api/user/profile', {
        headers: { Authorization: `Bearer ${token}` },
      });
      expect(prof.ok()).toBeTruthy();
    } else {
      const openapi = await mcp.request.get('/openapi.json');
      expect(openapi.status()).toBe(200);
    }

    expect(okCount).toBeGreaterThanOrEqual(3);
  });
});
