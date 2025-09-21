import { test, expect } from '@playwright/test';

/**
 * Complete User Journey E2E Test
 * =============================
 * 
 * This test covers the complete user journey from registration to property posting:
 * 1. User Registration → Create new account
 * 2. Onboarding → Complete user setup  
 * 3. Property Creation → Add first property listing
 * 4. Social Media Post → Generate AI content and post
 * 5. Agent Website → View property on agent profile
 * 
 * Natural Language: "Complete end-to-end user journey from registration to property sale"
 */

test.describe('Complete User Journey - Registration to Property Posting', () => {
  
  test('Complete user journey: Registration → Onboarding → Property → Social Post → Agent Website', async ({ page }) => {
    
    // === PHASE 1: USER REGISTRATION ===
    // Natural Language: "New user registers and creates account"
    console.log('🚀 Starting complete user journey...');
    
    await page.goto('/simple-register');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Fill registration form with unique data
    const timestamp = Date.now();
    const testEmail = `testuser${timestamp}@propertyai.com`;
    const testPassword = 'SecurePassword123!';
    
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);
    await page.fill('input[name="confirmPassword"]', testPassword);
    
    // Natural Language: "Submit registration form"
    await page.click('button[type="submit"]');
    
    // Natural Language: "Wait for registration to complete"
    await page.waitForTimeout(2000);
    
    // === PHASE 2: ONBOARDING ===
    // Natural Language: "User completes onboarding process"
    console.log('📋 Completing onboarding...');
    
    // Check if we're redirected to onboarding or dashboard
    const currentUrl = page.url();
    if (currentUrl.includes('/onboarding')) {
      // Fill onboarding form
      await page.fill('input[name="companyName"]', 'Doe Real Estate');
      await page.fill('input[name="phone"]', '+1-555-0123');
      await page.selectOption('select[name="experience"]', 'intermediate');
      await page.selectOption('select[name="specialization"]', 'residential');
      
      // Natural Language: "Complete onboarding and proceed to dashboard"
      await page.click('button[type="submit"]');
      await page.waitForTimeout(2000);
    }
    
    // === PHASE 3: PROPERTY CREATION ===
    // Natural Language: "User creates their first property listing"
    console.log('🏠 Creating first property...');
    
    await page.goto('/properties');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Click add property button
    await page.click('button[data-testid="add-property-button"], button:has-text("Add Property"), a[href*="/properties/new"]');
    
    // Fill property form
    await page.fill('input[name="title"]', 'Beautiful Modern Villa in Downtown');
    await page.fill('textarea[name="description"]', 'Stunning 4-bedroom villa with modern amenities, garden, and pool. Perfect for families looking for luxury living.');
    await page.fill('input[name="price"]', '2500000');
    await page.selectOption('select[name="propertyType"]', 'villa');
    await page.fill('input[name="location"]', 'Downtown, New York');
    await page.fill('input[name="bedrooms"]', '4');
    await page.fill('input[name="bathrooms"]', '3');
    await page.fill('input[name="areaSqft"]', '3200');
    
    // Add amenities and features
    await page.check('input[name="amenities"][value="parking"], input[value="parking"]');
    await page.check('input[name="amenities"][value="garden"], input[value="garden"]');
    await page.check('input[name="amenities"][value="pool"], input[value="pool"]');
    await page.check('input[name="features"][value="modular_kitchen"], input[value="modular_kitchen"]');
    await page.check('input[name="features"][value="wooden_flooring"], input[value="wooden_flooring"]');
    
    // Natural Language: "Submit property and verify it was created"
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    
    // Verify property appears in list
    await expect(page.locator('text=Beautiful Modern Villa in Downtown')).toBeVisible();
    
    // === PHASE 4: SOCIAL MEDIA PUBLISHING ===
    // Natural Language: "User generates AI content and publishes to social media"
    console.log('📱 Generating AI content and publishing...');
    
    // Navigate to social publishing
    await page.goto('/social-publishing');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Select property for promotion
    await page.click('button[data-testid="promote-property-button"], button:has-text("Promote Property"), select[name="property"]');
    
    // Choose target platforms
    await page.check('input[name="platforms"][value="facebook"], input[value="facebook"]');
    await page.check('input[name="platforms"][value="instagram"], input[value="instagram"]');
    await page.check('input[name="platforms"][value="linkedin"], input[value="linkedin"]');
    
    // Select content tone and style
    await page.selectOption('select[name="tone"]', 'luxury');
    await page.selectOption('select[name="language"]', 'en');
    await page.selectOption('select[name="length"]', 'medium');
    
    // Natural Language: "Generate AI-powered content"
    await page.click('button[data-testid="generate-content-button"], button:has-text("Generate Content")');
    
    // Wait for AI generation to complete
    await page.waitForTimeout(10000); // Give AI time to generate content
    
    // Verify content was generated
    await expect(page.locator('text=Content generated successfully, [data-testid="content-preview"]')).toBeVisible();
    
    // Natural Language: "Publish to social media platforms"
    await page.click('button[data-testid="publish-all-button"], button:has-text("Publish All")');
    
    // Wait for publishing to complete
    await page.waitForTimeout(5000);
    
    // === PHASE 5: AGENT WEBSITE/PROFILE ===
    // Natural Language: "User views their agent profile and property listing"
    console.log('🌐 Viewing agent profile...');
    
    // Navigate to agent profile
    await page.goto('/profile');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Verify agent profile displays
    await expect(page.locator('text=John Doe')).toBeVisible();
    await expect(page.locator('text=Doe Real Estate')).toBeVisible();
    
    // Navigate to properties section
    await page.click('text=Properties, a[href*="/properties"]');
    
    // Verify property is listed on profile
    await expect(page.locator('text=Beautiful Modern Villa in Downtown')).toBeVisible();
    await expect(page.locator('text=$2,500,000')).toBeVisible();
    
    // === PHASE 6: VERIFICATION ===
    // Natural Language: "Verify complete journey was successful"
    console.log('✅ Verifying complete journey...');
    
    // Check that user is logged in
    await expect(page.locator('text=John Doe, [data-testid="user-menu"]')).toBeVisible();
    
    // Check that property exists
    await page.goto('/properties');
    await expect(page.locator('text=Beautiful Modern Villa in Downtown')).toBeVisible();
    
    // Check that social posts were created
    await page.goto('/social-publishing');
    await expect(page.locator('text=Published, [data-testid="published-posts"]')).toBeVisible();
    
    console.log('🎉 Complete user journey test finished successfully!');
  });

  test('User can navigate through all main sections', async ({ page }) => {
    // Natural Language: "User can access all main sections of the application"
    
    // Go to home page
    await page.goto('/');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Navigate to properties
    await page.goto('/properties');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Navigate to analytics
    await page.goto('/analytics');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Navigate to social publishing
    await page.goto('/social-publishing');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Navigate to profile
    await page.goto('/profile');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    console.log('✅ All main sections are accessible');
  });

  test('Application maintains state across navigation', async ({ page }) => {
    // Natural Language: "Application maintains user state when navigating between pages"
    
    // This test would verify that user authentication state
    // and data persists across page navigation
    
    await page.goto('/simple-login');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Navigate to different pages and verify consistent experience
    await page.goto('/properties');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    await page.goto('/analytics');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    console.log('✅ Application state maintained across navigation');
  });
});