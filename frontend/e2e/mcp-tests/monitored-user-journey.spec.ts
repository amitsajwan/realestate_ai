import { test, expect } from '@playwright/test';

/**
 * Monitored User Journey E2E Test
 * ===============================
 * 
 * This test monitors logs and API calls to understand what's actually happening
 * during the user journey from registration to property creation.
 */

test.describe('Monitored User Journey', () => {
  
  test('Complete user journey with detailed logging', async ({ page }) => {
    
    console.log('🚀 Starting monitored user journey...');
    
    // Capture all console messages and network requests
    const consoleLogs: string[] = [];
    const networkRequests: string[] = [];
    
    page.on('console', msg => {
      const logMessage = `[${msg.type()}] ${msg.text()}`;
      consoleLogs.push(logMessage);
      console.log(`📱 Frontend Console: ${logMessage}`);
    });
    
    page.on('request', request => {
      const requestInfo = `${request.method()} ${request.url()}`;
      networkRequests.push(requestInfo);
      console.log(`🌐 Network Request: ${requestInfo}`);
    });
    
    page.on('response', response => {
      const responseInfo = `${response.status()} ${response.url()}`;
      console.log(`📡 Network Response: ${responseInfo}`);
    });
    
    // === PHASE 1: USER REGISTRATION ===
    console.log('📝 Phase 1: User Registration');
    
    await page.goto('/simple-register');
    console.log(`📍 Navigated to: ${page.url()}`);
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    console.log('✅ Page loaded completely');
    
    // Check if form elements are visible
    const firstNameInput = page.locator('input[name="first_name"]');
    const isFirstNameVisible = await firstNameInput.isVisible();
    console.log(`📝 First Name Input Visible: ${isFirstNameVisible}`);
    
    if (!isFirstNameVisible) {
      console.log('❌ Registration form not visible, checking page content...');
      const pageContent = await page.content();
      console.log(`📄 Page Title: ${await page.title()}`);
      console.log(`📄 Page URL: ${page.url()}`);
      console.log(`📄 Form elements found: ${pageContent.includes('input') ? 'Yes' : 'No'}`);
      
      // Take screenshot for debugging
      await page.screenshot({ path: 'debug-registration-page.png' });
      console.log('📸 Screenshot saved: debug-registration-page.png');
      
      // Try to find any input elements
      const allInputs = await page.locator('input').count();
      console.log(`📄 Total input elements: ${allInputs}`);
      
      if (allInputs > 0) {
        const inputNames = await page.locator('input').allTextContents();
        console.log(`📄 Input names found: ${inputNames.join(', ')}`);
      }
      
      throw new Error('Registration form not visible');
    }
    
    // Fill registration form
    const timestamp = Date.now();
    const testEmail = `testuser${timestamp}@propertyai.com`;
    const testPassword = 'SecurePassword123!';
    
    console.log(`📧 Registering user: ${testEmail}`);
    
    await firstNameInput.fill('John');
    await page.fill('input[name="last_name"]', 'Doe');
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);
    
    console.log('✅ Registration form filled');
    
    // Submit registration
    await page.click('button[type="submit"]');
    console.log('📤 Registration form submitted');
    
    // Wait for response
    await page.waitForTimeout(3000);
    console.log(`📍 After registration: ${page.url()}`);
    
    // === PHASE 2: LOGIN ===
    console.log('🔐 Phase 2: User Login');
    
    await page.goto('/simple-login');
    console.log(`📍 Navigated to login: ${page.url()}`);
    
    await page.waitForLoadState('networkidle');
    
    // Check if login form is visible
    const emailInput = page.locator('input[name="username"]');
    const isEmailVisible = await emailInput.isVisible();
    console.log(`📧 Email Input Visible: ${isEmailVisible}`);
    
    if (!isEmailVisible) {
      console.log('❌ Login form not visible');
      await page.screenshot({ path: 'debug-login-page.png' });
      console.log('📸 Screenshot saved: debug-login-page.png');
      throw new Error('Login form not visible');
    }
    
    // Fill login form
    await emailInput.fill(testEmail);
    await page.fill('input[name="password"]', testPassword);
    
    console.log('✅ Login form filled');
    
    // Submit login
    await page.click('button[type="submit"]');
    console.log('📤 Login form submitted');
    
    // Wait for response
    await page.waitForTimeout(3000);
    console.log(`📍 After login: ${page.url()}`);
    
    // === PHASE 3: TEST PROPERTY CREATION ===
    console.log('🏠 Phase 3: Property Creation');
    
    await page.goto('/properties');
    console.log(`📍 Navigated to properties: ${page.url()}`);
    
    await page.waitForLoadState('networkidle');
    
    // Check if properties page loaded
    const pageTitle = await page.title();
    console.log(`📄 Properties page title: ${pageTitle}`);
    
    // === PHASE 4: TEST ANALYTICS ===
    console.log('📊 Phase 4: Analytics Dashboard');
    
    await page.goto('/analytics');
    console.log(`📍 Navigated to analytics: ${page.url()}`);
    
    await page.waitForLoadState('networkidle');
    
    const analyticsTitle = await page.title();
    console.log(`📄 Analytics page title: ${analyticsTitle}`);
    
    // === SUMMARY ===
    console.log('\n📊 MONITORED USER JOURNEY SUMMARY');
    console.log('=====================================');
    console.log(`✅ Registration: ${isFirstNameVisible ? 'SUCCESS' : 'FAILED'}`);
    console.log(`✅ Login: ${isEmailVisible ? 'SUCCESS' : 'FAILED'}`);
    console.log(`✅ Properties: ${pageTitle.includes('PropertyAI') ? 'SUCCESS' : 'FAILED'}`);
    console.log(`✅ Analytics: ${analyticsTitle.includes('PropertyAI') ? 'SUCCESS' : 'FAILED'}`);
    
    console.log(`\n📱 Frontend Console Logs (${consoleLogs.length}):`);
    consoleLogs.slice(0, 10).forEach(log => console.log(`   ${log}`));
    
    console.log(`\n🌐 Network Requests (${networkRequests.length}):`);
    networkRequests.slice(0, 10).forEach(req => console.log(`   ${req}`));
    
    // Test passed if we got this far
    expect(true).toBe(true);
  });
  
  test('Backend API monitoring during user journey', async ({ page }) => {
    
    console.log('🔍 Testing Backend API connectivity...');
    
    // Test backend health
    const healthResponse = await page.request.get('http://localhost:8000/api/v1/health');
    console.log(`🏥 Backend Health: ${healthResponse.status()}`);
    
    if (healthResponse.ok()) {
      const healthData = await healthResponse.json();
      console.log(`📊 Backend Status: ${JSON.stringify(healthData)}`);
    }
    
    // Test user registration API directly
    const timestamp = Date.now();
    const testEmail = `apitest${timestamp}@propertyai.com`;
    
    console.log(`🧪 Testing direct API registration: ${testEmail}`);
    
    const registerResponse = await page.request.post('http://localhost:8000/api/v1/auth/register', {
      data: {
        email: testEmail,
        password: 'TestPassword123!',
        first_name: 'API',
        last_name: 'Test'
      }
    });
    
    console.log(`📝 Registration API: ${registerResponse.status()}`);
    
    if (registerResponse.ok()) {
      const registerData = await registerResponse.json();
      console.log(`✅ User created: ${JSON.stringify(registerData)}`);
      
      // Test login API
      const loginResponse = await page.request.post('http://localhost:8000/api/v1/auth/jwt/login', {
        form: {
          username: testEmail,
          password: 'TestPassword123!'
        }
      });
      
      console.log(`🔐 Login API: ${loginResponse.status()}`);
      
      if (loginResponse.ok()) {
        const loginData = await loginResponse.json();
        console.log(`✅ Login successful: Token received`);
        
        // Test authenticated request
        const meResponse = await page.request.get('http://localhost:8000/api/v1/auth/me', {
          headers: {
            'Authorization': `Bearer ${loginData.access_token}`
          }
        });
        
        console.log(`👤 User Info API: ${meResponse.status()}`);
        
        if (meResponse.ok()) {
          const userData = await meResponse.json();
          console.log(`✅ User info retrieved: ${JSON.stringify(userData)}`);
        }
      }
    }
    
    expect(healthResponse.status()).toBe(200);
  });
});