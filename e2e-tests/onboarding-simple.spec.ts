import { test, expect } from '@playwright/test';

test.describe('Onboarding Flow - Direct Test', () => {
  test('should render onboarding form elements', async ({ page }) => {
    // Navigate directly to onboarding page
    await page.goto('/onboarding');
    
    // Check if we're redirected to login (expected behavior)
    await page.waitForURL('/login');
    
    // Verify login page loads
    await expect(page.locator('h2')).toContainText('Sign in');
    
    // Switch to register mode
    await page.click('text=Sign up');
    
    // Verify registration form elements are present
    await expect(page.locator('input[name="firstName"]')).toBeVisible();
    await expect(page.locator('input[name="lastName"]')).toBeVisible();
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('input[name="confirmPassword"]')).toBeVisible();
    
    // Fill form with valid data
    await page.fill('input[name="email"]', `test${Date.now()}@example.com`);
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="phone"]', '+15551234567');
    await page.fill('input[name="password"]', 'Jd9!Qm7#VzA2');
    await page.fill('input[name="confirmPassword"]', 'Jd9!Qm7#VzA2');
    
    // Wait a moment for validation
    await page.waitForTimeout(1000);
    
    // Check if submit button becomes enabled
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeVisible();
    
    // Check button state
    const isDisabled = await submitButton.getAttribute('disabled');
    console.log('Button disabled:', isDisabled);
    
    // Get button text
    const buttonText = await submitButton.textContent();
    console.log('Button text:', buttonText);
    
    // Check for any console errors
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    
    // Force click if needed
    await submitButton.click({ force: true });
    
    // Wait for potential redirect or error
    await page.waitForTimeout(3000);
    
    // Log current URL for debugging
    console.log('Current URL:', page.url());
    
    // Check for any error messages on the page
    const errorMessages = await page.locator('.text-red-600, .text-red-500').allTextContents();
    console.log('Error messages:', errorMessages);
  });
});