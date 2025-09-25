import { expect, test } from '@playwright/test';

/**
 * Natural Language Test: User Authentication Flow
 * ==============================================
 * 
 * Test Description: "User can register, login, and access dashboard"
 * 
 * This test validates the complete authentication journey including:
 * - User registration with valid data
 * - Email verification (if implemented)
 * - User login with correct credentials
 * - Dashboard access after authentication
 * - Logout functionality
 */

test.describe('Authentication Flow - Natural Language Testing', () => {
  test('User can register and login successfully', async ({ page }) => {
    // Natural Language: "Go to the application and verify it loads"
    await page.goto('/');
    await expect(page).toHaveTitle(/PropertyAI/);

    // Natural Language: "Navigate to login page and switch to registration"
    await page.goto('/login');
    await expect(page).toHaveURL(/.*login/);
    await page.click('text=Sign up');

    // Natural Language: "Fill registration form with valid user data"
    await page.fill('input[name="first_name"]', 'John');
    await page.fill('input[name="last_name"]', 'Doe');
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.fill('input[name="confirmPassword"]', 'SecurePassword123!');

    // Natural Language: "Submit registration and verify success"
    await page.click('button[type="submit"]');

    // Wait a bit for the form submission to process
    await page.waitForTimeout(3000);

    // Check current URL and handle accordingly
    const currentUrl = page.url();
    console.log('Current URL after registration:', currentUrl);

    // If still on login page, check for success message or error
    if (currentUrl.includes('/login')) {
      // Look for success message or check if we're back to login form
      const successMessage = page.locator('text=Registration successful, text=successfully, text=Please sign in');
      if (await successMessage.isVisible()) {
        console.log('Registration successful, switching to login form');
        // Registration was successful, now test login
        await page.fill('input[name="email"]', 'john.doe@example.com');
        await page.fill('input[name="password"]', 'SecurePassword123!');
        await page.click('button[type="submit"]');
        await page.waitForURL(/.*(dashboard|onboarding)/, { timeout: 10000 });
      } else {
        // Check for error messages
        const errorMessage = page.locator('[role="alert"], .text-red-600, .text-red-500');
        if (await errorMessage.isVisible()) {
          const errorText = await errorMessage.textContent();
          console.log('Registration error:', errorText);
        }
      }
    } else {
      // Redirected successfully
      await expect(page).toHaveURL(/.*(dashboard|onboarding)/);
    }

    // Natural Language: "Verify logout functionality works"
    // Look for logout button (arrow right on rectangle icon)
    await page.click('button[aria-label*="logout"], button:has-text("Logout"), button[title*="logout"]');
    await expect(page).toHaveURL(/.*login/);
  });

  test('User login fails with invalid credentials', async ({ page }) => {
    // Natural Language: "Go to login page"
    await page.goto('/login');

    // Natural Language: "Try to login with invalid credentials"
    await page.fill('input[name="email"]', 'invalid@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Natural Language: "Verify error message is displayed"
    await expect(page.locator('text=Invalid credentials')).toBeVisible();
    await expect(page).toHaveURL(/.*login/);
  });
});
