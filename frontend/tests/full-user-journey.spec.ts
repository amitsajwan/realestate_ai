import { test, expect } from '@playwright/test';

test.describe('Complete User Journey', () => {
  test('Full User Journey: Register → Login → Onboarding → Add Property → Post Creation → Publishing → Agent Website', async ({ page }) => {
    // Set viewport for consistent screenshots
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    // Step 1: Navigate to registration page
    await page.goto('http://localhost:3000/register');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/01-register-page.png', fullPage: true });
    
    // Fill registration form
    await page.fill('input[name="email"]', 'testuser@example.com');
    await page.fill('input[name="password"]', 'TestPassword123!');
    await page.fill('input[name="firstName"]', 'Test');
    await page.fill('input[name="lastName"]', 'User');
    await page.screenshot({ path: 'screenshots/02-register-form-filled.png', fullPage: true });
    
    // Submit registration
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/03-register-success.png', fullPage: true });
    
    // Step 2: Login
    await page.goto('http://localhost:3000/login');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/04-login-page.png', fullPage: true });
    
    await page.fill('input[name="email"]', 'testuser@example.com');
    await page.fill('input[name="password"]', 'TestPassword123!');
    await page.screenshot({ path: 'screenshots/05-login-form-filled.png', fullPage: true });
    
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/06-login-success.png', fullPage: true });
    
    // Step 3: Agent Onboarding
    await page.goto('http://localhost:3000/onboarding');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/07-onboarding-page.png', fullPage: true });
    
    // Fill onboarding form
    await page.fill('input[name="name"]', 'Test Agent');
    await page.fill('input[name="email"]', 'testuser@example.com');
    await page.fill('input[name="phone"]', '+1234567890');
    await page.fill('input[name="company_name"]', 'Test Real Estate Agency');
    await page.fill('input[name="license_number"]', 'RE123456');
    await page.fill('textarea[name="bio"]', 'Experienced real estate agent specializing in luxury properties');
    await page.screenshot({ path: 'screenshots/08-onboarding-form-filled.png', fullPage: true });
    
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/09-onboarding-success.png', fullPage: true });
    
    // Step 4: Add Property
    await page.goto('http://localhost:3000/properties/add');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/10-add-property-page.png', fullPage: true });
    
    // Fill property form
    await page.fill('input[name="title"]', 'Luxury Villa with Pool');
    await page.fill('textarea[name="description"]', 'Beautiful luxury villa with modern amenities and private pool');
    await page.selectOption('select[name="property_type"]', 'house');
    await page.fill('input[name="price"]', '2500000');
    await page.fill('input[name="location"]', 'Beverly Hills, CA');
    await page.fill('input[name="bedrooms"]', '5');
    await page.fill('input[name="bathrooms"]', '4');
    await page.fill('input[name="area_sqft"]', '4000');
    await page.screenshot({ path: 'screenshots/11-property-form-filled.png', fullPage: true });
    
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/12-property-created.png', fullPage: true });
    
    // Step 5: Post Creation
    await page.goto('http://localhost:3000/posts/create');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/13-post-creation-page.png', fullPage: true });
    
    // Fill post creation form
    await page.fill('input[name="title"]', 'Luxury Villa Listing');
    await page.fill('textarea[name="content"]', 'Check out this amazing luxury villa with all modern amenities');
    await page.selectOption('select[name="property_id"]', '1'); // Assuming property ID 1
    await page.screenshot({ path: 'screenshots/14-post-form-filled.png', fullPage: true });
    
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/15-post-created.png', fullPage: true });
    
    // Step 6: Publishing
    await page.goto('http://localhost:3000/publishing');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/16-publishing-page.png', fullPage: true });
    
    // Select property and channels
    await page.selectOption('select[name="property_id"]', '1');
    await page.check('input[name="channels"][value="website"]');
    await page.check('input[name="channels"][value="facebook"]');
    await page.screenshot({ path: 'screenshots/17-publishing-form-filled.png', fullPage: true });
    
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/18-publishing-success.png', fullPage: true });
    
    // Step 7: Agent Website
    await page.goto('http://localhost:3000/agent/testuser');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/19-agent-website.png', fullPage: true });
    
    // Check if property is visible on agent website
    await expect(page.locator('text=Luxury Villa with Pool')).toBeVisible();
    await page.screenshot({ path: 'screenshots/20-agent-website-with-property.png', fullPage: true });
  });
});
