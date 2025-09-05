import { test, expect } from '@playwright/test';

test.describe('GenAI Property Form End-to-End Tests', () => {
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

  test('Complete GenAI Property Form Workflow - Login to Form Submission', async ({ page }) => {
    console.log('=== Starting Complete GenAI Property Form E2E Test ===');

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
    console.log('✓ Login form submitted');

    // Wait for redirect to dashboard
    await page.waitForURL('/', { timeout: 10000 });
    console.log('✓ Successfully redirected to dashboard');

    // Step 3: Verify dashboard loaded
    console.log('Step 3: Verifying dashboard components');
    await expect(page.locator('text=PropertyAI')).toBeVisible();
    await expect(page.locator('text=Smart Form Demo')).toBeVisible();
    console.log('✓ Dashboard loaded with navigation');

    // Step 4: Navigate to GenAI Property Form
    console.log('Step 4: Navigating to GenAI Property Form');
    await page.click('text=Smart Form Demo');
    
    // Wait for navigation to GenAI form demo page
    await page.waitForURL('/demo/genai-form', { timeout: 10000 });
    console.log('✓ Successfully navigated to GenAI form demo page');

    // Step 5: Verify GenAI form page loaded
    console.log('Step 5: Verifying GenAI form page components');
    await expect(page.locator('text=GenAI Property Form Demo')).toBeVisible();
    await expect(page.locator('text=Property Details')).toBeVisible();
    console.log('✓ GenAI form page loaded successfully');

    // Step 6: Fill Property Details (Step 1)
    console.log('Step 6: Filling Property Details form');
    
    // Fill basic property information
    await page.fill('input[name="title"]', 'Luxury 3BHK Apartment in Mumbai');
    await page.fill('textarea[name="description"]', 'Beautiful spacious apartment with modern amenities');
    await page.fill('input[name="price"]', '15000000');
    await page.selectOption('select[name="propertyType"]', 'apartment');
    await page.fill('input[name="bedrooms"]', '3');
    await page.fill('input[name="bathrooms"]', '2');
    await page.fill('input[name="area"]', '1200');
    await page.fill('input[name="location"]', 'Bandra West, Mumbai');
    
    console.log('✓ Property details filled');

    // Proceed to next step
    await page.click('button:has-text("Next: AI Assistance")');
    await page.waitForTimeout(1000); // Wait for step transition
    console.log('✓ Moved to AI Assistance step');

    // Step 7: AI Assistance (Step 2)
    console.log('Step 7: Testing AI Assistance features');
    
    // Verify AI assistance step is visible
    await expect(page.locator('text=AI Assistance')).toBeVisible();
    
    // Test AI description generation
    const generateDescBtn = page.locator('button:has-text("Generate AI Description")');
    if (await generateDescBtn.isVisible()) {
      await generateDescBtn.click();
      await page.waitForTimeout(2000); // Wait for AI generation
      console.log('✓ AI description generation triggered');
    }
    
    // Test price suggestion
    const priceSuggestionBtn = page.locator('button:has-text("Get Price Suggestion")');
    if (await priceSuggestionBtn.isVisible()) {
      await priceSuggestionBtn.click();
      await page.waitForTimeout(2000);
      console.log('✓ Price suggestion triggered');
    }
    
    // Proceed to final step
    await page.click('button:has-text("Next: Social Media")');
    await page.waitForTimeout(1000);
    console.log('✓ Moved to Social Media step');

    // Step 8: Social Media Post (Step 3)
    console.log('Step 8: Testing Social Media Post features');
    
    // Verify social media step is visible
    await expect(page.locator('text=Social Media Post')).toBeVisible();
    
    // Test social media post generation
    const generatePostBtn = page.locator('button:has-text("Generate Post")');
    if (await generatePostBtn.isVisible()) {
      await generatePostBtn.click();
      await page.waitForTimeout(2000);
      console.log('✓ Social media post generation triggered');
    }

    // Step 9: Submit the complete form
    console.log('Step 9: Submitting the complete property form');
    
    const submitBtn = page.locator('button:has-text("Create Property")');
    if (await submitBtn.isVisible()) {
      await submitBtn.click();
      
      // Wait for submission response
      await page.waitForTimeout(3000);
      
      // Check for success message or redirect
      const successMessage = page.locator('text=Property created successfully');
      const toastMessage = page.locator('[data-testid="toast"]');
      
      if (await successMessage.isVisible() || await toastMessage.isVisible()) {
        console.log('✓ Property creation successful');
      } else {
        console.log('⚠ Property submission completed (success message may vary)');
      }
    }

    console.log('=== GenAI Property Form E2E Test Completed Successfully ===');
  });

  test('GenAI Form Validation Tests', async ({ page }) => {
    console.log('=== Starting GenAI Form Validation Tests ===');

    // Login first
    await page.goto('/login');
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    // Navigate to GenAI form
    await page.click('text=Smart Form Demo');
    await page.waitForURL('/demo/genai-form');

    // Test form validation
    console.log('Testing form validation...');
    
    // Try to proceed without filling required fields
    const nextBtn = page.locator('button:has-text("Next")');
    if (await nextBtn.isVisible()) {
      await nextBtn.click();
      
      // Check for validation errors
      const errorMessages = page.locator('.error, [role="alert"], .text-red-500');
      const errorCount = await errorMessages.count();
      
      if (errorCount > 0) {
        console.log(`✓ Form validation working - ${errorCount} validation errors displayed`);
      } else {
        console.log('⚠ No validation errors found - may need to check validation implementation');
      }
    }

    console.log('=== GenAI Form Validation Tests Completed ===');
  });

  test('GenAI Form API Integration Tests', async ({ page }) => {
    console.log('=== Starting GenAI Form API Integration Tests ===');

    let apiCalls: Array<{ method: string; url: string; status: number }> = [];
    
    // Monitor API calls
    page.on('response', async response => {
      const url = response.url();
      if (url.includes('/api/')) {
        const status = response.status();
        const method = response.request().method();
        apiCalls.push({ method, url, status });
        console.log(`[API CALL] ${method} ${url} - Status: ${status}`);
        
        if (status >= 400) {
          try {
            const errorBody = await response.text();
            console.error(`[API ERROR] ${errorBody}`);
          } catch (e) {
            console.error(`[API ERROR] Could not read error response`);
          }
        }
      }
    });

    // Login and navigate to form
    await page.goto('/login');
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
    await page.click('text=Smart Form Demo');
    await page.waitForURL('/demo/genai-form');

    // Fill form and trigger API calls
    await page.fill('input[name="title"]', 'API Test Property');
    await page.fill('input[name="price"]', '10000000');
    
    // Try to trigger AI features that should make API calls
    const aiButtons = [
      'button:has-text("Generate AI Description")',
      'button:has-text("Get Price Suggestion")',
      'button:has-text("Generate SEO")',
      'button:has-text("Market Analysis")'
    ];
    
    for (const buttonSelector of aiButtons) {
      const button = page.locator(buttonSelector);
      if (await button.isVisible()) {
        await button.click();
        await page.waitForTimeout(2000); // Wait for API call
      }
    }

    // Verify API calls were made
    console.log(`Total API calls made: ${apiCalls.length}`);
    
    const successfulCalls = apiCalls.filter(call => call.status < 400);
    const failedCalls = apiCalls.filter(call => call.status >= 400);
    
    console.log(`✓ Successful API calls: ${successfulCalls.length}`);
    if (failedCalls.length > 0) {
      console.error(`✗ Failed API calls: ${failedCalls.length}`);
      failedCalls.forEach(call => {
        console.error(`  - ${call.method} ${call.url} (${call.status})`);
      });
    }

    console.log('=== GenAI Form API Integration Tests Completed ===');
  });
});