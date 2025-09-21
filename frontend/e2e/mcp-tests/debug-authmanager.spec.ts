import { test, expect } from '@playwright/test';

/**
 * Debug AuthManager Initialization Issues
 * ======================================
 */

test.describe('Debug AuthManager Issues', () => {
  
  test('Check AuthManager initialization in browser', async ({ page }) => {
    
    console.log('🔍 Debugging AuthManager initialization...');
    
    const errors: string[] = [];
    const logs: string[] = [];
    
    // Capture all console messages
    page.on('console', msg => {
      logs.push(`${msg.type()}: ${msg.text()}`);
      if (msg.type() === 'error') {
        errors.push(msg.text());
        console.log(`❌ Error: ${msg.text()}`);
      }
    });
    
    // Go to login page
    await page.goto('/login');
    
    // Wait for initialization attempts
    await page.waitForTimeout(5000);
    
    console.log(`📊 Total logs: ${logs.length}`);
    console.log(`📊 Total errors: ${errors.length}`);
    
    // Check if AuthManager is available
    const authManagerInfo = await page.evaluate(() => {
      return {
        authManagerExists: typeof window !== 'undefined' && 'authManager' in window,
        authManagerType: typeof (window as any).authManager,
        authManagerMethods: typeof (window as any).authManager === 'object' ? 
          Object.getOwnPropertyNames((window as any).authManager) : [],
        localStorage: typeof window !== 'undefined' ? Object.keys(window.localStorage) : [],
        sessionStorage: typeof window !== 'undefined' ? Object.keys(window.sessionStorage) : []
      };
    });
    
    console.log('🔐 AuthManager Info:', JSON.stringify(authManagerInfo, null, 2));
    
    // Check for specific initialization messages
    const initMessages = logs.filter(log => 
      log.includes('AuthManager') || 
      log.includes('auth') || 
      log.includes('init')
    );
    
    console.log('🔧 AuthManager Messages:');
    initMessages.forEach(msg => console.log(`   ${msg}`));
    
    // Check if forms are eventually visible
    const emailInput = page.locator('input[name="email"]');
    const emailVisible = await emailInput.isVisible();
    console.log(`📧 Email input visible: ${emailVisible}`);
    
    // Wait longer to see if form eventually loads
    await page.waitForTimeout(10000);
    
    const emailVisibleAfterWait = await emailInput.isVisible();
    console.log(`📧 Email input visible after 15 seconds: ${emailVisibleAfterWait}`);
    
    // Check page source for clues
    const pageContent = await page.content();
    const hasAuthManager = pageContent.includes('AuthManager');
    const hasLoading = pageContent.includes('Loading');
    
    console.log(`📄 Page contains "AuthManager": ${hasAuthManager}`);
    console.log(`📄 Page contains "Loading": ${hasLoading}`);
    
    // Take screenshot
    await page.screenshot({ path: 'debug-authmanager.png' });
    console.log('📸 Screenshot saved: debug-authmanager.png');
  });

  test('Test AuthManager API calls directly', async ({ page }) => {
    
    console.log('🔍 Testing AuthManager API calls...');
    
    // Test the API endpoints that AuthManager would call
    const apiTests = [
      { name: 'Health Check', url: 'http://localhost:8000/api/v1/health' },
      { name: 'Current User (no token)', url: 'http://localhost:8000/api/v1/auth/me' },
      { name: 'Login Endpoint', url: 'http://localhost:8000/api/v1/auth/login' }
    ];
    
    for (const test of apiTests) {
      try {
        const response = await page.request.get(test.url);
        console.log(`🔗 ${test.name}: ${response.status()}`);
        
        if (response.status() !== 200) {
          const text = await response.text();
          console.log(`   Response: ${text.substring(0, 100)}...`);
        }
      } catch (error) {
        console.log(`❌ ${test.name}: Error - ${error}`);
      }
    }
    
    // Test POST to login endpoint
    try {
      const loginResponse = await page.request.post('http://localhost:8000/api/v1/auth/login', {
        form: {
          username: 'test@example.com',
          password: 'testpassword'
        }
      });
      console.log(`🔐 Login POST: ${loginResponse.status()}`);
      
      const loginText = await loginResponse.text();
      console.log(`   Response: ${loginText.substring(0, 100)}...`);
    } catch (error) {
      console.log(`❌ Login POST: Error - ${error}`);
    }
  });
});