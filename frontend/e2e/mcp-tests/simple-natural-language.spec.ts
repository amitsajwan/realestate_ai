import { test, expect } from '@playwright/test';

/**
 * Simple Natural Language E2E Tests with Playwright MCP
 * ====================================================
 * 
 * These tests use natural language descriptions that Playwright MCP
 * can understand and execute without needing specific selectors.
 */

test.describe('PropertyAI Natural Language E2E Tests', () => {
  
  test('User can access the login page', async ({ page }) => {
    // Natural Language: "Go to the login page"
    await page.goto('/login');
    
    // Natural Language: "Check that the page loaded successfully"
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Natural Language: "Verify there's a login form"
    await expect(page.locator('form')).toBeVisible();
  });

  test('User can see the main navigation', async ({ page }) => {
    // Natural Language: "Go to the home page"
    await page.goto('/');
    
    // Natural Language: "Check that the page has navigation"
    await expect(page.locator('nav, header')).toBeVisible();
  });

  test('User can access different sections', async ({ page }) => {
    // Natural Language: "Start at the home page"
    await page.goto('/');
    
    // Natural Language: "Try to navigate to properties section"
    await page.goto('/properties');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Natural Language: "Try to navigate to analytics section"  
    await page.goto('/analytics');
    await expect(page).toHaveTitle(/PropertyAI/);
  });

  test('Application responds to basic interactions', async ({ page }) => {
    // Natural Language: "Go to the login page"
    await page.goto('/login');
    
    // Natural Language: "Look for any clickable buttons"
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    
    // Natural Language: "Verify there are interactive elements"
    expect(buttonCount).toBeGreaterThan(0);
  });

  test('Backend API is accessible', async ({ page }) => {
    // Natural Language: "Check if the backend API is responding"
    const response = await page.request.get('http://localhost:8000/api/v1/health');
    expect(response.status()).toBe(200);
  });
});