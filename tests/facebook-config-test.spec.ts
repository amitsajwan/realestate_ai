import { test, expect } from '@playwright/test';

test.describe('Facebook Configuration API Test', () => {
  test('Test Facebook configuration validation endpoint', async ({ page }) => {
    // Test the API endpoint directly
    const response = await page.request.post('http://localhost:8003/api/facebook/test-config', {
      data: {
        app_id: 'test123',
        app_secret: 'test456',
        page_id: 'test789'
      }
    });

    expect(response.status()).toBe(200);
    const responseData = await response.json();
    expect(responseData.success).toBe(false);
    expect(responseData.error).toContain('Invalid App ID or App Secret');
  });

  test('Test Facebook configuration with realistic format', async ({ page }) => {
    // Test with realistic Facebook App ID format
    const response = await page.request.post('http://localhost:8003/api/facebook/test-config', {
      data: {
        app_id: '123456789012345',
        app_secret: 'abcdef123456789abcdef123456789ab',
        page_id: '987654321098765'
      }
    });

    expect(response.status()).toBe(200);
    const responseData = await response.json();
    expect(responseData.success).toBe(false);
    expect(responseData.error).toContain('Invalid App ID or App Secret');
  });

  test('Test Facebook configuration without page_id', async ({ page }) => {
    // Test without page_id (optional parameter)
    const response = await page.request.post('http://localhost:8003/api/facebook/test-config', {
      data: {
        app_id: 'test123',
        app_secret: 'test456'
      }
    });

    expect(response.status()).toBe(200);
    const responseData = await response.json();
    expect(responseData.success).toBe(false);
    expect(responseData.error).toContain('Invalid App ID or App Secret');
  });

  test('Test Facebook configuration with missing parameters', async ({ page }) => {
    // Test with missing app_secret
    const response = await page.request.post('http://localhost:8003/api/facebook/test-config', {
      data: {
        app_id: 'test123'
      }
    });

    expect(response.status()).toBe(200);
    const responseData = await response.json();
    expect(responseData.success).toBe(false);
    expect(responseData.error).toContain('App ID and App Secret are required');
  });
});
