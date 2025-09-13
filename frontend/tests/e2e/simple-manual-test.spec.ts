import { test, expect } from '@playwright/test';

test.describe('SIMPLE MANUAL TEST - Step by Step', () => {
  test('Test 1: Basic Page Load and Form Check', async ({ page }) => {
    console.log('🔍 SIMPLE MANUAL TEST - Starting...');
    
    // Step 1: Go to login page
    console.log('Step 1: Going to login page...');
    await page.goto('http://localhost:3001/login');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/simple-01-login-page.png', fullPage: true });
    
    // Check what we see
    const pageInfo = await page.evaluate(() => {
      const title = document.title;
      const hasEmail = !!document.querySelector('input[type="email"]');
      const hasPassword = !!document.querySelector('input[type="password"]');
      const hasSubmit = !!document.querySelector('button[type="submit"]');
      const hasSignUp = !!Array.from(document.querySelectorAll('button')).find(btn => 
        btn.textContent?.includes('Sign up') || btn.textContent?.includes('Sign Up')
      );
      
      return {
        title,
        hasEmail,
        hasPassword,
        hasSubmit,
        hasSignUp
      };
    });
    
    console.log('Login page info:', pageInfo);
    
    // Step 2: Try to switch to registration
    if (pageInfo.hasSignUp) {
      console.log('Step 2: Switching to registration form...');
      await page.click('button:has-text("Sign up")');
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'screenshots/simple-02-registration-form.png', fullPage: true });
      
      // Check registration form
      const regInfo = await page.evaluate(() => {
        const hasFirstName = !!document.querySelector('input[name="firstName"]');
        const hasLastName = !!document.querySelector('input[name="lastName"]');
        const hasEmail = !!document.querySelector('input[type="email"]');
        const hasPassword = !!document.querySelector('input[type="password"]');
        const hasConfirmPassword = !!document.querySelector('input[name="confirmPassword"]');
        const hasPhone = !!document.querySelector('input[name="phone"]');
        const hasSubmit = !!document.querySelector('button[type="submit"]');
        
        return {
          hasFirstName,
          hasLastName,
          hasEmail,
          hasPassword,
          hasConfirmPassword,
          hasPhone,
          hasSubmit
        };
      });
      
      console.log('Registration form info:', regInfo);
      
      // Step 3: Try to fill form
      console.log('Step 3: Trying to fill registration form...');
      try {
        await page.fill('input[name="firstName"]', 'Test');
        await page.fill('input[name="lastName"]', 'User');
        await page.fill('input[type="email"]', 'test@example.com');
        await page.fill('input[type="password"]', 'password123');
        await page.fill('input[name="confirmPassword"]', 'password123');
        await page.fill('input[name="phone"]', '1234567890');
        
        await page.waitForTimeout(1000);
        
        // Check if submit button is enabled
        const submitState = await page.evaluate(() => {
          const submitButton = document.querySelector('button[type="submit"]');
          return {
            exists: !!submitButton,
            disabled: submitButton ? submitButton.hasAttribute('disabled') : false,
            text: submitButton ? submitButton.textContent?.trim() : null
          };
        });
        
        console.log('Submit button state:', submitState);
        
        if (!submitState.disabled) {
          console.log('Step 4: Trying to submit form...');
          await page.click('button[type="submit"]');
          await page.waitForTimeout(5000);
          
          const afterSubmit = await page.evaluate(() => {
            return {
              url: window.location.href,
              hasError: !!document.querySelector('.error, .alert, [role="alert"]'),
              hasSuccess: !!document.querySelector('.success, .alert-success')
            };
          });
          
          console.log('After submit:', afterSubmit);
        } else {
          console.log('Submit button is disabled - form validation issue');
        }
        
      } catch (error) {
        console.log('Error filling form:', error.message);
      }
    }
    
    console.log('✅ SIMPLE MANUAL TEST COMPLETE');
  });
});