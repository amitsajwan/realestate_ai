import { test, expect } from '@playwright/test';

test.describe('PropertyAI - Complete Demo Journey', () => {
  test('Full user journey: Login → Dashboard → Modern Onboarding → Features', async ({ page }) => {
    console.log('\n🎬 PROPERTYAI COMPLETE DEMO JOURNEY');
    console.log('='.repeat(60));
    
    // ==========================================
    // PHASE 1: LOGIN AND DASHBOARD
    // ==========================================
    console.log('\n📍 PHASE 1: Login & Dashboard');
    console.log('-'.repeat(40));
    
    // Navigate and login
    await page.goto('http://localhost:8003/');
    await expect(page).toHaveTitle(/Real Estate CRM - Login/);
    console.log('✅ Login page loaded');
    
    // Login with demo credentials
    await page.fill('input[type="email"]', 'demo@mumbai.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    
    // Wait for dashboard
    await page.waitForURL('**/dashboard');
    await expect(page).toHaveTitle(/PropertyAI - Next-Gen AI Real Estate Dashboard/);
    console.log('✅ Dashboard loaded successfully');
    
    // Take screenshot of dashboard
    await page.screenshot({ path: 'test-results/demo-dashboard.png', fullPage: true });
    console.log('📸 Dashboard screenshot captured');
    
    // ==========================================
    // PHASE 2: DASHBOARD FEATURES OVERVIEW
    // ==========================================
    console.log('\n📍 PHASE 2: Dashboard Features');
    console.log('-'.repeat(40));
    
    // Check for key sections
    await expect(page.locator('h1')).toContainText('PropertyAI');
    await expect(page.locator('h5:has-text("Facebook Integration")')).toBeVisible();
    console.log('✅ Facebook Integration section found');
    
    // Check for AI onboarding button
    await expect(page.locator('a[href="/modern-onboarding"]')).toBeVisible();
    console.log('✅ Modern AI Onboarding link found');
    
    // ==========================================
    // PHASE 3: MODERN ONBOARDING JOURNEY
    // ==========================================
    console.log('\n📍 PHASE 3: Modern AI Onboarding');
    console.log('-'.repeat(40));
    
    // Navigate to modern onboarding
    await page.click('a[href="/modern-onboarding"]');
    await page.waitForLoadState('networkidle');
    
    await expect(page).toHaveTitle(/PropertyAI - Modern Agent Onboarding/);
    await expect(page.locator('.ai-powered-badge')).toContainText('Powered by GenAI');
    console.log('✅ Modern onboarding page loaded');
    
    // Take screenshot of onboarding start
    await page.screenshot({ path: 'test-results/demo-onboarding-start.png', fullPage: true });
    console.log('📸 Onboarding start screenshot captured');
    
    // ==========================================
    // STEP 1: Personal Information
    // ==========================================
    console.log('\n🔄 STEP 1: Personal Information');
    
    const timestamp = Date.now();
    const demoEmail = `demo.agent${timestamp}@propertyai.com`;
    
    await page.fill('input[name="name"]', 'Demo Agent');
    await page.fill('input[name="email"]', demoEmail);
    await page.fill('input[name="phone"]', '+91-9876543210');
    await page.fill('input[name="whatsapp"]', '+91-9876543210');
    
    console.log(`✅ Personal info filled: ${demoEmail}`);
    await page.click('#nextBtn');
    
    // ==========================================
    // STEP 2: Company Details
    // ==========================================
    console.log('\n🔄 STEP 2: Company Details');
    
    await expect(page.locator('#step2')).toBeVisible();
    
    await page.fill('input[name="company"]', 'PropertyAI Demo Real Estate');
    await page.selectOption('select[name="experience_years"]', '5');
    await page.fill('input[name="specialization_areas"]', 'Mumbai, Luxury Properties');
    await page.fill('input[name="languages"]', 'English, Hindi, Marathi');
    
    console.log('✅ Company details filled');
    await page.click('#nextBtn');
    
    // ==========================================
    // STEP 3: AI Branding Generation
    // ==========================================
    console.log('\n🔄 STEP 3: AI Branding Generation');
    
    await expect(page.locator('#step3')).toBeVisible();
    console.log('🤖 Initiating AI branding generation...');
    
    await page.click('#generateBranding');
    await page.waitForSelector('#brandingResults', { state: 'visible', timeout: 10000 });
    
    // Get generated branding
    const tagline = await page.locator('#aiTagline').inputValue();
    console.log(`🎯 AI Generated Tagline: "${tagline}"`);
    
    console.log('✅ AI branding generated successfully');
    await page.click('#nextBtn');
    
    // ==========================================
    // STEP 4: Profile Setup
    // ==========================================
    console.log('\n🔄 STEP 4: Profile Setup');
    
    await expect(page.locator('#step4')).toBeVisible();
    
    await page.fill('input[name="profile_photo_url"]', 'https://example.com/profile.jpg');
    await page.fill('textarea[name="bio"]', 'Experienced real estate professional specializing in luxury properties in Mumbai.');
    
    // Select contact preferences
    const contactOptions = await page.locator('input[name="contact_preferences[]"]').all();
    for (let i = 0; i < Math.min(2, contactOptions.length); i++) {
      await contactOptions[i].check();
    }
    
    console.log('✅ Profile setup completed');
    await page.click('#nextBtn');
    
    // ==========================================
    // STEP 5: AI Preferences
    // ==========================================
    console.log('\n🔄 STEP 5: AI Preferences');
    
    await expect(page.locator('#step5')).toBeVisible();
    
    await page.selectOption('select[name="content_style"]', 'luxury');
    await page.selectOption('select[name="automation_level"]', 'advanced');
    
    // Select AI preferences
    const aiOptions = await page.locator('input[name="ai_preferences[]"]').all();
    for (let i = 0; i < Math.min(2, aiOptions.length); i++) {
      await aiOptions[i].check();
    }
    
    console.log('✅ AI preferences configured');
    await page.click('#nextBtn');
    
    // ==========================================
    // STEP 6: Verification & Completion
    // ==========================================
    console.log('\n🔄 STEP 6: Verification & Completion');
    
    await expect(page.locator('#step6')).toBeVisible();
    
    // Send verification code
    await page.click('#sendVerification');
    console.log('✅ Verification code sent');
    
    // Fill verification code
    const verificationInputs = await page.locator('.verification-input').all();
    for (let i = 0; i < 6; i++) {
      await verificationInputs[i].fill((i + 1).toString());
    }
    
    // Accept terms
    await page.check('input[name="terms_accepted"]');
    await page.check('input[name="marketing_consent"]');
    
    console.log('✅ Terms accepted, verification completed');
    
    // Submit form
    await page.click('#submitBtn');
    
    // Wait for redirect to login
    await page.waitForURL('http://localhost:8003/', { timeout: 10000 });
    console.log('✅ Onboarding completed successfully!');
    
    // ==========================================
    // PHASE 4: LOGIN WITH NEW USER
    // ==========================================
    console.log('\n📍 PHASE 4: New User Login');
    console.log('-'.repeat(40));
    
    // Login with newly created user
    await page.fill('input[type="email"]', demoEmail);
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    
    await page.waitForURL('**/dashboard');
    console.log('✅ New user login successful!');
    
    // Take final screenshot
    await page.screenshot({ path: 'test-results/demo-complete-journey.png', fullPage: true });
    console.log('📸 Complete journey screenshot captured');
    
    // ==========================================
    // DEMO COMPLETION SUMMARY
    // ==========================================
    console.log('\n🎉 PROPERTYAI DEMO JOURNEY COMPLETED!');
    console.log('='.repeat(60));
    console.log('✅ Login & Authentication');
    console.log('✅ Dashboard Overview');
    console.log('✅ Facebook Integration');
    console.log('✅ Modern AI Onboarding (6 steps)');
    console.log('✅ Real AI Branding Generation');
    console.log('✅ Database Persistence');
    console.log('✅ New User Creation & Login');
    console.log('');
    console.log('🚀 PROPERTYAI - NEXT-GENERATION REAL ESTATE CRM');
    console.log('   Powered by AI | Built for Success | Ready for Production');
    console.log('='.repeat(60));
  });
});
