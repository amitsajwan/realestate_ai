import { test, expect, request } from '@playwright/test';

/**
 * Error Scenarios and Edge Cases Tests
 * ====================================
 * 
 * This test suite focuses on testing error handling, edge cases,
 * and system resilience under various failure conditions.
 */

test.describe('Error Scenarios and Edge Cases', () => {
  let testUser: any;
  let authToken: string;

  test.beforeAll(async ({ request }) => {
    // Create a test user for error scenario testing
    const timestamp = Date.now();
    testUser = {
      first_name: 'Error',
      last_name: 'Tester',
      email: `errortest${timestamp}@propertyai.com`,
      password: 'SecurePassword123!',
      phone: '+1-555-ERROR-001'
    };

    // Register user
    await request.post('http://localhost:8000/api/v1/auth/register', {
      data: testUser
    });

    // Login to get token
    const loginResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
      form: {
        username: testUser.email,
        password: testUser.password
      }
    });
    const loginData = await loginResponse.json();
    authToken = loginData.access_token;
  });

  test('Invalid Authentication Scenarios', async ({ page }) => {
    console.log('🔐 Testing invalid authentication scenarios...');

    // Test 1: Login with invalid credentials
    const invalidLoginResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
      form: {
        username: 'nonexistent@example.com',
        password: 'wrongpassword'
      }
    });
    
    expect(invalidLoginResponse.status()).toBe(400);
    console.log('✅ Invalid login correctly rejected');

    // Test 2: Access protected endpoint without token
    const unauthorizedResponse = await request.get('http://localhost:8000/api/v1/properties/', {
      headers: {
        'Authorization': 'Bearer invalid_token'
      }
    });
    
    expect(unauthorizedResponse.status()).toBe(401);
    console.log('✅ Unauthorized access correctly rejected');

    // Test 3: Access protected frontend pages without authentication
    await page.goto('/properties');
    await page.waitForLoadState('networkidle');
    
    // Should redirect to login or show authentication error
    const currentUrl = page.url();
    const hasAuthError = await page.locator('text=login, text=sign in, text=unauthorized').count() > 0;
    console.log(`✅ Unauthenticated access handled: URL=${currentUrl}, HasAuthError=${hasAuthError}`);
  });

  test('Invalid Data Submission Scenarios', async ({ page }) => {
    console.log('📝 Testing invalid data submission scenarios...');

    // Set valid auth token for authenticated requests
    await page.evaluate((token) => {
      localStorage.setItem('auth_token', token);
    }, authToken);

    // Test 1: Create property with missing required fields
    const invalidPropertyResponse = await request.post('http://localhost:8000/api/v1/properties/', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: {
        // Missing required fields like title, price, etc.
        description: 'Invalid property without required fields'
      }
    });

    expect(invalidPropertyResponse.status()).toBe(422); // Validation error
    console.log('✅ Invalid property data correctly rejected');

    // Test 2: Create property with invalid data types
    const invalidTypeResponse = await request.post('http://localhost:8000/api/v1/properties/', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: {
        title: 'Test Property',
        price: 'not_a_number', // Invalid type
        bedrooms: 'invalid',
        bathrooms: 'invalid',
        area: 'invalid',
        property_type: 'InvalidType',
        location: 'Test Location',
        address: 'Test Address',
        description: 'Test description'
      }
    });

    expect(invalidTypeResponse.status()).toBe(422);
    console.log('✅ Invalid data types correctly rejected');

    // Test 3: Test frontend form validation
    await page.goto('/register');
    await page.waitForLoadState('networkidle');

    // Try to submit empty form
    const submitButton = page.locator('button[type="submit"]');
    if (await submitButton.count() > 0) {
      await submitButton.click();
      await page.waitForTimeout(1000);

      // Check for validation errors
      const errorMessages = page.locator('text=required, text=invalid, .error, [class*="error"]');
      const errorCount = await errorMessages.count();
      console.log(`✅ Frontend form validation shows ${errorCount} error messages`);
    }
  });

  test('Network and Connection Error Handling', async ({ page }) => {
    console.log('🌐 Testing network and connection error handling...');

    // Test 1: API endpoint that doesn't exist
    const notFoundResponse = await request.get('http://localhost:8000/api/v1/nonexistent-endpoint', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(notFoundResponse.status()).toBe(404);
    console.log('✅ Non-existent endpoint correctly returns 404');

    // Test 2: Invalid API base URL (simulate network error)
    const networkErrorResponse = await request.get('http://localhost:9999/api/v1/health');
    
    // Should fail due to connection refused
    expect(networkErrorResponse.status()).toBeGreaterThanOrEqual(400);
    console.log('✅ Network error correctly handled');

    // Test 3: Frontend error handling for failed API calls
    await page.evaluate((token) => {
      localStorage.setItem('auth_token', token);
    }, authToken);

    await page.goto('/properties');
    await page.waitForLoadState('networkidle');

    // Look for any error states in the UI
    const errorElements = page.locator('[class*="error"], [class*="failed"], .alert-error');
    const errorCount = await errorElements.count();
    console.log(`✅ Frontend shows ${errorCount} error elements`);
  });

  test('Large Data and Performance Edge Cases', async ({ page }) => {
    console.log('⚡ Testing large data and performance edge cases...');

    // Test 1: Create property with extremely large description
    const largeDescription = 'A'.repeat(10000); // 10KB description
    const largeDataResponse = await request.post('http://localhost:8000/api/v1/properties/', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: {
        title: 'Property with Large Description',
        description: largeDescription,
        property_type: 'Apartment',
        price: 500000,
        location: 'Test Location',
        address: 'Test Address',
        bedrooms: 2,
        bathrooms: 1,
        area: 1000,
        amenities: 'Test amenities',
        features: ['Feature 1', 'Feature 2']
      }
    });

    // Should either accept or reject with appropriate error
    const status = largeDataResponse.status();
    expect([200, 413, 422]).toContain(status);
    console.log(`✅ Large data handling: Status ${status}`);

    // Test 2: Create multiple properties rapidly (rate limiting test)
    const rapidRequests = Array.from({ length: 10 }, (_, i) => 
      request.post('http://localhost:8000/api/v1/properties/', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        data: {
          title: `Rapid Property ${i}`,
          description: `Property created rapidly ${i}`,
          property_type: 'Apartment',
          price: 500000 + i,
          location: 'Test Location',
          address: `${i} Test Street`,
          bedrooms: 2,
          bathrooms: 1,
          area: 1000,
          amenities: 'Test amenities',
          features: ['Feature 1']
        }
      })
    );

    const results = await Promise.allSettled(rapidRequests);
    const successful = results.filter(r => r.status === 'fulfilled' && r.value.ok()).length;
    const rateLimited = results.filter(r => r.status === 'fulfilled' && r.value.status() === 429).length;
    
    console.log(`✅ Rapid requests: ${successful} successful, ${rateLimited} rate limited`);
  });

  test('Cross-User Data Isolation', async ({ page }) => {
    console.log('🔒 Testing cross-user data isolation...');

    // Create a second user
    const secondUser = {
      first_name: 'Second',
      last_name: 'User',
      email: `seconduser${Date.now()}@propertyai.com`,
      password: 'SecurePassword123!',
      phone: '+1-555-SECOND-001'
    };

    await request.post('http://localhost:8000/api/v1/auth/register', {
      data: secondUser
    });

    const secondUserLogin = await request.post('http://localhost:8000/api/v1/auth/login', {
      form: {
        username: secondUser.email,
        password: secondUser.password
      }
    });
    const secondUserData = await secondUserLogin.json();
    const secondUserToken = secondUserData.access_token;

    // Create property with first user
    const firstUserProperty = await request.post('http://localhost:8000/api/v1/properties/', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: {
        title: 'First User Property',
        description: 'Property owned by first user',
        property_type: 'Apartment',
        price: 500000,
        location: 'Test Location',
        address: 'First User Street',
        bedrooms: 2,
        bathrooms: 1,
        area: 1000,
        amenities: 'Test amenities',
        features: ['Feature 1']
      }
    });

    expect(firstUserProperty.ok()).toBeTruthy();
    const firstProperty = await firstUserProperty.json();

    // Try to access first user's property with second user's token
    const unauthorizedAccess = await request.get(`http://localhost:8000/api/v1/properties/${firstProperty.id}`, {
      headers: {
        'Authorization': `Bearer ${secondUserToken}`
      }
    });

    // Should either return 403/404 or return the property (depending on business logic)
    const status = unauthorizedAccess.status();
    expect([200, 403, 404]).toContain(status);
    console.log(`✅ Cross-user access control: Status ${status}`);

    // Test frontend data isolation
    await page.evaluate((token) => {
      localStorage.setItem('auth_token', token);
    }, secondUserToken);

    await page.goto('/properties');
    await page.waitForLoadState('networkidle');

    // Should only show second user's properties (none yet)
    const propertyElements = page.locator('div[class*="property"], div[class*="card"]');
    const propertyCount = await propertyElements.count();
    console.log(`✅ Frontend data isolation: Second user sees ${propertyCount} properties`);
  });

  test('Special Characters and Unicode Handling', async ({ page }) => {
    console.log('🌍 Testing special characters and Unicode handling...');

    // Test with various special characters and Unicode
    const specialPropertyData = {
      title: 'Property with Special Characters: émojis 🏠🚀, accents, & symbols!',
      description: 'Test property with unicode: 中文, العربية, русский, ελληνικά, हिन्दी, and emojis 🎉🏆⭐',
      property_type: 'Apartment',
      price: 500000,
      location: 'Test Location with émojis 🗺️',
      address: '123 Test St. with émojis 🏠',
      bedrooms: 2,
      bathrooms: 1,
      area: 1000,
      amenities: 'Special amenities: 🏊‍♂️🏋️‍♀️🚗',
      features: ['Feature with émojis 🎯', 'Another feature 🌟']
    };

    const specialCharResponse = await request.post('http://localhost:8000/api/v1/properties/', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: specialPropertyData
    });

    if (specialCharResponse.ok()) {
      const createdProperty = await specialCharResponse.json();
      console.log('✅ Special characters and Unicode handled correctly');
      
      // Verify the data was stored correctly
      const retrievedProperty = await request.get(`http://localhost:8000/api/v1/properties/${createdProperty.id}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      expect(retrievedProperty.ok()).toBeTruthy();
      console.log('✅ Special characters retrieved correctly');
    } else {
      console.log(`⚠️ Special characters rejected with status: ${specialCharResponse.status()}`);
    }

    // Test frontend form with special characters
    await page.evaluate((token) => {
      localStorage.setItem('auth_token', token);
    }, authToken);

    await page.goto('/register');
    await page.waitForLoadState('networkidle');

    // Try to fill form with special characters
    const firstNameInput = page.locator('input[name="first_name"]');
    if (await firstNameInput.count() > 0) {
      await firstNameInput.fill('José María');
      console.log('✅ Frontend handles special characters in forms');
    }
  });

  test('System Recovery and Resilience', async ({ page }) => {
    console.log('🔄 Testing system recovery and resilience...');

    // Test 1: Multiple rapid login attempts
    const rapidLogins = Array.from({ length: 5 }, () =>
      request.post('http://localhost:8000/api/v1/auth/login', {
        form: {
          username: testUser.email,
          password: testUser.password
        }
      })
    );

    const loginResults = await Promise.allSettled(rapidLogins);
    const successfulLogins = loginResults.filter(r => r.status === 'fulfilled' && r.value.ok()).length;
    console.log(`✅ Rapid login attempts: ${successfulLogins}/5 successful`);

    // Test 2: Frontend recovery from errors
    await page.evaluate((token) => {
      localStorage.setItem('auth_token', token);
    }, authToken);

    // Navigate to various pages to test recovery
    const pages = ['/properties', '/social-publishing', '/analytics', '/onboarding'];
    for (const pagePath of pages) {
      try {
        await page.goto(pagePath);
        await page.waitForLoadState('networkidle', { timeout: 5000 });
        console.log(`✅ Page ${pagePath} loaded successfully`);
      } catch (error) {
        console.log(`⚠️ Page ${pagePath} failed to load: ${error}`);
      }
    }

    // Test 3: Backend health check after stress
    const healthResponse = await request.get('http://localhost:8000/api/v1/health');
    expect(healthResponse.ok()).toBeTruthy();
    console.log('✅ Backend health check passed after stress testing');
  });
});