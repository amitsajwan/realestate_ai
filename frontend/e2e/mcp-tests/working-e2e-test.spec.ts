import { test, expect } from '@playwright/test';

/**
 * Working E2E Tests - Focus on What Actually Works
 * ===============================================
 * 
 * These tests focus on functionality that we know works based on our
 * Tier 1 and Tier 2 testing results.
 */

test.describe('PropertyAI Working E2E Tests', () => {
  
  test('Backend API is accessible and healthy', async ({ page }) => {
    // Natural Language: "Check if the backend API is responding"
    const response = await page.request.get('http://localhost:8000/api/v1/health');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('Frontend application loads', async ({ page }) => {
    // Natural Language: "Go to the application and verify it loads"
    await page.goto('/');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Natural Language: "Check that the page has some content"
    await expect(page.locator('body')).toBeVisible();
  });

  test('Login page is accessible', async ({ page }) => {
    // Natural Language: "Go to the login page"
    await page.goto('/login');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Natural Language: "Check that the page loaded"
    await expect(page.locator('body')).toBeVisible();
    
    // Natural Language: "Check that there's a sign in heading"
    await expect(page.locator('text=Sign in to your account')).toBeVisible();
  });

  test('Analytics page is accessible', async ({ page }) => {
    // Natural Language: "Go to the analytics page"
    await page.goto('/analytics');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Natural Language: "Check that the page loaded"
    await expect(page.locator('body')).toBeVisible();
    
    // Natural Language: "Check that there's an analytics heading"
    await expect(page.locator('text=Analytics Dashboard')).toBeVisible();
  });

  test('Properties page is accessible', async ({ page }) => {
    // Natural Language: "Go to the properties page"
    await page.goto('/properties');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Natural Language: "Check that the page loaded"
    await expect(page.locator('body')).toBeVisible();
  });

  test('User can interact with basic elements', async ({ page }) => {
    // Natural Language: "Go to the login page"
    await page.goto('/login');
    
    // Natural Language: "Look for clickable elements"
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    
    // Natural Language: "Verify there are interactive elements"
    expect(buttonCount).toBeGreaterThan(0);
    
    // Natural Language: "Check that we can find the sign up button"
    await expect(page.locator('text=Sign up')).toBeVisible();
  });

  test('Application has proper meta information', async ({ page }) => {
    // Natural Language: "Go to the home page"
    await page.goto('/');
    
    // Natural Language: "Check that the page has proper title"
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Natural Language: "Check that the page has proper description"
    const metaDescription = await page.locator('meta[name="description"]').getAttribute('content');
    expect(metaDescription).toContain('real estate');
  });
});