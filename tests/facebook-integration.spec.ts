import { test, expect } from '@playwright/test';

test.describe('Facebook Integration Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/');
    await page.fill('input[type="email"]', 'demo@mumbai.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    
    // Wait for dashboard
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
