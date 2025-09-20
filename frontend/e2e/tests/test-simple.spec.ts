import { test, expect } from '@playwright/test';

test.describe('Simple Core Functionality', () => {
  test('should load home page', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await expect(page).toHaveTitle(/PropertyAI/);
    await expect(page.locator('body')).toBeVisible();
  });

  test('should load login page', async ({ page }) => {
    await page.goto('http://localhost:3000/login');
    await expect(page.locator('form')).toBeVisible();
  });

  test('should load registration page', async ({ page }) => {
    await page.goto('http://localhost:3000/register');
    await expect(page.locator('form')).toBeVisible();
  });

  test('should load dashboard page', async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard');
    await expect(page.locator('body')).toBeVisible();
  });
});
