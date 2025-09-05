import { test, expect, Page, BrowserContext } from '@playwright/test';
import { faker } from '@faker-js/faker';

// Test configuration
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Mock Facebook OAuth responses
const mockFacebookUser = {
  id: '123456789',
  name: 'Test Facebook User',
  email: 'facebook.test@example.com',
  first_name: 'Test',
  last_name: 'User'
};

const mockFacebookToken = {
  access_token: 'mock_facebook_access_token',
  token_type: 'bearer',
  expires_in: 5183944
};

test.describe('Facebook Authentication', () => {
  let context: BrowserContext;
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    // Create a new context for each test to ensure isolation
    context = await browser.newContext();
    page = await context.newPage();
    
    // Mock Facebook API responses
    await page.route('**/oauth/access_token', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockFacebookToken)
      });
    });
    
    await page.route('**/me?fields=id,name,email,first_name,last_name', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockFacebookUser)
      });
    });
  });

  test.afterEach(async () => {
    await context.close();
  });

  test('should display Facebook login button on login page', async () => {
    await page.goto(`${BASE_URL}/login`);
    
    // Check that Facebook login button is visible
    const facebookButton = page.locator('button:has-text("Facebook")');
    await expect(facebookButton).toBeVisible();
    
    // Verify button styling and icon
    await expect(facebookButton).toHaveClass(/bg-white/);
    const facebookIcon = facebookButton.locator('svg');
    await expect(facebookIcon).toBeVisible();
  });

  test('should initiate Facebook OAuth flow when button is clicked', async () => {
    await page.goto(`${BASE_URL}/login`);
    
    // Mock the Facebook OAuth endpoint
    let oauthRequestMade = false;
    await page.route(`${API_BASE_URL}/auth/facebook/login`, async route => {
      oauthRequestMade = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          auth_url: 'https://www.facebook.com/v18.0/dialog/oauth?client_id=test&redirect_uri=test&scope=email,public_profile&response_type=code&state=test'
        })
      });
    });
    
    // Click Facebook login button
    const facebookButton = page.locator('button:has-text("Facebook")');
    await facebookButton.click();
    
    // Verify that the OAuth request was made
    await page.waitForTimeout(1000); // Give time for the request
    expect(oauthRequestMade).toBe(true);
  });

  test('should handle Facebook OAuth callback successfully', async () => {
    // Mock successful Facebook OAuth callback
    await page.route(`${API_BASE_URL}/api/v1/facebook/callback*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: `
          <html>
            <body>
              <script>
                window.opener.postMessage({
                  type: 'FACEBOOK_AUTH_SUCCESS',
                  user: ${JSON.stringify(mockFacebookUser)}
                }, '*');
                window.close();
              </script>
            </body>
          </html>
        `
      });
    });
    
    await page.goto(`${BASE_URL}/login`);
    
    // Simulate Facebook OAuth callback
    await page.evaluate(() => {
      window.postMessage({
        type: 'FACEBOOK_AUTH_SUCCESS',
        user: {
          id: '123456789',
          name: 'Test Facebook User',
          email: 'facebook.test@example.com'
        }
      }, '*');
    });
    
    // Should redirect to dashboard or onboarding
    await expect(page).toHaveURL(/\/(dashboard|onboarding)/);
  });

  test('should handle Facebook OAuth errors gracefully', async () => {
    await page.goto(`${BASE_URL}/login`);
    
    // Mock Facebook OAuth error
    await page.route(`${API_BASE_URL}/auth/facebook/login`, async route => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Facebook OAuth configuration error'
        })
      });
    });
    
    // Click Facebook login button
    const facebookButton = page.locator('button:has-text("Facebook")');
    await facebookButton.click();
    
    // Should show error message
    await expect(page.locator('text=Facebook login failed')).toBeVisible();
  });

  test('should work alongside email/password authentication', async () => {
    await page.goto(`${BASE_URL}/login`);
    
    // Verify both authentication methods are available
    const emailInput = page.locator('input[name="email"]');
    const passwordInput = page.locator('input[name="password"]');
    const loginButton = page.locator('button[type="submit"]:has-text("Sign in")');
    const facebookButton = page.locator('button:has-text("Facebook")');
    
    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    await expect(loginButton).toBeVisible();
    await expect(facebookButton).toBeVisible();
    
    // Verify separator between methods
    await expect(page.locator('text=Or continue with')).toBeVisible();
  });

  test('should handle existing user with Facebook login', async () => {
    // Mock API response for existing user
    await page.route(`${API_BASE_URL}/api/v1/facebook/callback*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: `
          <html>
            <body>
              <script>
                window.opener.postMessage({
                  type: 'FACEBOOK_AUTH_SUCCESS',
                  user: {
                    id: '123456789',
                    email: 'existing.user@example.com',
                    name: 'Existing User',
                    onboarding_completed: true
                  }
                }, '*');
                window.close();
              </script>
            </body>
          </html>
        `
      });
    });
    
    await page.goto(`${BASE_URL}/login`);
    
    // Simulate Facebook login for existing user
    await page.evaluate(() => {
      window.postMessage({
        type: 'FACEBOOK_AUTH_SUCCESS',
        user: {
          id: '123456789',
          email: 'existing.user@example.com',
          name: 'Existing User',
          onboarding_completed: true
        }
      }, '*');
    });
    
    // Should redirect to dashboard for existing user
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should handle new user with Facebook login', async () => {
    // Mock API response for new user
    await page.route(`${API_BASE_URL}/api/v1/facebook/callback*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: `
          <html>
            <body>
              <script>
                window.opener.postMessage({
                  type: 'FACEBOOK_AUTH_SUCCESS',
                  user: {
                    id: '987654321',
                    email: 'new.facebook.user@example.com',
                    name: 'New Facebook User',
                    onboarding_completed: false
                  }
                }, '*');
                window.close();
              </script>
            </body>
          </html>
        `
      });
    });
    
    await page.goto(`${BASE_URL}/login`);
    
    // Simulate Facebook login for new user
    await page.evaluate(() => {
      window.postMessage({
        type: 'FACEBOOK_AUTH_SUCCESS',
        user: {
          id: '987654321',
          email: 'new.facebook.user@example.com',
          name: 'New Facebook User',
          onboarding_completed: false
        }
      }, '*');
    });
    
    // Should redirect to onboarding for new user
    await expect(page).toHaveURL(/\/onboarding/);
  });

  test('should maintain session after Facebook login', async () => {
    // Mock successful Facebook login with token
    await page.route(`${API_BASE_URL}/api/v1/facebook/callback*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: `
          <html>
            <body>
              <script>
                // Simulate setting auth token in localStorage
                localStorage.setItem('auth_token', 'mock_jwt_token');
                window.opener.postMessage({
                  type: 'FACEBOOK_AUTH_SUCCESS',
                  user: ${JSON.stringify(mockFacebookUser)},
                  token: 'mock_jwt_token'
                }, '*');
                window.close();
              </script>
            </body>
          </html>
        `
      });
    });
    
    await page.goto(`${BASE_URL}/login`);
    
    // Simulate Facebook login
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock_jwt_token');
      window.postMessage({
        type: 'FACEBOOK_AUTH_SUCCESS',
        user: {
          id: '123456789',
          email: 'facebook.test@example.com',
          name: 'Test Facebook User'
        },
        token: 'mock_jwt_token'
      }, '*');
    });
    
    // Navigate to a protected route
    await page.goto(`${BASE_URL}/dashboard`);
    
    // Should remain authenticated
    await expect(page).toHaveURL(/\/dashboard/);
    
    // Verify auth token is stored
    const authToken = await page.evaluate(() => localStorage.getItem('auth_token'));
    expect(authToken).toBe('mock_jwt_token');
  });

  test('should handle Facebook login button loading state', async () => {
    await page.goto(`${BASE_URL}/login`);
    
    // Mock slow Facebook OAuth response
    await page.route(`${API_BASE_URL}/auth/facebook/login`, async route => {
      await new Promise(resolve => setTimeout(resolve, 2000)); // 2 second delay
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          auth_url: 'https://www.facebook.com/v18.0/dialog/oauth?client_id=test'
        })
      });
    });
    
    const facebookButton = page.locator('button:has-text("Facebook")');
    
    // Click Facebook login button
    await facebookButton.click();
    
    // Should show loading state
    await expect(facebookButton).toBeDisabled();
    
    // Wait for response
    await page.waitForTimeout(2500);
    
    // Button should be enabled again
    await expect(facebookButton).toBeEnabled();
  });

  test('should prevent multiple simultaneous Facebook login attempts', async () => {
    await page.goto(`${BASE_URL}/login`);
    
    let requestCount = 0;
    await page.route(`${API_BASE_URL}/auth/facebook/login`, async route => {
      requestCount++;
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          auth_url: 'https://www.facebook.com/v18.0/dialog/oauth?client_id=test'
        })
      });
    });
    
    const facebookButton = page.locator('button:has-text("Facebook")');
    
    // Click multiple times rapidly
    await facebookButton.click();
    await facebookButton.click();
    await facebookButton.click();
    
    // Wait for all requests to complete
    await page.waitForTimeout(2000);
    
    // Should only make one request
    expect(requestCount).toBe(1);
  });
});

