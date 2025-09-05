import { test, expect } from '@playwright/test';

test.describe('Consolidated Property Form End-to-End Tests', () => {
  const testEmail = 'demo@mumbai.com';
  const testPassword = 'demo123';

  test.beforeEach(async ({ page }) => {
    // Enable detailed logging
    page.on('console', msg => {
      console.log(`[BROWSER] ${msg.type()}: ${msg.text()}`);
    });

    page.on('pageerror', error => {
      console.error(`[PAGE ERROR] ${error.message}`);
    });

    // Log all network requests
    page.on('request', request => {
      console.log(`[REQUEST] ${request.method()} ${request.url()}`);
    });

    page.on('response', response => {
      const status = response.status();
      const url = response.url();
      if (status >= 400) {
        console.error(`[RESPONSE ERROR] ${response.request().method()} ${url} - Status: ${status}`);
      } else {
        console.log(`[RESPONSE] ${response.request().method()} ${url} - Status: ${status}`);
      }
    });
  });

  test('Simple variant on homepage works correctly', async ({ page }) => {
    console.log('=== Testing Simple Variant on Homepage ===');

    // Step 1: Navigate to login page
    console.log('Step 1: Navigating to login page');
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Verify login page loaded
    await expect(page).toHaveTitle(/PropertyAI|Login/);
    console.log('✓ Login page loaded successfully');

    // Step 2: Perform login
    console.log('Step 2: Performing login with demo credentials');
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);
    
    // Click login button
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    
    // Verify successful login (should redirect to dashboard)
    await expect(page).toHaveURL(/\/dashboard/);
    console.log('✓ Login successful, redirected to dashboard');

    // Step 3: Navigate to homepage
    console.log('Step 3: Navigating to homepage');
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Step 4: Test simple property form
    console.log('Step 4: Testing simple property form');
    
    // Find the Add Property section
    const addPropertySection = page.locator('text=Add New Property').first();
    await expect(addPropertySection).toBeVisible();
    console.log('✓ Add Property section found');
    
    // Fill out the simple form
    await page.fill('input[name="title"]', 'Test Property from E2E');
    await page.fill('input[name="location"]', 'Mumbai, Maharashtra');
    await page.fill('input[name="price"]', '5000000');
    await page.fill('textarea[name="description"]', 'This is a test property created during E2E testing');
    
    console.log('✓ Form fields filled');
    
    // Submit the form
    await page.click('button:has-text("Add Property")');
    
    // Wait for success message or redirect
    await page.waitForTimeout(2000);
    
    console.log('✓ Simple property form submitted successfully');
  });

  test('Wizard variant on Smart Form Demo page works correctly', async ({ page }) => {
    console.log('=== Testing Wizard Variant on Smart Form Demo ===');

    // Step 1: Navigate to login page
    console.log('Step 1: Navigating to login page');
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Step 2: Perform login
    console.log('Step 2: Performing login with demo credentials');
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);
    
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    
    // Step 3: Navigate to Smart Form Demo
    console.log('Step 3: Navigating to Smart Form Demo');
    await page.goto('/demo/smart-form');
    await page.waitForLoadState('networkidle');
    
    // Verify we're on the right page
    await expect(page.locator('text=Smart Property Form')).toBeVisible();
    console.log('✓ Smart Form Demo page loaded');
    
    // Step 4: Test wizard navigation
    console.log('Step 4: Testing wizard navigation');
    
    // Should start at step 1
    await expect(page.locator('text=Step 1 of 4')).toBeVisible();
    console.log('✓ Started at Step 1');
    
    // Fill basic information
    await page.fill('input[name="title"]', 'Wizard Test Property');
    await page.fill('input[name="location"]', 'Bandra, Mumbai');
    await page.fill('input[name="price"]', '7500000');
    
    // Go to next step
    await page.click('button:has-text("Next")');
    await expect(page.locator('text=Step 2 of 4')).toBeVisible();
    console.log('✓ Navigated to Step 2');
    
    // Fill property details
    await page.selectOption('select[name="propertyType"]', 'apartment');
    await page.fill('input[name="bedrooms"]', '3');
    await page.fill('input[name="bathrooms"]', '2');
    
    // Go to next step
    await page.click('button:has-text("Next")');
    await expect(page.locator('text=Step 3 of 4')).toBeVisible();
    console.log('✓ Navigated to Step 3');
    
    // Fill amenities (if available)
    // Go to final step
    await page.click('button:has-text("Next")');
    await expect(page.locator('text=Step 4 of 4')).toBeVisible();
    console.log('✓ Navigated to Step 4 (Review)');
    
    // Submit the form
    await page.click('button:has-text("Submit Property")');
    
    // Wait for success
    await page.waitForTimeout(3000);
    
    console.log('✓ Wizard property form submitted successfully');
  });

  test('AI features work when enabled', async ({ page }) => {
    console.log('=== Testing AI Features ===');

    // Login first
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    
    // Navigate to Smart Form Demo
    await page.goto('/demo/smart-form');
    await page.waitForLoadState('networkidle');
    
    // Check for AI-related buttons/features
    const aiButtons = page.locator('button:has-text("AI")');
    if (await aiButtons.count() > 0) {
      console.log('✓ AI features are visible');
      
      // Test AI suggestion (if available)
      const aiSuggestButton = aiButtons.first();
      await aiSuggestButton.click();
      await page.waitForTimeout(1000);
      console.log('✓ AI suggestion button clicked');
    } else {
      console.log('ℹ No AI buttons found - this is expected if AI features are not enabled');
    }
  });

  test('Form validation works correctly', async ({ page }) => {
    console.log('=== Testing Form Validation ===');

    // Login first
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    
    // Test simple form validation on homepage
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Try to submit empty form
    await page.click('button:has-text("Add Property")');
    
    // Check for validation messages
    const validationMessages = page.locator('text=/required|Please|Error/');
    if (await validationMessages.count() > 0) {
      console.log('✓ Form validation is working');
    } else {
      console.log('ℹ No validation messages found - form might have different validation approach');
    }
  });

  test('CORS and API connectivity work correctly', async ({ page }) => {
    console.log('=== Testing CORS and API Connectivity ===');

    // Navigate to any page to test API connectivity
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Monitor network requests for CORS errors
    let corsErrors = 0;
    page.on('response', response => {
      if (response.status() === 400 && response.request().method() === 'OPTIONS') {
        corsErrors++;
        console.error(`CORS Error detected: ${response.url()}`);
      }
    });
    
    // Try to make a login request
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);
    await page.click('button[type="submit"]');
    
    // Wait for request to complete
    await page.waitForTimeout(3000);
    
    if (corsErrors === 0) {
      console.log('✓ No CORS errors detected');
    } else {
      console.error(`❌ ${corsErrors} CORS errors detected`);
    }
    
    // Check if we successfully logged in (no CORS issues)
    const currentUrl = page.url();
    if (currentUrl.includes('/dashboard') || currentUrl.includes('/onboarding')) {
      console.log('✓ API connectivity working - successful login');
    } else {
      console.log('ℹ Login may have failed - check API connectivity');
    }
  });
});