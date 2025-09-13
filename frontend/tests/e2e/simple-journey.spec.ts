import { test, expect } from '@playwright/test';

test.describe('Simple User Journey', () => {
  test('Basic User Journey: Home → Login → Dashboard → Available Pages', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    console.log('🎬 Starting Simple User Journey Test...');
    
    // Step 1: Home page
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/simple-01-home.png', fullPage: true });
    console.log('📸 Home page captured');
    
    // Step 2: Login page
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/simple-02-login.png', fullPage: true });
    console.log('📸 Login page captured');
    
    // Step 3: Try to login with existing user
    await page.fill('input[type="email"]', 'frontenduser@example.com');
    await page.fill('input[type="password"]', 'TestPassword123!');
    await page.screenshot({ path: 'screenshots/simple-03-login-filled.png', fullPage: true });
    console.log('📸 Login form filled');
    
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/simple-04-login-success.png', fullPage: true });
    console.log('📸 Login success');
    
    // Step 4: Dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/simple-05-dashboard.png', fullPage: true });
    console.log('📸 Dashboard captured');
    
    // Step 5: Properties page
    await page.goto('/properties');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/simple-06-properties.png', fullPage: true });
    console.log('📸 Properties page captured');
    
    // Step 6: Try to add property
    await page.goto('/properties/add');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/simple-07-add-property.png', fullPage: true });
    console.log('📸 Add property page captured');
    
    // Step 7: Try onboarding
    await page.goto('/onboarding');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/simple-08-onboarding.png', fullPage: true });
    console.log('📸 Onboarding page captured');
    
    // Step 8: Try agent profile
    await page.goto('/agent/profile');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/simple-09-agent-profile.png', fullPage: true });
    console.log('📸 Agent profile page captured');
    
    // Step 9: Try publishing
    await page.goto('/publishing');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/simple-10-publishing.png', fullPage: true });
    console.log('📸 Publishing page captured');
    
    // Step 10: Try agent website
    await page.goto('/agent/frontenduser');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'screenshots/simple-11-agent-website.png', fullPage: true });
    console.log('📸 Agent website captured');
    
    console.log('✅ Simple User Journey Test Completed!');
  });
});