test.describe('Facebook Authentication Integration', () => {
  test('should allow switching between email and Facebook login', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    
    // Start with email login
    const emailInput = page.locator('input[name="email"]');
    await emailInput.fill('test@example.com');
    
    // Switch to Facebook login
    const facebookButton = page.locator('button:has-text("Facebook")');
    await expect(facebookButton).toBeVisible();
    
    // Email input should still contain the value
    await expect(emailInput).toHaveValue('test@example.com');
    
    // Both methods should be available simultaneously
    await expect(emailInput).toBeVisible();
    await expect(facebookButton).toBeVisible();
  });

  test('should handle Facebook login when user already has email account', async ({ page }) => {
    // This test would require backend integration to properly test
    // account linking scenarios
    await page.goto(`${BASE_URL}/login`);
    
    // Mock scenario where Facebook email matches existing account
    await page.route(`${API_BASE_URL}/api/v1/facebook/callback*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: `
          <html>
            <body>
              <script>
                window.opener.postMessage({
                  type: 'FACEBOOK_AUTH_SUCCESS',
                  user: {
                    id: '123456789',
                    email: 'existing@example.com',
                    name: 'Existing User',
                    facebook_connected: true
                  }
                }, '*');
                window.close();
              </script>
            </body>
          </html>
        `
      });
    });
    
    // Simulate Facebook login
    await page.evaluate(() => {
      window.postMessage({
        type: 'FACEBOOK_AUTH_SUCCESS',
        user: {
          id: '123456789',
          email: 'existing@example.com',
          name: 'Existing User',
          facebook_connected: true
        }
      }, '*');
    });
    
    // Should successfully authenticate
    await expect(page).toHaveURL(/\/(dashboard|onboarding)/);
  });
});