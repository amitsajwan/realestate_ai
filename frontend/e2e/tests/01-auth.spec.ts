import { test, expect } from '@playwright/test';

test.describe('Authentication System', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should display login form correctly', async ({ page }) => {
    // Check if login form elements are visible
    await expect(page.locator('h2')).toContainText('Sign in to your account');
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should switch to registration form', async ({ page }) => {
    // Click on "Sign up" link
    await page.click('text=Sign up');
    
    // Check if registration form is displayed
    await expect(page.locator('h2')).toContainText('Create your account');
    await expect(page.locator('input[name="firstName"]')).toBeVisible();
    await expect(page.locator('input[name="lastName"]')).toBeVisible();
    await expect(page.locator('input[name="confirmPassword"]')).toBeVisible();
  });

  test('should validate email field', async ({ page }) => {
    // Try to submit with invalid email
    await page.fill('input[name="email"]', 'invalid-email');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Check for validation error
    await expect(page.locator('text=Invalid email format')).toBeVisible();
  });

  test('should validate password field', async ({ page }) => {
    // Switch to registration form
    await page.click('text=Sign up');
    
    // Try weak password
    await page.fill('input[name="password"]', '123');
    
    // Check for password strength indicator
    await expect(page.locator('text=Very Weak')).toBeVisible();
  });

  test('should show password strength indicator', async ({ page }) => {
    // Switch to registration form
    await page.click('text=Sign up');
    
    // Test different password strengths
    await page.fill('input[name="password"]', 'password123');
    await expect(page.locator('text=Weak')).toBeVisible();
    
    await page.fill('input[name="password"]', 'Password123!');
    await expect(page.locator('text=Strong')).toBeVisible();
  });

  test('should toggle password visibility', async ({ page }) => {
    // Fill password field
    await page.fill('input[name="password"]', 'testpassword');
    
    // Check initial state (password hidden)
    await expect(page.locator('input[name="password"]')).toHaveAttribute('type', 'password');
    
    // Click eye icon to show password
    await page.click('button[aria-label="Toggle password visibility"]');
    await expect(page.locator('input[name="password"]')).toHaveAttribute('type', 'text');
    
    // Click again to hide password
    await page.click('button[aria-label="Toggle password visibility"]');
    await expect(page.locator('input[name="password"]')).toHaveAttribute('type', 'password');
  });

  test('should handle Facebook login button', async ({ page }) => {
    // Check if Facebook login button is visible
    await expect(page.locator('text=Facebook')).toBeVisible();
    
    // Click Facebook login button
    await page.click('text=Facebook');
    
    // Should redirect to Facebook OAuth (in real scenario)
    // For testing, we'll just verify the button is clickable
    await expect(page.locator('text=Facebook')).toBeVisible();
  });

  test('should navigate to forgot password', async ({ page }) => {
    // Click forgot password link
    await page.click('text=Forgot your password?');
    
    // Should navigate to forgot password page
    await expect(page).toHaveURL(/.*forgot-password/);
  });

  test('should handle form submission with valid data', async ({ page }) => {
    // Fill valid login data
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should show loading state
    await expect(page.locator('button[type="submit"]')).toBeDisabled();
  });

  test('should handle registration with valid data', async ({ page }) => {
    // Switch to registration form
    await page.click('text=Sign up');
    
    // Fill valid registration data
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.fill('input[name="phone"]', '+1234567890');
    await page.fill('input[name="password"]', 'Password123!');
    await page.fill('input[name="confirmPassword"]', 'Password123!');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should show loading state
    await expect(page.locator('button[type="submit"]')).toBeDisabled();
  });

  test('should validate password confirmation', async ({ page }) => {
    // Switch to registration form
    await page.click('text=Sign up');
    
    // Fill mismatched passwords
    await page.fill('input[name="password"]', 'Password123!');
    await page.fill('input[name="confirmPassword"]', 'DifferentPassword123!');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should show validation error
    await expect(page.locator('text=Passwords do not match')).toBeVisible();
  });

  test('should handle form validation errors', async ({ page }) => {
    // Try to submit empty form
    await page.click('button[type="submit"]');
    
    // Should show validation errors
    await expect(page.locator('text=Email is required')).toBeVisible();
    await expect(page.locator('text=Password is required')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check if form is still usable on mobile
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    
    // Check if text wraps properly
    await expect(page.locator('text=Don\'t have an account?')).toBeVisible();
  });
});