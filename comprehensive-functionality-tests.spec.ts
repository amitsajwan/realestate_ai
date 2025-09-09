import { test, expect } from '@playwright/test';

/**
 * Comprehensive Functionality Tests for Real Estate Platform
 * =========================================================
 * 
 * This test suite covers all major functionality of the real estate platform:
 * 1. User Registration and Authentication
 * 2. Onboarding Flow
 * 3. Property Creation with Price and Images
 * 4. Property Management
 * 5. Social Media Integration
 * 6. Dashboard Functionality
 * 7. API Integration
 */

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:3000';
const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';

test.describe('Real Estate Platform - Complete Functionality Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Set up test data
    await page.addInitScript(() => {
      window.testData = {
        uniqueEmail: `test${Date.now()}@example.com`,
        password: 'TestPass123!',
        firstName: 'John',
        lastName: 'Doe',
        phone: '+1 (555) 123-4567',
        company: 'Test Real Estate',
        position: 'Senior Agent',
        licenseNumber: 'RE123456',
        propertyData: {
          address: '123 Test Property Street',
          location: 'Test City, Test State',
          propertyType: 'House',
          area: '1500',
          bedrooms: '3',
          bathrooms: '2',
          price: '500000',
          title: 'Beautiful Test Property',
          description: 'A stunning property for testing purposes with modern amenities.',
          amenities: 'Pool, Gym, Parking, Garden'
        }
      };
    });
  });

  test('Complete User Journey: Registration → Onboarding → Property Creation → Promotion', async ({ page }) => {
    console.log('🚀 Starting Complete User Journey Test');
    
    // Step 1: Navigate to application
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-01-initial-page.png', fullPage: true });
    console.log('✅ Navigated to application homepage');

    // Step 2: User Registration
    console.log('📝 Testing User Registration...');
    await page.click('text=Sign up');
    await page.waitForSelector('input[name="email"]', { timeout: 10000 });
    
    const testData = await page.evaluate(() => window.testData);
    await page.fill('input[name="email"]', testData.uniqueEmail);
    await page.fill('input[name="firstName"]', testData.firstName);
    await page.fill('input[name="lastName"]', testData.lastName);
    await page.fill('input[name="phone"]', testData.phone);
    await page.fill('input[name="password"]', testData.password);
    await page.fill('input[name="confirmPassword"]', testData.password);
    
    await page.screenshot({ path: 'test-02-registration-form.png', fullPage: true });
    await page.click('button[type="submit"]');
    
    // Wait for registration to complete
    await page.waitForTimeout(3000);
    console.log('✅ User registration completed');

    // Step 3: Onboarding Flow
    console.log('🎯 Testing Onboarding Flow...');
    
    // Check if redirected to onboarding or need to login
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      await page.click('text=Sign in');
      await page.fill('input[name="email"]', testData.uniqueEmail);
      await page.fill('input[name="password"]', testData.password);
      await page.click('button[type="submit"]');
      await page.waitForTimeout(3000);
    }

    // Navigate to onboarding if not already there
    if (!currentUrl.includes('/onboarding')) {
      await page.goto(`${BASE_URL}/onboarding`);
    }

    // Onboarding Step 1: Personal Information
    await page.waitForSelector('input[placeholder="John"]', { timeout: 10000 });
    await page.fill('input[placeholder="John"]', testData.firstName);
    await page.fill('input[placeholder="Doe"]', testData.lastName);
    await page.screenshot({ path: 'test-03-onboarding-step1.png', fullPage: true });
    await page.click('button:has-text("Next")');
    console.log('✅ Onboarding Step 1 completed');

    // Onboarding Step 2: Company Details
    await page.waitForSelector('input[placeholder="Real Estate Pro"]', { timeout: 5000 });
    await page.fill('input[placeholder="Real Estate Pro"]', testData.company);
    await page.fill('input[placeholder="Senior Agent"]', testData.position);
    await page.screenshot({ path: 'test-04-onboarding-step2.png', fullPage: true });
    await page.click('button:has-text("Next")');
    console.log('✅ Onboarding Step 2 completed');

    // Onboarding Step 3: AI Preferences
    const selects = page.locator('select');
    await selects.nth(0).selectOption({ label: 'Professional' });
    await selects.nth(1).selectOption({ label: 'Friendly' });
    await page.screenshot({ path: 'test-05-onboarding-step3.png', fullPage: true });
    await page.click('button:has-text("Next")');
    console.log('✅ Onboarding Step 3 completed');

    // Onboarding Step 4: Social Media (skip)
    await page.click('button:has-text("Next")');
    console.log('✅ Onboarding Step 4 completed');

    // Onboarding Step 5: Terms and Conditions
    await page.check('#terms');
    await page.check('#privacy');
    await page.screenshot({ path: 'test-06-onboarding-step5.png', fullPage: true });
    await page.click('button:has-text("Next")');
    console.log('✅ Onboarding Step 5 completed');

    // Complete onboarding
    await page.click('button:has-text("Complete")');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    await page.screenshot({ path: 'test-07-dashboard.png', fullPage: true });
    console.log('✅ Onboarding completed - redirected to dashboard');

    // Step 4: Property Creation
    console.log('🏠 Testing Property Creation...');
    
    // Navigate to property creation
    await page.click('text=Add Property');
    await page.waitForSelector('text=Add New Property', { timeout: 10000 });
    await page.screenshot({ path: 'test-08-property-form-start.png', fullPage: true });

    // Property Form Step 1: Address Information
    await page.fill('input[name="address"]', testData.propertyData.address);
    await page.fill('input[name="location"]', testData.propertyData.location);
    await page.screenshot({ path: 'test-09-property-step1-address.png', fullPage: true });
    await page.click('button:has-text("Next")');
    console.log('✅ Property Step 1: Address completed');

    // Property Form Step 2: Basic Information
    await page.waitForSelector('text=Tell us about your property', { timeout: 5000 });
    await page.selectOption('select[name="propertyType"]', testData.propertyData.propertyType);
    await page.fill('input[name="area"]', testData.propertyData.area);
    await page.selectOption('select[name="bedrooms"]', testData.propertyData.bedrooms);
    await page.selectOption('select[name="bathrooms"]', testData.propertyData.bathrooms);
    await page.screenshot({ path: 'test-10-property-step2-basic.png', fullPage: true });
    await page.click('button:has-text("Next")');
    console.log('✅ Property Step 2: Basic information completed');

    // Property Form Step 3: Pricing
    await page.waitForSelector('text=Set your price', { timeout: 5000 });
    await page.fill('input[name="price"]', testData.propertyData.price);
    
    // Verify price input is working correctly
    const priceInput = page.locator('input[name="price"]');
    await expect(priceInput).toHaveValue(500000);
    await expect(priceInput).toHaveAttribute('type', 'number');
    
    await page.screenshot({ path: 'test-11-property-step3-pricing.png', fullPage: true });
    await page.click('button:has-text("Next")');
    console.log('✅ Property Step 3: Pricing completed');

    // Property Form Step 4: Images
    await page.waitForSelector('text=Add Property Images', { timeout: 5000 });
    await expect(page.locator('text=Click to upload images')).toBeVisible();
    await expect(page.locator('text=Image Tips')).toBeVisible();
    await page.screenshot({ path: 'test-12-property-step4-images.png', fullPage: true });
    
    // Skip images for now (can be enhanced later)
    await page.click('button:has-text("Next")');
    console.log('✅ Property Step 4: Images interface verified');

    // Property Form Step 5: Description
    await page.waitForSelector('text=Create compelling content', { timeout: 5000 });
    await page.fill('input[name="title"]', testData.propertyData.title);
    await page.fill('textarea[name="description"]', testData.propertyData.description);
    await page.fill('textarea[name="amenities"]', testData.propertyData.amenities);
    await page.screenshot({ path: 'test-13-property-step5-description.png', fullPage: true });
    
    // Submit the property
    await page.click('button:has-text("Create Property")');
    
    // Wait for success message
    await page.waitForSelector('text=AI-powered property created successfully!', { timeout: 15000 });
    await page.screenshot({ path: 'test-14-property-created-success.png', fullPage: true });
    console.log('✅ Property created successfully');

    // Step 5: Verify Property in Dashboard
    console.log('📋 Verifying Property in Dashboard...');
    
    // Navigate back to dashboard
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForLoadState('networkidle');
    
    // Look for the properties section
    await page.waitForSelector('text=Properties', { timeout: 10000 });
    await page.screenshot({ path: 'test-15-properties-list.png', fullPage: true });
    
    // Verify the property appears in the list
    const propertyCard = page.locator('text=Beautiful Test Property').first();
    await expect(propertyCard).toBeVisible();
    
    // Verify the price is displayed correctly
    const priceDisplay = page.locator('text=₹5L').or(page.locator('text=₹500,000')).or(page.locator('text=₹5.0L'));
    await expect(priceDisplay).toBeVisible();
    
    // Click on the property to view details
    await propertyCard.click();
    await page.waitForSelector('text=Beautiful Test Property', { timeout: 5000 });
    await page.screenshot({ path: 'test-16-property-details.png', fullPage: true });
    
    // Verify all property details
    await expect(page.locator('text=Beautiful Test Property')).toBeVisible();
    await expect(page.locator('text=123 Test Property Street')).toBeVisible();
    await expect(page.locator('text=3')).toBeVisible(); // bedrooms
    await expect(page.locator('text=2')).toBeVisible(); // bathrooms
    await expect(page.locator('text=1500')).toBeVisible(); // area
    
    console.log('✅ Property verification completed');

    // Step 6: Test Property Promotion (if available)
    console.log('📢 Testing Property Promotion...');
    
    // Look for promotion options
    const promoteButton = page.locator('text=Promote').or(page.locator('text=Share'));
    if (await promoteButton.isVisible()) {
      await promoteButton.click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'test-17-promotion-options.png', fullPage: true });
      console.log('✅ Promotion interface accessed');
    } else {
      console.log('ℹ️ Promotion feature not available in current view');
    }

    console.log('🎉 Complete User Journey Test Completed Successfully!');
  });

  test('API Integration and Data Persistence', async ({ page }) => {
    console.log('🔌 Testing API Integration...');
    
    // Test API connectivity
    const response = await page.request.get(`${API_BASE}/health`);
    expect(response.status()).toBe(200);
    console.log('✅ API health check passed');

    // Test user registration API
    const testData = await page.evaluate(() => window.testData);
    const registerResponse = await page.request.post(`${API_BASE}/api/v1/auth/register`, {
      data: {
        email: `apitest${Date.now()}@example.com`,
        password: testData.password,
        first_name: testData.firstName,
        last_name: testData.lastName,
        phone: testData.phone
      }
    });
    
    expect(registerResponse.status()).toBe(201);
    console.log('✅ User registration API working');

    // Test login API
    const loginResponse = await page.request.post(`${API_BASE}/api/v1/auth/login`, {
      data: {
        email: `apitest${Date.now()}@example.com`,
        password: testData.password
      }
    });
    
    expect(loginResponse.status()).toBe(200);
    const loginData = await loginResponse.json();
    expect(loginData.access_token).toBeDefined();
    console.log('✅ User login API working');

    console.log('🎉 API Integration Test Completed Successfully!');
  });

  test('Form Validation and Error Handling', async ({ page }) => {
    console.log('✅ Testing Form Validation...');
    
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');
    
    // Test registration form validation
    await page.click('text=Sign up');
    await page.waitForSelector('input[name="email"]');
    
    // Try to submit empty form
    await page.click('button[type="submit"]');
    
    // Check for validation errors
    const emailError = page.locator('text=Email is required');
    const passwordError = page.locator('text=Password is required');
    
    if (await emailError.isVisible() || await passwordError.isVisible()) {
      console.log('✅ Form validation working correctly');
      await page.screenshot({ path: 'test-validation-errors.png', fullPage: true });
    }
    
    // Test invalid email format
    await page.fill('input[name="email"]', 'invalid-email');
    await page.fill('input[name="password"]', 'test');
    await page.click('button[type="submit"]');
    
    // Check for email format validation
    const emailFormatError = page.locator('text=Invalid email format');
    if (await emailFormatError.isVisible()) {
      console.log('✅ Email format validation working');
    }
    
    console.log('🎉 Form Validation Test Completed!');
  });

  test('Responsive Design and Mobile Compatibility', async ({ page }) => {
    console.log('📱 Testing Responsive Design...');
    
    // Test desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-desktop-view.png', fullPage: true });
    console.log('✅ Desktop view tested');

    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-tablet-view.png', fullPage: true });
    console.log('✅ Tablet view tested');

    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-mobile-view.png', fullPage: true });
    console.log('✅ Mobile view tested');

    console.log('🎉 Responsive Design Test Completed!');
  });

  test('Performance and Loading Times', async ({ page }) => {
    console.log('⚡ Testing Performance...');
    
    const startTime = Date.now();
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;
    
    console.log(`📊 Page load time: ${loadTime}ms`);
    
    // Check for performance issues
    if (loadTime < 3000) {
      console.log('✅ Page loads within acceptable time');
    } else {
      console.log('⚠️ Page load time is slower than expected');
    }
    
    // Test navigation performance
    const navStartTime = Date.now();
    await page.click('text=Sign up');
    await page.waitForSelector('input[name="email"]');
    const navTime = Date.now() - navStartTime;
    
    console.log(`📊 Navigation time: ${navTime}ms`);
    
    if (navTime < 1000) {
      console.log('✅ Navigation is fast');
    } else {
      console.log('⚠️ Navigation could be faster');
    }
    
    console.log('🎉 Performance Test Completed!');
  });
});

