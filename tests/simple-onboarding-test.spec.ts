import { test, expect } from '@playwright/test';

test('Modern Onboarding Flow - Step by Step Test', async ({ page }) => {
  console.log('🚀 Starting Modern Onboarding Flow Test');
  
  // Navigate to modern onboarding page
  await page.goto('http://localhost:8003/modern-onboarding');
  await page.waitForLoadState('networkidle');
  
  console.log('✅ Page loaded successfully');
  
  // Verify page title and elements
  await expect(page).toHaveTitle(/PropertyAI - Modern Agent Onboarding/);
  await expect(page.locator('h1')).toContainText('PropertyAI');
  await expect(page.locator('.ai-powered-badge')).toContainText('Powered by GenAI');
  
  console.log('✅ Page elements verified');
  
  // Step 1: Personal Information
  console.log('🔄 Step 1: Filling Personal Information');
  await expect(page.locator('#step1')).toBeVisible();
  
  const timestamp = Date.now();
  await page.fill('input[name="name"]', 'Test Agent');
  await page.fill('input[name="email"]', `test.agent${timestamp}@modern-test.com`);
  await page.fill('input[name="phone"]', '+91-9876543210');
  await page.fill('input[name="whatsapp"]', '+91-9876543210');
  
  console.log('✅ Step 1: Personal information filled');
  
  // Move to Step 2
  await page.click('#nextBtn');
  await page.waitForTimeout(1000);
  
  // Step 2: Company Details
  console.log('🔄 Step 2: Filling Company Details');
  await expect(page.locator('#step2')).toBeVisible();
  
  await page.fill('input[name="company"]', 'Test Real Estate Solutions');
  await page.selectOption('select[name="experience_years"]', '3');
  await page.fill('input[name="specialization_areas"]', 'Mumbai, Bandra');
  await page.fill('input[name="languages"]', 'English, Hindi');
  
  console.log('✅ Step 2: Company details filled');
  
  // Move to Step 3
  await page.click('#nextBtn');
  await page.waitForTimeout(1000);
  
  // Step 3: AI Branding Generation
  console.log('🔄 Step 3: Testing AI Branding Generation');
  await expect(page.locator('#step3')).toBeVisible();
  await expect(page.locator('#generateBranding')).toBeVisible();
  
  // Click Generate AI Branding
  await page.click('#generateBranding');
  
  // Wait for branding results
  await page.waitForSelector('#brandingResults', { state: 'visible', timeout: 10000 });
  
  // Verify branding results
  const tagline = await page.locator('#aiTagline').inputValue();
  const about = await page.locator('#aiAbout').inputValue();
  
  console.log(`✅ Step 3: AI branding generated - Tagline: "${tagline}"`);
  console.log(`   About: ${about.substring(0, 50)}...`);
  
  // Move to Step 4
  await page.click('#nextBtn');
  await page.waitForTimeout(1000);
  
  // Step 4: Profile Setup
  console.log('🔄 Step 4: Profile Setup');
  await expect(page.locator('#step4')).toBeVisible();
  
  await page.fill('input[name="profile_photo_url"]', 'https://example.com/test.jpg');
  await page.fill('textarea[name="bio"]', 'Test bio for modern onboarding');
  
  console.log('✅ Step 4: Profile setup completed');
  
  // Move to Step 5
  await page.click('#nextBtn');
  await page.waitForTimeout(1000);
  
  // Step 5: AI Preferences
  console.log('🔄 Step 5: AI Preferences');
  await expect(page.locator('#step5')).toBeVisible();
  
  await page.selectOption('select[name="content_style"]', 'modern');
  await page.selectOption('select[name="automation_level"]', 'advanced');
  
  console.log('✅ Step 5: AI preferences configured');
  
  // Move to Step 6
  await page.click('#nextBtn');
  await page.waitForTimeout(1000);
  
  // Step 6: Verification & Completion
  console.log('🔄 Step 6: Verification & Completion');
  await expect(page.locator('#step6')).toBeVisible();
  
  // Send verification code
  await page.click('#sendVerification');
  await page.waitForTimeout(2000);
  
  // Fill verification code
  const verificationInputs = await page.locator('.verification-input').all();
  for (let i = 0; i < 6; i++) {
    await verificationInputs[i].fill((i + 1).toString());
  }
  
  // Accept terms
  await page.check('input[name="terms_accepted"]');
  await page.check('input[name="marketing_consent"]');
  
  console.log('✅ Step 6: Verification completed');
  
  // Submit form
  await page.click('#submitBtn');
  
  // Wait for redirect to login page (success)
  await page.waitForURL('http://localhost:8003/', { timeout: 10000 });
  
  console.log('✅ Final: Redirected to login page');
  
  console.log('\n🎉 MODERN ONBOARDING FLOW TEST COMPLETED SUCCESSFULLY!');
  console.log('📋 All 6 steps completed:');
  console.log('   1. ✅ Personal Information');
  console.log('   2. ✅ Company Details');
  console.log('   3. ✅ AI Branding Generation (Real LLM)');
  console.log('   4. ✅ Profile Setup');
  console.log('   5. ✅ AI Preferences');
  console.log('   6. ✅ Verification & Completion');
  console.log('   🎯 Final: Successfully redirected to login');
});
