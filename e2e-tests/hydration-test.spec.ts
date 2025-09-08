import { test, expect } from '@playwright/test';

test.describe('Hydration Error Test', () => {
  test('should load login page without hydration errors', async ({ page }) => {
    // Listen for console errors
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Listen for page errors
    page.on('pageerror', error => {
      errors.push(`Page error: ${error.message}`);
    });

    // Navigate to login page
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Wait a bit for any hydration to complete
    await page.waitForTimeout(2000);
    
    // Check for hydration errors
    const hydrationErrors = errors.filter(error => 
      error.includes('Hydration') || 
      error.includes('hydration') ||
      error.includes('mismatch')
    );
    
    console.log('All errors:', errors);
    console.log('Hydration errors:', hydrationErrors);
    
    // The page should load without hydration errors
    expect(hydrationErrors.length).toBe(0);
  });

  test('should load dashboard page without hydration errors', async ({ page }) => {
    // Listen for console errors
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Listen for page errors
    page.on('pageerror', error => {
      errors.push(`Page error: ${error.message}`);
    });

    // Navigate to dashboard page
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Wait a bit for any hydration to complete
    await page.waitForTimeout(2000);
    
    // Check for hydration errors
    const hydrationErrors = errors.filter(error => 
      error.includes('Hydration') || 
      error.includes('hydration') ||
      error.includes('mismatch')
    );
    
    console.log('All errors:', errors);
    console.log('Hydration errors:', hydrationErrors);
    
    // The page should load without hydration errors
    expect(hydrationErrors.length).toBe(0);
  });
});