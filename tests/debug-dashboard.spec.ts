import { test, expect } from '@playwright/test';

test('debug dashboard loading', async ({ page }) => {
    // Go to login page
    await page.goto('/');
    console.log('Current URL:', page.url());
    console.log('Page title:', await page.title());
    
    // Fill login form
    await page.fill('#email', 'demo@mumbai.com');
    await page.fill('#password', 'demo123');
    await page.click('button[type="submit"]');
    
    // Wait and check what happens
    await page.waitForTimeout(3000);
    console.log('After login URL:', page.url());
    console.log('After login title:', await page.title());
    
    // Check if we're on dashboard
    if (page.url().includes('/dashboard')) {
        console.log('Successfully on dashboard');
        await expect(page).toHaveTitle(/PropertyAI/);
    } else {
        console.log('Not on dashboard, current URL:', page.url());
        // Take screenshot for debugging
        await page.screenshot({ path: 'debug-dashboard.png' });
    }
});
