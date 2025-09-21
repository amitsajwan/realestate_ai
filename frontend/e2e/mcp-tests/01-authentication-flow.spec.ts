import { test, expect } from '@playwright/test';

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
    
    // Natural Language: "Navigate to registration page"
    await page.click('text=Sign Up');
    await expect(page).toHaveURL(/.*register/);
    
    // Natural Language: "Fill registration form with valid user data"
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.fill('input[name="confirmPassword"]', 'SecurePassword123!');
    
    // Natural Language: "Submit registration and verify success"
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Registration successful')).toBeVisible();
    
    // Natural Language: "Navigate to login page"
    await page.click('text=Sign In');
    await expect(page).toHaveURL(/.*login/);
    
    // Natural Language: "Login with registered credentials"
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.click('button[type="submit"]');
    
    // Natural Language: "Verify user is logged in and dashboard loads"
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('text=Welcome, John')).toBeVisible();
    
    // Natural Language: "Verify logout functionality works"
    await page.click('button[data-testid="logout-button"]');
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
