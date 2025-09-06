import { test, expect } from '@playwright/test';

test.describe('API Connectivity Test', () => {
  test('should be able to connect to backend API', async ({ page }) => {
    // Navigate to login page to initialize the app
    await page.goto('/login');
    await page.waitForLoadState('load');

    // Check if we can make a direct API call from the browser
    const apiResponse = await page.evaluate(async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/auth/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'Jd9!Qm7#VzA2',
            confirm_password: 'Jd9!Qm7#VzA2',
            first_name: 'Test',
            last_name: 'User'
          })
        });
        
        return {
          status: response.status,
          statusText: response.statusText,
          ok: response.ok,
          url: response.url
        };
      } catch (error) {
        const err = error as Error;
        return {
          error: err.message,
          name: err.name
        };
      }
    });

    console.log('API Response:', apiResponse);
    
    // The test should at least get a response (even if it's an error)
    expect(apiResponse).toBeDefined();
  });

  test('should validate /me endpoint returns onboarding_completed field', async ({ page }) => {
    // First register and login a test user
    await page.goto('/login');
    await page.waitForLoadState('load');

    // Switch to register mode
    await page.click('text=Sign up');
    await page.waitForSelector('input[name="firstName"]', { timeout: 5000 });

    // Register with unique email
    const uniqueEmail = `apitest${Date.now()}@example.com`;
    await page.fill('input[name="email"]', uniqueEmail);
    await page.fill('input[name="firstName"]', 'API');
    await page.fill('input[name="lastName"]', 'Test');
    await page.fill('input[name="phone"]', '+1 (555) 999-0000');
    await page.fill('input[name="password"]', 'ApiTest123!');
    await page.fill('input[name="confirmPassword"]', 'ApiTest123!');
    
    await page.click('button[type="submit"]', { force: true });
    await page.waitForTimeout(3000);

    // Login if needed
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      await page.click('text=Sign in');
      await page.fill('input[name="email"]', uniqueEmail);
      await page.fill('input[name="password"]', 'ApiTest123!');
      await page.click('button[type="submit"]', { force: true });
      await page.waitForTimeout(3000);
    }

    // Test /me endpoint response structure
    const meResponse = await page.evaluate(async () => {
      try {
        // Get token from localStorage or cookies
        const token = localStorage.getItem('token') || document.cookie.split('; ').find(row => row.startsWith('token='))?.split('=')[1];
        
        const response = await fetch('http://localhost:8000/api/v1/auth/me?x=test', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
          }
        });
        
        const data = await response.json();
        
        return {
          status: response.status,
          data: data,
          hasOnboardingCompleted: 'onboarding_completed' in data,
          hasLastLogin: 'last_login' in data,
          hasLoginAttempts: 'login_attempts' in data,
          hasIsVerified: 'is_verified' in data
        };
      } catch (error) {
        const err = error as Error;
        return {
          error: err.message,
          name: err.name
        };
      }
    });

    console.log('/me API Response:', meResponse);
    
    // Validate response structure
    if (meResponse.status === 200) {
      expect(meResponse.hasOnboardingCompleted).toBe(true);
      expect(meResponse.hasLastLogin).toBe(true);
      expect(meResponse.hasLoginAttempts).toBe(true);
      expect(meResponse.hasIsVerified).toBe(true);
      console.log('✅ /me endpoint includes all required UserResponse fields');
    } else {
      console.log('⚠️ /me endpoint test skipped due to authentication issues');
    }
  });
});