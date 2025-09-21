import { test, expect } from '@playwright/test';

/**
 * Debug Login and Authentication Issues
 * ====================================
 * 
 * This test investigates what's wrong with the login flow
 */

test.describe('Debug Login and Authentication', () => {
  
  test('Investigate login page loading and form elements', async ({ page }) => {
    
    console.log('🔍 Investigating login page...');
    
    // Go to login page
    await page.goto('/login');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Wait for page to load
    await page.waitForTimeout(3000);
    
    // Check what elements are actually visible
    console.log('📋 Checking page content...');
    
    // Look for any forms
    const forms = page.locator('form');
    const formCount = await forms.count();
    console.log(`📝 Found ${formCount} forms on page`);
    
    // Look for input fields
    const inputs = page.locator('input');
    const inputCount = await inputs.count();
    console.log(`🔤 Found ${inputCount} input fields on page`);
    
    // Look for buttons
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    console.log(`🔘 Found ${buttonCount} buttons on page`);
    
    // Check for loading states
    const loadingElements = page.locator('text=Loading, .loading, [data-testid*="loading"]');
    const loadingCount = await loadingElements.count();
    console.log(`⏳ Found ${loadingCount} loading elements`);
    
    // Check page HTML content
    const pageContent = await page.content();
    console.log(`📄 Page content length: ${pageContent.length} characters`);
    
    // Check if there are any JavaScript errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`❌ JavaScript Error: ${msg.text()}`);
      }
    });
    
    // Take a screenshot for debugging
    await page.screenshot({ path: 'debug-login-page.png' });
    console.log('📸 Screenshot saved: debug-login-page.png');
    
    // Check specific elements we expect
    const emailInput = page.locator('input[name="email"]');
    const passwordInput = page.locator('input[name="password"]');
    const submitButton = page.locator('button[type="submit"]');
    
    console.log(`📧 Email input visible: ${await emailInput.isVisible()}`);
    console.log(`🔒 Password input visible: ${await passwordInput.isVisible()}`);
    console.log(`📤 Submit button visible: ${await submitButton.isVisible()}`);
    
    // Try to find any input fields
    const allInputs = page.locator('input');
    for (let i = 0; i < Math.min(await allInputs.count(), 5); i++) {
      const input = allInputs.nth(i);
      const type = await input.getAttribute('type');
      const name = await input.getAttribute('name');
      const placeholder = await input.getAttribute('placeholder');
      console.log(`🔤 Input ${i}: type="${type}", name="${name}", placeholder="${placeholder}"`);
    }
  });

  test('Test backend login API directly', async ({ page }) => {
    
    console.log('🔍 Testing backend login API directly...');
    
    // Test login API with form data (as expected by FastAPI Users)
    const loginResponse = await page.request.post('http://localhost:8000/api/v1/auth/login', {
      form: {
        username: 'test@propertyai.com',
        password: 'TestPassword123!'
      }
    });
    
    console.log(`🔐 Login API Response: ${loginResponse.status()}`);
    
    if (loginResponse.status() === 200) {
      const loginData = await loginResponse.json();
      console.log(`✅ Login successful: ${JSON.stringify(loginData)}`);
    } else {
      const errorText = await loginResponse.text();
      console.log(`❌ Login failed: ${errorText}`);
    }
  });

  test('Check registration flow and redirect', async ({ page }) => {
    
    console.log('🔍 Testing registration flow...');
    
    await page.goto('/register');
    
    // Fill registration form
    const timestamp = Date.now();
    const testEmail = `test${timestamp}@propertyai.com`;
    
    await page.fill('input[name="firstName"]', 'Test');
    await page.fill('input[name="lastName"]', 'User');
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', 'TestPassword123!');
    await page.fill('input[name="confirmPassword"]', 'TestPassword123!');
    
    console.log(`📧 Registering with email: ${testEmail}`);
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Wait and check what happens
    await page.waitForTimeout(5000);
    
    const currentUrl = page.url();
    console.log(`📍 After registration, URL: ${currentUrl}`);
    
    // Check if we're redirected or if there are any error messages
    const errorMessages = page.locator('text=error, text=Error, .error, [class*="error"]');
    const errorCount = await errorMessages.count();
    console.log(`❌ Found ${errorCount} error messages`);
    
    // Check for success messages
    const successMessages = page.locator('text=success, text=Success, .success, [class*="success"]');
    const successCount = await successMessages.count();
    console.log(`✅ Found ${successCount} success messages`);
    
    // Take screenshot after registration
    await page.screenshot({ path: 'debug-after-registration.png' });
    console.log('📸 Screenshot saved: debug-after-registration.png');
  });
});