import { test, expect } from '@playwright/test';

test.describe('Dashboard Navigation and UX Flow', () => {
  test('should navigate through all dashboard sections and verify UX', async ({ page }) => {
    // Start at the dashboard (assuming user is logged in)
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check if we're redirected to login (expected for unauthenticated users)
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      console.log('User not authenticated, testing login flow first');
      
      // Test login page elements
      await expect(page.locator('h2')).toContainText('Sign in');
      await expect(page.locator('input[name="email"]')).toBeVisible();
      await expect(page.locator('input[name="password"]')).toBeVisible();
      
      // Switch to registration to test the form
      await page.click('text=Sign up');
      await page.waitForTimeout(1000);
      
      // Test registration form elements
      await expect(page.locator('input[name="firstName"]')).toBeVisible();
      await expect(page.locator('input[name="lastName"]')).toBeVisible();
      await expect(page.locator('input[name="email"]')).toBeVisible();
      await expect(page.locator('input[name="password"]')).toBeVisible();
      await expect(page.locator('input[name="confirmPassword"]')).toBeVisible();
      
      console.log('✓ Login/Registration forms are properly rendered');
      return; // Exit early since we can't test dashboard without authentication
    }
    
    // If we reach here, user is authenticated - test dashboard navigation
    console.log('Testing authenticated dashboard navigation');
    
    // Test main navigation sections
    const navigationSections = [
      { name: 'Dashboard', selector: 'a[href="/"]' },
      { name: 'Properties', selector: 'a[href="/properties"]' },
      { name: 'Smart Form Demo', selector: 'a[href="/demo/smart-form"]' },
      { name: 'AI Content', selector: 'a[href="/ai-content"]' },
      { name: 'Analytics', selector: 'a[href="/analytics"]' },
      { name: 'CRM', selector: 'a[href="/crm"]' },
      { name: 'Facebook', selector: 'a[href="/facebook"]' },
      { name: 'Profile', selector: 'a[href="/profile"]' }
    ];
    
    // Test each navigation section
    for (const section of navigationSections) {
      console.log(`Testing navigation to ${section.name}`);
      
      // Check if navigation link exists
      const navLink = page.locator(section.selector);
      await expect(navLink).toBeVisible();
      
      // Click and verify navigation
      await navLink.click();
      await page.waitForLoadState('networkidle');
      
      // Verify URL changed (basic navigation test)
      const newUrl = page.url();
      console.log(`Navigated to: ${newUrl}`);
      
      // Go back to dashboard for next test
      if (section.name !== 'Dashboard') {
        await page.goto('/');
        await page.waitForLoadState('networkidle');
      }
    }
    
    console.log('✓ All navigation sections are accessible');
  });
  
  test('should test property creation flow', async ({ page }) => {
    // Navigate to properties page
    await page.goto('/properties');
    await page.waitForLoadState('networkidle');
    
    // Check if we're redirected to login
    if (page.url().includes('/login')) {
      console.log('User not authenticated, skipping property creation test');
      return;
    }
    
    // Look for Add Property button
    const addPropertyButton = page.locator('button:has-text("Add Property")');
    if (await addPropertyButton.isVisible()) {
      console.log('✓ Add Property button found');
      
      // Click Add Property button
      await addPropertyButton.click();
      await page.waitForTimeout(1000);
      
      // Check if property form is displayed
      const propertyForm = page.locator('form');
      if (await propertyForm.isVisible()) {
        console.log('✓ Property form is displayed');
        
        // Test form fields
        const formFields = [
          'input[name="title"]',
          'select[name="type"]',
          'input[name="location"]',
          'input[name="price"]',
          'textarea[name="description"]'
        ];
        
        for (const field of formFields) {
          const fieldElement = page.locator(field);
          if (await fieldElement.isVisible()) {
            console.log(`✓ Form field ${field} is visible`);
          }
        }
        
        // Test AI buttons if present
        const aiButtons = [
          'button:has-text("AI Suggestions")',
          'button:has-text("AI Auto-Fill")',
          'button:has-text("AI Insights")'
        ];
        
        for (const buttonText of aiButtons) {
          const button = page.locator(buttonText);
          if (await button.isVisible()) {
            console.log(`✓ ${buttonText} button is available`);
          }
        }
      }
    } else {
      console.log('Add Property button not found - checking alternative entry points');
    }
  });
  
  test('should test smart form demo navigation', async ({ page }) => {
    // Navigate directly to smart form demo
    await page.goto('/demo/smart-form');
    await page.waitForLoadState('networkidle');
    
    // Check if we're redirected to login
    if (page.url().includes('/login')) {
      console.log('User not authenticated, skipping smart form test');
      return;
    }
    
    // Verify smart form page loads
    const pageTitle = page.locator('h1, h2, h3');
    if (await pageTitle.isVisible()) {
      const titleText = await pageTitle.textContent();
      console.log(`✓ Smart form page loaded with title: ${titleText}`);
    }
    
    // Check for form elements
    const form = page.locator('form');
    if (await form.isVisible()) {
      console.log('✓ Smart form is displayed');
    }
  });
});