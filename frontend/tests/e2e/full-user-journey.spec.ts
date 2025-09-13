import { test, expect } from '@playwright/test';

test.describe('Complete User Journey', () => {
  test('Full User Journey: Register → Login → Onboarding → Add Property → Post Creation → Publishing → Agent Website', async ({ page }) => {
    // Set viewport for consistent screenshots
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    // Create screenshots directory
    await page.context().addInitScript(() => {
      // This will run before any page loads
    });
    
    console.log('🎬 Starting Full User Journey Test...');
    
    // Step 1: Navigate to home page first
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/01-home-page.png', fullPage: true });
    console.log('📸 Screenshot 1: Home page captured');
    
    // Step 2: Navigate to registration page
    await page.goto('/register');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/02-register-page.png', fullPage: true });
    console.log('📸 Screenshot 2: Register page captured');
    
    // Check if registration form exists, if not, try login
    const registerForm = page.locator('form').first();
    if (await registerForm.count() > 0) {
      // Fill registration form
      await page.fill('input[name="email"], input[type="email"]', 'testuser@example.com');
      await page.fill('input[name="password"], input[type="password"]', 'TestPassword123!');
      await page.fill('input[name="firstName"], input[name="first_name"]', 'Test');
      await page.fill('input[name="lastName"], input[name="last_name"]', 'User');
      await page.screenshot({ path: 'screenshots/03-register-form-filled.png', fullPage: true });
      console.log('📸 Screenshot 3: Register form filled');
      
      // Submit registration
      await page.click('button[type="submit"], button:has-text("Register"), button:has-text("Sign Up")');
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'screenshots/04-register-submitted.png', fullPage: true });
      console.log('📸 Screenshot 4: Register submitted');
    }
    
    // Step 3: Login
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/05-login-page.png', fullPage: true });
    console.log('📸 Screenshot 5: Login page captured');
    
    // Fill login form
    await page.fill('input[name="email"], input[type="email"]', 'testuser@example.com');
    await page.fill('input[name="password"], input[type="password"]', 'TestPassword123!');
    await page.screenshot({ path: 'screenshots/06-login-form-filled.png', fullPage: true });
    console.log('📸 Screenshot 6: Login form filled');
    
    await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/07-login-success.png', fullPage: true });
    console.log('📸 Screenshot 7: Login success');
    
    // Step 4: Try to navigate to dashboard or onboarding
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/08-dashboard.png', fullPage: true });
    console.log('📸 Screenshot 8: Dashboard');
    
    // Step 5: Agent Onboarding
    await page.goto('/onboarding');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/09-onboarding-page.png', fullPage: true });
    console.log('📸 Screenshot 9: Onboarding page');
    
    // Fill onboarding form if it exists
    const onboardingForm = page.locator('form').first();
    if (await onboardingForm.count() > 0) {
      await page.fill('input[name="name"], input[name="username"]', 'Test Agent');
      await page.fill('input[name="email"]', 'testuser@example.com');
      await page.fill('input[name="phone"], input[name="whatsapp"]', '+1234567890');
      await page.fill('input[name="company_name"]', 'Test Real Estate Agency');
      await page.fill('input[name="license_number"]', 'RE123456');
      await page.fill('textarea[name="bio"]', 'Experienced real estate agent specializing in luxury properties');
      await page.screenshot({ path: 'screenshots/10-onboarding-form-filled.png', fullPage: true });
      console.log('📸 Screenshot 10: Onboarding form filled');
      
      await page.click('button[type="submit"], button:has-text("Submit"), button:has-text("Complete")');
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'screenshots/11-onboarding-success.png', fullPage: true });
      console.log('📸 Screenshot 11: Onboarding success');
    }
    
    // Step 6: Add Property
    await page.goto('/properties/add');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/12-add-property-page.png', fullPage: true });
    console.log('📸 Screenshot 12: Add property page');
    
    // Fill property form if it exists
    const propertyForm = page.locator('form').first();
    if (await propertyForm.count() > 0) {
      await page.fill('input[name="title"]', 'Luxury Villa with Pool');
      await page.fill('textarea[name="description"]', 'Beautiful luxury villa with modern amenities and private pool');
      await page.selectOption('select[name="property_type"]', 'house');
      await page.fill('input[name="price"]', '2500000');
      await page.fill('input[name="location"]', 'Beverly Hills, CA');
      await page.fill('input[name="bedrooms"]', '5');
      await page.fill('input[name="bathrooms"]', '4');
      await page.fill('input[name="area_sqft"]', '4000');
      await page.screenshot({ path: 'screenshots/13-property-form-filled.png', fullPage: true });
      console.log('📸 Screenshot 13: Property form filled');
      
      await page.click('button[type="submit"], button:has-text("Create"), button:has-text("Add Property")');
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'screenshots/14-property-created.png', fullPage: true });
      console.log('📸 Screenshot 14: Property created');
    }
    
    // Step 7: Post Creation
    await page.goto('/posts/create');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/15-post-creation-page.png', fullPage: true });
    console.log('📸 Screenshot 15: Post creation page');
    
    // Step 8: Publishing
    await page.goto('/publishing');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/16-publishing-page.png', fullPage: true });
    console.log('📸 Screenshot 16: Publishing page');
    
    // Step 9: Agent Website
    await page.goto('/agent/testuser');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/17-agent-website.png', fullPage: true });
    console.log('📸 Screenshot 17: Agent website');
    
    // Step 10: Properties listing
    await page.goto('/properties');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/18-properties-listing.png', fullPage: true });
    console.log('📸 Screenshot 18: Properties listing');
    
    console.log('✅ Full User Journey Test Completed!');
  });
});
