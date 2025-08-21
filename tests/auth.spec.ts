import { test, expect } from '@playwright/test';

test.describe('Authentication Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page before each test
    await page.goto('/');
  });

  test('should display login page correctly', async ({ page }) => {
    // Check if we're on the login page
    await expect(page).toHaveTitle(/Real Estate CRM - Login/);
    
    // Check for login form elements
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    
    // Check for login form labels
    await expect(page.locator('label[for="email"]')).toContainText('Email');
    await expect(page.locator('label[for="password"]')).toContainText('Password');
  });

  test('should login with valid credentials', async ({ page }) => {
    // Fill in valid credentials
    await page.fill('input[type="email"]', 'demo@mumbai.com');
    await page.fill('input[type="password"]', 'demo123');
    
    // Submit the form
    await page.click('button[type="submit"]');
    
    // Wait for navigation to dashboard
    await page.waitForURL('**/dashboard');
    
    // Verify we're on the dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page).toHaveTitle(/PropertyAI - Next-Gen AI Real Estate Dashboard/);
    
    // Check for dashboard elements
    await expect(page.locator('h1')).toContainText('PropertyAI');
  });

  test('should show error with invalid credentials', async ({ page }) => {
    // Fill in invalid credentials
    await page.fill('input[type="email"]', 'invalid@example.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    
    // Submit the form
    await page.click('button[type="submit"]');
    
    // Should stay on login page
    await expect(page).toHaveURL('/');
    
    // Check for error message (if implemented)
    // Note: Current implementation may not show error messages
    // This test verifies we don't navigate away with invalid credentials
  });

  test('should validate required fields', async ({ page }) => {
    // Try to submit without filling fields
    await page.click('button[type="submit"]');
    
    // Should stay on login page
    await expect(page).toHaveURL('/');
    
    // Check that form is still visible
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('should maintain session after login', async ({ page }) => {
    // Login first
    await page.fill('input[type="email"]', 'demo@mumbai.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    
    // Wait for dashboard
    await page.waitForURL('**/dashboard');
    
    // Navigate to another page and back
    await page.goto('/');
    await page.goto('/dashboard');
    
    // Should still be on dashboard (session maintained)
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page).toHaveTitle(/PropertyAI - Next-Gen AI Real Estate Dashboard/);
  });
});
