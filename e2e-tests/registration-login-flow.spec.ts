import { test, expect } from '@playwright/test';

test.describe('Registration and Login Flow', () => {
  test('should register a user and then login successfully', async ({ page }) => {
    // Step 1: Navigate to login page
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Step 2: Switch to registration mode
    await page.waitForSelector('button:has-text("Sign up")', { timeout: 5000 });
    await page.click('button:has-text("Sign up")');
    await page.waitForTimeout(1000);
    
    // Step 3: Wait for registration form
    await page.waitForSelector('input[name="firstName"]', { timeout: 10000 });
    
    // Step 4: Fill registration form with unique email
    const uniqueEmail = `testuser${Date.now()}@example.com`;
    const testPassword = 'Jd9!Qm7#VzA2';
    
    console.log('Registering user with email:', uniqueEmail);
    
    await page.fill('input[name="email"]', uniqueEmail);
    await page.fill('input[name="firstName"]', 'Test');
    await page.fill('input[name="lastName"]', 'User');
    await page.fill('input[name="phone"]', '+15551234567');
    await page.fill('input[name="password"]', testPassword);
    await page.fill('input[name="confirmPassword"]', testPassword);
    
    // Step 5: Submit registration
    await page.waitForTimeout(1000);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    
    // Step 6: Verify registration success (should be on login page)
    const currentUrl = page.url();
    expect(currentUrl).toContain('/login');
    console.log('Registration completed, now on login page');
    
    // Step 7: Navigate to fresh login page to avoid form state issues
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Step 8: Fill login form with same credentials
    await page.fill('input[name="email"]', uniqueEmail);
    await page.fill('input[name="password"]', testPassword);
    
    // Step 9: Submit login
    await page.click('button[type="submit"]');
    await page.waitForTimeout(5000);
    
    // Step 10: Verify login success
    const finalUrl = page.url();
    console.log('Final URL after login:', finalUrl);
    
    // Should be redirected to dashboard or onboarding
    expect(finalUrl).toMatch(/\/(dashboard|onboarding)/);
    console.log('✅ Successfully registered and logged in!');
  });

  test('should handle invalid login credentials', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Try to login with invalid credentials
    await page.fill('input[name="email"]', 'nonexistent@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    
    // Should still be on login page with error message
    const currentUrl = page.url();
    expect(currentUrl).toContain('/login');
    
    // Check for error message
    const errorMessages = await page.locator('[role="alert"], .text-red-600, .error').allTextContents();
    expect(errorMessages.length).toBeGreaterThan(0);
    console.log('✅ Invalid login properly handled with error message');
  });
});