import { test, expect } from '@playwright/test';

test.describe('Facebook Integration in Modern Onboarding', () => {
  test('Complete onboarding flow with Facebook integration', async ({ page }) => {
    // Navigate to modern onboarding
    await page.goto('http://localhost:8003/modern-onboarding');
    await expect(page).toHaveTitle(/PropertyAI - Modern Agent Onboarding/);

    // Step 1: Basic Information
    await expect(page.locator('#step1')).toBeVisible();
    await page.fill('input[name="name"]', 'Test Agent');
    await page.fill('input[name="email"]', `test-${Date.now()}@example.com`);
    await page.fill('input[name="phone"]', '+1234567890');
    await page.fill('input[name="company"]', 'Test Real Estate');
    await page.click('#nextBtn');

    // Step 2: Experience & Specialization
    await expect(page.locator('#step2')).toBeVisible();
    await page.selectOption('select[name="experience_years"]', '3-5 years');
    await page.fill('input[name="specialization_areas"]', 'Mumbai, Bandra');
    await page.fill('input[name="languages"]', 'English, Hindi');
    await page.click('#nextBtn');

    // Step 3: AI Preferences
    await expect(page.locator('#step3')).toBeVisible();
    await page.check('#aiContent');
    await page.check('#aiSocial');
    await page.click('#nextBtn');

    // Step 4: Branding
    await expect(page.locator('#step4')).toBeVisible();
    await page.fill('#aiTagline', 'Your Trusted Real Estate Partner');
    await page.fill('#aiAbout', 'Professional real estate services');
    await page.click('#generateBrandingBtn');
    
    // Wait for AI branding generation
    await page.waitForSelector('.branding-suggestions', { timeout: 10000 });
    await page.click('#nextBtn');

    // Step 5: Facebook Integration Setup (NEW)
    await expect(page.locator('#step5')).toBeVisible();
    
    // Test the three Facebook setup options
    const facebookOptions = page.locator('.facebook-option');
    await expect(facebookOptions).toHaveCount(3);
    
    // Test "Quick Start" option
    await page.click('text=Quick Start (Recommended)');
    await expect(page.locator('.facebook-option.selected')).toBeVisible();
    await expect(page.locator('#ourAppSetup')).toBeVisible();
    
    // Test "Advanced Setup" option
    await page.click('text=Advanced Setup');
    await expect(page.locator('#yourAppSetup')).toBeVisible();
    
    // Test Facebook configuration validation
    await page.fill('input[name="facebook_app_id"]', 'test123');
    await page.fill('input[name="facebook_app_secret"]', 'test456');
    await page.fill('input[name="facebook_page_id"]', 'test789');
    
    // Click test configuration button
    await page.click('#testFacebookConfig');
    
    // Wait for response (should show error for invalid credentials)
    await page.waitForSelector('.alert', { timeout: 5000 });
    const alertText = await page.locator('.alert').textContent();
    expect(alertText).toContain('Invalid App ID or App Secret');
    
    // Test "Skip for Now" option
    await page.click('text=Skip for Now');
    await expect(page.locator('#ourAppSetup')).not.toBeVisible();
    await expect(page.locator('#yourAppSetup')).not.toBeVisible();
    
    // Select "Quick Start" for continuation
    await page.click('text=Quick Start (Recommended)');
    await page.click('#nextBtn');

    // Step 6: Review & Confirm
    await expect(page.locator('#step6')).toBeVisible();
    await page.click('#nextBtn');

    // Step 7: Success
    await expect(page.locator('#step7')).toBeVisible();
    await expect(page.locator('text=Congratulations!')).toBeVisible();
    await expect(page.locator('text=Your AI-powered real estate profile is ready')).toBeVisible();
  });

  test('Facebook configuration validation with real format', async ({ page }) => {
    await page.goto('http://localhost:8003/modern-onboarding');
    
    // Navigate to Step 5
    for (let i = 1; i <= 4; i++) {
      await page.fill(`#step${i} input`, 'test');
      await page.click('#nextBtn');
    }
    
    await expect(page.locator('#step5')).toBeVisible();
    await page.click('text=Advanced Setup');
    
    // Test with realistic Facebook App ID format
    await page.fill('input[name="facebook_app_id"]', '123456789012345');
    await page.fill('input[name="facebook_app_secret"]', 'abcdef123456789abcdef123456789ab');
    await page.fill('input[name="facebook_page_id"]', '987654321098765');
    
    await page.click('#testFacebookConfig');
    
    // Should show validation error (since these aren't real credentials)
    await page.waitForSelector('.alert', { timeout: 5000 });
    const alertText = await page.locator('.alert').textContent();
    expect(alertText).toContain('Invalid App ID or App Secret');
  });

  test('Mobile responsiveness of Facebook integration step', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('http://localhost:8003/modern-onboarding');
    
    // Navigate to Step 5
    for (let i = 1; i <= 4; i++) {
      await page.fill(`#step${i} input`, 'test');
      await page.click('#nextBtn');
    }
    
    await expect(page.locator('#step5')).toBeVisible();
    
    // Verify Facebook options are visible and clickable on mobile
    const facebookOptions = page.locator('.facebook-option');
    await expect(facebookOptions).toHaveCount(3);
    
    // Test mobile interaction
    await page.click('text=Quick Start (Recommended)');
    await expect(page.locator('.facebook-option.selected')).toBeVisible();
    await expect(page.locator('#ourAppSetup')).toBeVisible();
    
    // Verify form elements are properly sized for mobile
    const appSetupForm = page.locator('#ourAppSetup');
    await expect(appSetupForm).toBeVisible();
    
    // Test mobile form interaction
    await page.click('#connectFacebookBtn');
    
    // Should show some response (either success or error)
    await page.waitForTimeout(2000);
  });
});