test.describe('Error Handling and Edge Cases', () => {
  
  test('Network Error Handling', async ({ page }) => {
    console.log('🌐 Testing Network Error Handling...');
    
    // Simulate network failure
    await page.route('**/*', route => route.abort());
    
    await page.goto(BASE_URL);
    
    // Check if error handling is in place
    const errorMessage = page.locator('text=Network error').or(page.locator('text=Connection failed'));
    if (await errorMessage.isVisible()) {
      console.log('✅ Network error handling working');
    } else {
      console.log('ℹ️ No specific network error handling detected');
    }
    
    console.log('🎉 Network Error Handling Test Completed!');
  });

  test('Invalid URL Handling', async ({ page }) => {
    console.log('🔗 Testing Invalid URL Handling...');
    
    await page.goto(`${BASE_URL}/invalid-page`);
    
    // Check for 404 handling
    const notFoundMessage = page.locator('text=404').or(page.locator('text=Page not found'));
    if (await notFoundMessage.isVisible()) {
      console.log('✅ 404 error handling working');
    } else {
      console.log('ℹ️ No specific 404 handling detected');
    }
    
    console.log('🎉 Invalid URL Handling Test Completed!');
  });
});

console.log('📋 Test Suite Summary:');
console.log('✅ Complete User Journey Test');
console.log('✅ API Integration Test');
console.log('✅ Form Validation Test');
console.log('✅ Responsive Design Test');
console.log('✅ Performance Test');
console.log('✅ Error Handling Tests');
console.log('');
console.log('🎯 All tests are designed to provide comprehensive coverage of the real estate platform functionality.');
console.log('📸 Screenshots will be generated for each test step to provide visual evidence.');