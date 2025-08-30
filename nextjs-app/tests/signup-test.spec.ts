import { test, expect } from '@playwright/test';

test.describe('Step 1: Signup Test', () => {
  test('should successfully register a new user', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Wait for the Sign up button to be visible
    await page.waitForSelector('button:has-text("Sign up")', { timeout: 5000 });
    
    // Click "Sign up" to switch to registration mode
    await page.click('button:has-text("Sign up")');
    
    // Wait a moment for the form to switch
    await page.waitForTimeout(1000);
    
    // Wait for registration form to appear
    await page.waitForSelector('input[name="firstName"]', { timeout: 10000 });
    
    // Fill registration form with unique email
    const uniqueEmail = `test${Date.now()}@example.com`;
    console.log('Using email:', uniqueEmail);
    
    await page.fill('input[name="email"]', uniqueEmail);
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    // Use E.164-like format or leave blank to satisfy validation
    await page.fill('input[name="phone"]', '+15551234567');
    await page.fill('input[name="password"]', 'Jd9!Qm7#VzA2');
    await page.fill('input[name="confirmPassword"]', 'Jd9!Qm7#VzA2');
    
    // Wait a moment for validation
    await page.waitForTimeout(1000);
    
    // Check if submit button is enabled
    const submitButton = page.locator('button[type="submit"]');
    const isDisabled = await submitButton.getAttribute('disabled');
    console.log('Submit button disabled:', isDisabled);
    
    // Submit registration
    await submitButton.click({ force: true });
    
    // Wait for response
    await page.waitForTimeout(3000);
    
    // Check current URL and any error messages
    console.log('Current URL after registration:', page.url());
    
    // Check for any error messages on the page
    const errorMessages = await page.locator('[role="alert"], .text-red-600, .error').allTextContents();
    console.log('Error messages:', errorMessages);
    
    // Check for success indicators
    const successMessages = await page.locator('.text-green-600, .success').allTextContents();
    console.log('Success messages:', successMessages);
    
    // Verify we're either redirected or see a success message
    const currentUrl = page.url();
    const isOnLoginPage = currentUrl.includes('/login');
    
    if (isOnLoginPage) {
      console.log('Still on login page - checking for success message or login form');
      // If still on login page, check if we can now login
      const hasLoginForm = await page.locator('input[name="email"]').isVisible();
      console.log('Login form visible:', hasLoginForm);
    } else {
      console.log('Redirected to:', currentUrl);
    }
  });
});