import { test, expect } from '@playwright/test';

/**
 * Debug Hydration and Client-Side Rendering Issues
 * ===============================================
 */

test.describe('Debug Hydration Issues', () => {
  
  test('Check for JavaScript errors and hydration issues', async ({ page }) => {
    
    console.log('🔍 Checking for JavaScript errors and hydration issues...');
    
    const errors: string[] = [];
    const logs: string[] = [];
    
    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
        console.log(`❌ JavaScript Error: ${msg.text()}`);
      } else {
        logs.push(msg.text());
        console.log(`📝 Console Log: ${msg.text()}`);
      }
    });
    
    // Capture page errors
    page.on('pageerror', error => {
      errors.push(error.message);
      console.log(`❌ Page Error: ${error.message}`);
    });
    
    // Go to login page
    await page.goto('/login');
    
    // Wait for potential hydration
    await page.waitForTimeout(5000);
    
    console.log(`📊 Total errors captured: ${errors.length}`);
    console.log(`📊 Total logs captured: ${logs.length}`);
    
    // Check if form eventually renders
    const form = page.locator('form');
    const formVisible = await form.isVisible();
    console.log(`📝 Form visible after 5 seconds: ${formVisible}`);
    
    // Check for the "Loading..." text
    const loadingText = page.locator('text=Loading...');
    const loadingVisible = await loadingText.isVisible();
    console.log(`⏳ Loading text visible: ${loadingVisible}`);
    
    // Check for input fields
    const emailInput = page.locator('input[name="email"]');
    const emailVisible = await emailInput.isVisible();
    console.log(`📧 Email input visible: ${emailVisible}`);
    
    // Wait longer to see if form eventually loads
    await page.waitForTimeout(10000);
    
    const formVisibleAfterWait = await form.isVisible();
    const emailVisibleAfterWait = await emailInput.isVisible();
    
    console.log(`📝 Form visible after 15 seconds: ${formVisibleAfterWait}`);
    console.log(`📧 Email input visible after 15 seconds: ${emailVisibleAfterWait}`);
    
    // Check page source for any clues
    const pageContent = await page.content();
    const hasLoadingDiv = pageContent.includes('Loading...');
    const hasForm = pageContent.includes('<form');
    const hasInput = pageContent.includes('<input');
    
    console.log(`📄 Page source contains "Loading...": ${hasLoadingDiv}`);
    console.log(`📄 Page source contains "<form": ${hasForm}`);
    console.log(`📄 Page source contains "<input": ${hasInput}`);
    
    // Take screenshot
    await page.screenshot({ path: 'debug-hydration.png' });
    console.log('📸 Screenshot saved: debug-hydration.png');
  });

  test('Test if authManager is causing issues', async ({ page }) => {
    
    console.log('🔍 Testing authManager initialization...');
    
    // Go to login page
    await page.goto('/login');
    
    // Wait for page to load
    await page.waitForTimeout(3000);
    
    // Check if authManager is available in window object
    const authManagerExists = await page.evaluate(() => {
      return typeof window !== 'undefined' && 
             'authManager' in window && 
             window.authManager !== undefined;
    });
    
    console.log(`🔐 AuthManager exists in window: ${authManagerExists}`);
    
    // Check for any auth-related errors
    const authErrors = await page.evaluate(() => {
      return (window as any).authErrors || [];
    });
    
    console.log(`❌ Auth errors: ${JSON.stringify(authErrors)}`);
    
    // Try to trigger form rendering manually
    await page.evaluate(() => {
      // Force client-side rendering
      if (typeof window !== 'undefined') {
        const event = new Event('load');
        window.dispatchEvent(event);
      }
    });
    
    await page.waitForTimeout(2000);
    
    // Check if form is now visible
    const form = page.locator('form');
    const formVisible = await form.isVisible();
    console.log(`📝 Form visible after manual trigger: ${formVisible}`);
  });

  test('Check registration form submission method', async ({ page }) => {
    
    console.log('🔍 Checking registration form submission method...');
    
    await page.goto('/register');
    
    // Wait for page to load
    await page.waitForTimeout(3000);
    
    // Check form method
    const form = page.locator('form').first();
    const method = await form.getAttribute('method');
    const action = await form.getAttribute('action');
    
    console.log(`📝 Form method: ${method}`);
    console.log(`📝 Form action: ${action}`);
    
    // Check if form has proper submission handler
    const hasOnSubmit = await form.evaluate((el) => {
      return el.onsubmit !== null || el.getAttribute('onsubmit') !== null;
    });
    
    console.log(`📝 Form has onSubmit handler: ${hasOnSubmit}`);
    
    // Check for any form-related JavaScript errors
    const formErrors = await page.evaluate(() => {
      const errors = [];
      try {
        const forms = document.querySelectorAll('form');
        forms.forEach((form, index) => {
          console.log(`Form ${index}:`, form);
        });
      } catch (e) {
        errors.push(e.message);
      }
      return errors;
    });
    
    console.log(`❌ Form errors: ${JSON.stringify(formErrors)}`);
  });
});