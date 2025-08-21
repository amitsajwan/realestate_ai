import { test, expect } from '@playwright/test';

test.describe('Onboarding 7-Step Flow Verification', () => {
  test('should complete all 7 steps of onboarding successfully', async ({ page }) => {
    // Navigate to onboarding
    await page.goto('/modern-onboarding');
    
    // Verify we start at step 1
    await expect(page.locator('#step1')).toBeVisible();
    await expect(page.locator('h2')).toContainText('Step 1 of 7');

    // Step 1: Agent Information
    await page.fill('input[name="name"]', 'Test Agent');
    await page.fill('input[name="email"]', `agent${Date.now()}@test.com`);
    await page.fill('input[name="phone"]', '9876543210');
    await page.selectOption('select[name="experience_years"]', '5');
    await page.click('button:has-text("Next")');

    // Step 2: Business Details
    await expect(page.locator('#step2')).toBeVisible();
    await expect(page.locator('h2')).toContainText('Step 2 of 7');
    await page.fill('input[name="company_name"]', 'Test Real Estate');
    await page.fill('input[name="business_address"]', 'Mumbai, Maharashtra');
    await page.selectOption('select[name="business_type"]', 'real_estate_firm');
    await page.click('button:has-text("Next")');

    // Step 3: Service Areas
    await expect(page.locator('#step3')).toBeVisible();
    await expect(page.locator('h2')).toContainText('Step 3 of 7');
    await page.fill('input[name="primary_location"]', 'Mumbai');
    await page.check('input[value="residential"]');
    await page.click('button:has-text("Next")');

    // Step 4: AI Branding
    await expect(page.locator('#step4')).toBeVisible();
    await expect(page.locator('h2')).toContainText('Step 4 of 7');
    await page.click('button:has-text("Generate AI Branding")');
    // Wait for AI generation (or skip if it fails)
    await page.waitForTimeout(2000);
    await page.click('button:has-text("Next")');

    // Step 5: Facebook Integration
    await expect(page.locator('#step5')).toBeVisible();
    await expect(page.locator('h2')).toContainText('Step 5 of 7');
    await page.click('button:has-text("Skip for Now")');
    await page.click('button:has-text("Next")');

    // Step 6: Legal Compliance & RERA
    await expect(page.locator('#step6')).toBeVisible();
    await expect(page.locator('h2')).toContainText('Step 6 of 7');
    await page.fill('input[name="rera_number"]', 'MH123456789');
    await page.selectOption('select[name="rera_state"]', 'maharashtra');
    await page.selectOption('select[name="business_type"]', 'individual_agent');
    await page.check('input[value="residential_sale"]');
    await page.click('button:has-text("Next")');

    // Step 7: Verification & Completion
    await expect(page.locator('#step7')).toBeVisible();
    await expect(page.locator('h2')).toContainText('Step 7 of 7');
    
    // Verify final step elements
    await expect(page.locator('h3')).toContainText('Verification & Completion');
    await expect(page.locator('button:has-text("Send Verification Code")')).toBeVisible();
    
    // Complete the flow
    await page.click('button:has-text("Complete Registration")');
    
    // Should redirect to dashboard
    await page.waitForURL(/dashboard/);
    await expect(page).toHaveTitle(/Dashboard/);
  });

  test('should show progress correctly through all 7 steps', async ({ page }) => {
    await page.goto('/modern-onboarding');
    
    // Check initial progress
    await expect(page.locator('.progress-fill')).toBeVisible();
    
    // Verify step indicators
    const stepDots = page.locator('.step-dot');
    await expect(stepDots).toHaveCount(7);
    
    // First step should be active
    await expect(stepDots.first()).toHaveClass(/active/);
  });

  test('should validate RERA compliance fields in step 6', async ({ page }) => {
    await page.goto('/modern-onboarding');
    
    // Quick navigate to step 6 (assuming form allows skipping for testing)
    await page.evaluate(() => {
      (window as any).onboardingFlow.currentStep = 6;
      (window as any).onboardingFlow.updateStep();
    });
    
    await expect(page.locator('#step6')).toBeVisible();
    
    // Verify RERA fields are present
    await expect(page.locator('input[name="rera_number"]')).toBeVisible();
    await expect(page.locator('select[name="rera_state"]')).toBeVisible();
    await expect(page.locator('select[name="business_type"]')).toBeVisible();
    
    // Verify specialization checkboxes
    await expect(page.locator('input[value="residential_sale"]')).toBeVisible();
    await expect(page.locator('input[value="commercial"]')).toBeVisible();
    await expect(page.locator('input[value="land_plots"]')).toBeVisible();
  });
});
