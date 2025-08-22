import { test, expect } from '@playwright/test';

test.describe('Facebook Integration Tests', () => {
  test.beforeEach(async ({ page, context }) => {
    // Facebook OAuth login
    await page.goto('/');
    await page.click('button#facebook-login-btn');
    // Wait for Facebook OAuth popup and handle login
    const [popup] = await Promise.all([
      context.waitForEvent('page'),
      // The button click triggers the popup
    ]);
    // Simulate Facebook login in popup (replace selectors with actual Facebook login page selectors)
    await popup.waitForLoadState('domcontentloaded');
    // If Facebook login page appears, fill credentials
    if (await popup.locator('input[name="email"]').isVisible()) {
      await popup.fill('input[name="email"]', process.env.FB_TEST_EMAIL || 'your_fb_test_email');
      await popup.fill('input[name="pass"]', process.env.FB_TEST_PASSWORD || 'your_fb_test_password');
      await popup.click('button[name="login"]');
    }
    // Wait for redirect to dashboard
    await popup.waitForURL(/dashboard/);
    await popup.close();
    // Main page should now be authenticated
    await page.waitForURL('**/dashboard');
  });

  test('should load dashboard with Facebook integration', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/dashboard');
    
    // Verify dashboard loads
    await expect(page).toHaveTitle(/PropertyAI - Next-Gen AI Real Estate Dashboard/);
    await expect(page.locator('h1')).toContainText('PropertyAI');
    
    // Check for Facebook integration section
    await expect(page.locator('h5:has-text("Facebook Integration")')).toBeVisible();
  });

  test('should have Facebook API endpoints available', async ({ page }) => {
    // Test Facebook pages API endpoint
    const response = await page.request.get('/api/facebook/pages');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.pages).toBeDefined();
    expect(Array.isArray(data.pages)).toBe(true);
  });

  test('should be able to post to Facebook via API', async ({ page }) => {
    // Test Facebook posting API endpoint
    const response = await page.request.post('/api/facebook/post', {
      data: {
        page_id: '123456789',
        message: 'Test post from PropertyAI'
      }
    });
    
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.success).toBe(true);
  });
});
