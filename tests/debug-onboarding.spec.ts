import { test, expect } from '@playwright/test';

test('Debug Modern Onboarding Form Submission', async ({ page }) => {
  console.log('🚀 Starting Debug Test');
  
  // Navigate to modern onboarding page
  await page.goto('http://localhost:8003/modern-onboarding');
  await page.waitForLoadState('networkidle');
  
  // Listen for JavaScript errors
  page.on('pageerror', error => {
    console.log('🚨 JavaScript error:', error.message);
  });
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('🚨 Console error:', msg.text());
    }
  });
  
  console.log('✅ Page loaded');
  
  // Fill minimal data for step 1
  const timestamp = Date.now();
  await page.fill('input[name="name"]', 'Debug Test');
  await page.fill('input[name="email"]', `debug${timestamp}@test.com`);
  await page.fill('input[name="phone"]', '+91-1234567890');
  
  console.log('✅ Step 1 filled');
  
  // Go to step 2
  await page.click('#nextBtn');
  await page.waitForTimeout(1000);
  
  // Fill step 2
  await page.fill('input[name="company"]', 'Debug Company');
  await page.selectOption('select[name="experience_years"]', '2');
  await page.fill('input[name="specialization_areas"]', 'Mumbai');
  await page.fill('input[name="languages"]', 'English');
  
  console.log('✅ Step 2 filled');
  
  // Go to step 3
  await page.click('#nextBtn');
  await page.waitForTimeout(1000);
  
  // Generate AI branding
  await page.click('#generateBranding');
  await page.waitForSelector('#brandingResults', { state: 'visible', timeout: 10000 });
  
  console.log('✅ AI branding generated');
  
  // Go to step 4
  await page.click('#nextBtn');
  await page.waitForTimeout(1000);
  
  // Fill step 4
  await page.fill('input[name="profile_photo_url"]', 'https://example.com/debug.jpg');
  await page.fill('textarea[name="bio"]', 'Debug bio');
  
  console.log('✅ Step 4 filled');
  
  // Go to step 5
  await page.click('#nextBtn');
  await page.waitForTimeout(1000);
  
  // Fill step 5
  await page.selectOption('select[name="content_style"]', 'modern');
  await page.selectOption('select[name="automation_level"]', 'basic');
  
  console.log('✅ Step 5 filled');
  
  // Go to step 6
  await page.click('#nextBtn');
  await page.waitForTimeout(1000);
  
  // Fill step 6
  await page.click('#sendVerification');
  await page.waitForTimeout(2000);
  
  const verificationInputs = await page.locator('.verification-input').all();
  for (let i = 0; i < 6; i++) {
    await verificationInputs[i].fill((i + 1).toString());
  }
  
  await page.check('input[name="terms_accepted"]');
  await page.check('input[name="marketing_consent"]');
  
  console.log('✅ Step 6 filled');
  
  // Listen for network requests
  page.on('request', request => {
    console.log(`🌐 Request: ${request.method()} ${request.url()}`);
  });
  
  page.on('response', response => {
    console.log(`📡 Response: ${response.status()} ${response.url()}`);
    if (response.url().includes('/modern-agent/onboard')) {
      response.text().then(text => {
        console.log(`📄 Response body: ${text}`);
      });
    }
  });
  
  // Submit form
  console.log('🔄 Submitting form...');
  await page.click('#submitBtn');
  
  // Wait for redirect to login page (success)
  await page.waitForURL('http://localhost:8003/', { timeout: 10000 });
  
  console.log('✅ Successfully redirected to login page');
  console.log('🎉 Debug test completed successfully!');
});
