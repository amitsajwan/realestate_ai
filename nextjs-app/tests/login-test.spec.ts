import { test, expect } from '@playwright/test';

test.describe('Step 2: Login Test', () => {
  test('should successfully login with registered user', async ({ page }) => {
    // Use our previously registered test user
    await page.goto('/login');
    console.log('Current URL:', page.url());
    await page.waitForLoadState('networkidle');
    
    // Use our known test user credentials
    const testEmail = 'testuser@example.com';
    const testPassword = 'P@ssw0rd!2023';
    console.log('Logging in with email:', testEmail);
    
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);
    console.log('Using password:', testPassword);
    
    // Log request details
    await page.route('**', async route => {
      const request = route.request();
      const method = request.method();
      const url = request.url();
      console.log(`Network request: ${method} ${url}`);
      
      // Log detailed info for login requests
      if (url.includes('/api/v1/auth/login') && method === 'POST') {
        const postData = request.postData();
        console.log('Login request data:', postData);
      }
      
      // Continue with the request
      await route.continue();
    });
    
    // Set up response logging
    page.on('response', async response => {
      const url = response.url();
      const status = response.status();
      
      if (url.includes('/api/v1/auth')) {
        console.log(`Response: ${response.request().method()} ${url} - Status: ${status}`);
        
        if (status !== 200 && status !== 201) {
          try {
            const text = await response.text();
            console.log(`Error response body: ${text}`);
          } catch (e) {
            console.log('Could not get response body:');
          }
        }
      }
    });
    
    console.log('Attempting to login with:', testEmail);
    
    // Submit login
    await page.click('button[type="submit"]');
    
    // Wait for response
    await page.waitForTimeout(5000);
    
    // Check network requests
    console.log('Checking network requests for registration and login...');
    
    console.log('After login attempt, current URL:', page.url());
    
    // Check for error messages
    const loginErrorMessages = await page.locator('[role="alert"], .text-red-600, .error').allTextContents();
    console.log('Login error messages:', loginErrorMessages);
    
    // Check if we're redirected away from login page
    const currentUrl = page.url();
    const isStillOnLogin = currentUrl.includes('/login');
    
    if (!isStillOnLogin) {
      console.log('✅ Successfully logged in and redirected to:', currentUrl);
    } else {
      console.log('❌ Still on login page after login attempt');
      
      // Check if there are any validation errors
      const allErrors = await page.locator('text=/error|Error|invalid|Invalid/i').allTextContents();
      console.log('All potential error texts:', allErrors);
      
      if (loginErrorMessages.length > 0) {
        console.log('Login failed with errors:', loginErrorMessages);
      }
    }
  });
});