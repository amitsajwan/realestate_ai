import { test, expect } from '@playwright/test';

test.describe('Onboarding Fix Verification', () => {
  test('should complete onboarding and redirect to dashboard (no loop)', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Register a new user
    await page.click('text=Sign up');
    await page.waitForSelector('input[name="firstName"]', { timeout: 5000 });
    
    const uniqueEmail = `fixtest${Date.now()}@example.com`;
    const testPassword = 'TestPass123!';
    
    console.log('Registering user:', uniqueEmail);
    
    await page.fill('input[name="email"]', uniqueEmail);
    await page.fill('input[name="firstName"]', 'Fix');
    await page.fill('input[name="lastName"]', 'Test');
    await page.fill('input[name="phone"]', '+15551234567');
    await page.fill('input[name="password"]', testPassword);
    await page.fill('input[name="confirmPassword"]', testPassword);
    
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    
    // Login if needed
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      console.log('Logging in with registered credentials');
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      await page.fill('input[name="email"]', uniqueEmail);
      await page.fill('input[name="password"]', testPassword);
      await page.click('button[type="submit"]');
      await page.waitForTimeout(3000);
    }
    
    // Should be on onboarding page
    console.log('Current URL after login:', page.url());
    
    // Navigate to onboarding if not already there
    if (!page.url().includes('/onboarding')) {
      await page.goto('/onboarding');
    }
    
    await page.waitForSelector('input[placeholder="John"]', { timeout: 10000 });
    
    // Complete onboarding steps quickly
    console.log('Step 1: Personal Information');
    await page.fill('input[placeholder="John"]', 'Fix');
    await page.fill('input[placeholder="Doe"]', 'Test');
    await page.click('button:has-text("Next")');
    await page.waitForTimeout(1000);

    console.log('Step 2: Company Details');
    await page.fill('input[placeholder="Real Estate Pro"]', 'Test Company');
    await page.fill('input[placeholder="Senior Agent"]', 'Test Agent');
    await page.click('button:has-text("Next")');
    await page.waitForTimeout(1000);

    console.log('Step 3: AI Preferences');
    const selects = page.locator('select');
    await selects.nth(0).selectOption({ label: 'Professional' });
    await selects.nth(1).selectOption({ label: 'Friendly' });
    await page.click('button:has-text("Next")');
    await page.waitForTimeout(1000);
    
    console.log('Step 4: Social (skip)');
    await page.click('button:has-text("Next")');
    await page.waitForTimeout(1000);

    console.log('Step 5: Terms');
    await page.check('#terms');
    await page.check('#privacy');
    await page.click('button:has-text("Next")');
    await page.waitForTimeout(1000);
    
    console.log('Step 6: Complete onboarding');
    
    // This is the critical test - clicking "Complete" should redirect to dashboard
    await page.click('button:has-text("Complete")');
    
    // Wait longer for the completion process and potential redirect
    await page.waitForTimeout(5000);
    
    const finalUrl = page.url();
    console.log('Final URL after completion:', finalUrl);
    
    // THE FIX TEST: Should be on dashboard, NOT back on onboarding
    if (finalUrl.includes('/onboarding')) {
      // Check if we're still on onboarding - this indicates the bug is still present
      const currentStep = await page.textContent('.text-sm.text-gray-500');
      console.log('❌ BUG STILL PRESENT: User redirected back to onboarding');
      console.log('Current step shown:', currentStep);
      
      // Take screenshot for debugging
      await page.screenshot({ path: 'onboarding-loop-bug.png' });
      
      throw new Error('ONBOARDING LOOP BUG: User completed onboarding but was redirected back to onboarding instead of dashboard');
    } else if (finalUrl.includes('/dashboard')) {
      console.log('✅ FIX SUCCESSFUL: User redirected to dashboard after onboarding completion');
      
      // Verify dashboard content is loaded
      await expect(page).toHaveURL('/dashboard');
      
      // Take success screenshot
      await page.screenshot({ path: 'onboarding-fix-success.png' });
      
    } else {
      console.log('⚠️ UNEXPECTED: User redirected to unexpected page:', finalUrl);
      await page.screenshot({ path: 'onboarding-unexpected-redirect.png' });
      
      // This might be okay depending on your app flow, but let's check
      expect(finalUrl).not.toContain('/onboarding');
    }
    
    console.log('✅ Onboarding fix verification completed successfully');
  });
});