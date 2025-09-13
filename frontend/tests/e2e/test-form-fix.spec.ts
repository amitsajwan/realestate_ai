import { test, expect } from '@playwright/test';

test.describe('FORM FIX TEST - Check if forms work now', () => {
  test('Test login and registration forms', async ({ page }) => {
    console.log('🔍 TESTING FORM FIXES...');
    
    // Test 1: Login page
    console.log('Step 1: Testing login page...');
    await page.goto('http://localhost:3001/login');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/fix-01-login-page.png', fullPage: true });
    
    // Check if form is visible and submit button is enabled
    const loginState = await page.evaluate(() => {
      const loadingElement = Array.from(document.querySelectorAll('div')).find(div => 
        div.textContent?.includes('Loading')
      );
      const emailField = document.querySelector('input[type="email"]');
      const passwordField = document.querySelector('input[type="password"]');
      const submitButton = document.querySelector('button[type="submit"]');
      
      return {
        hasLoadingElement: !!loadingElement,
        hasEmailField: !!emailField,
        hasPasswordField: !!passwordField,
        hasSubmitButton: !!submitButton,
        submitButtonDisabled: submitButton ? submitButton.hasAttribute('disabled') : false,
        submitButtonText: submitButton ? submitButton.textContent?.trim() : null
      };
    });
    
    console.log('Login form state:', loginState);
    
    // Test 2: Try to fill and submit login form
    if (loginState.hasEmailField && loginState.hasPasswordField) {
      console.log('Step 2: Testing login form submission...');
      await page.fill('input[type="email"]', 'test@example.com');
      await page.fill('input[type="password"]', 'password123');
      await page.waitForTimeout(1000);
      
      const afterFill = await page.evaluate(() => {
        const submitButton = document.querySelector('button[type="submit"]');
        return {
          submitButtonDisabled: submitButton ? submitButton.hasAttribute('disabled') : false,
          emailValue: (document.querySelector('input[type="email"]') as HTMLInputElement)?.value,
          passwordValue: (document.querySelector('input[type="password"]') as HTMLInputElement)?.value
        };
      });
      
      console.log('After filling login form:', afterFill);
      
      if (!afterFill.submitButtonDisabled) {
        console.log('Step 3: Submitting login form...');
        await page.click('button[type="submit"]');
        await page.waitForTimeout(3000);
        await page.screenshot({ path: 'screenshots/fix-02-after-login-submit.png', fullPage: true });
      }
    }
    
    // Test 3: Registration form
    console.log('Step 4: Testing registration form...');
    await page.goto('http://localhost:3001/login');
    await page.waitForTimeout(2000);
    
    // Switch to registration
    const signUpButton = page.locator('button:has-text("Sign up")');
    if (await signUpButton.count() > 0) {
      await signUpButton.click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'screenshots/fix-03-registration-form.png', fullPage: true });
      
      const regState = await page.evaluate(() => {
        const firstNameField = document.querySelector('input[name="firstName"]');
        const lastNameField = document.querySelector('input[name="lastName"]');
        const emailField = document.querySelector('input[type="email"]');
        const passwordField = document.querySelector('input[type="password"]');
        const confirmPasswordField = document.querySelector('input[name="confirmPassword"]');
        const phoneField = document.querySelector('input[name="phone"]');
        const submitButton = document.querySelector('button[type="submit"]');
        
        return {
          hasFirstNameField: !!firstNameField,
          hasLastNameField: !!lastNameField,
          hasEmailField: !!emailField,
          hasPasswordField: !!passwordField,
          hasConfirmPasswordField: !!confirmPasswordField,
          hasPhoneField: !!phoneField,
          hasSubmitButton: !!submitButton,
          submitButtonDisabled: submitButton ? submitButton.hasAttribute('disabled') : false,
          submitButtonText: submitButton ? submitButton.textContent?.trim() : null
        };
      });
      
      console.log('Registration form state:', regState);
      
      // Test 4: Try to fill and submit registration form
      if (regState.hasFirstNameField && regState.hasEmailField) {
        console.log('Step 5: Testing registration form submission...');
        await page.fill('input[name="firstName"]', 'Test');
        await page.fill('input[name="lastName"]', 'User');
        await page.fill('input[type="email"]', 'testuser@example.com');
        await page.fill('input[type="password"]', 'Password123!');
        await page.fill('input[name="confirmPassword"]', 'Password123!');
        await page.fill('input[name="phone"]', '1234567890');
        await page.waitForTimeout(1000);
        
        const afterRegFill = await page.evaluate(() => {
          const submitButton = document.querySelector('button[type="submit"]');
          return {
            submitButtonDisabled: submitButton ? submitButton.hasAttribute('disabled') : false,
            firstNameValue: (document.querySelector('input[name="firstName"]') as HTMLInputElement)?.value,
            emailValue: (document.querySelector('input[type="email"]') as HTMLInputElement)?.value
          };
        });
        
        console.log('After filling registration form:', afterRegFill);
        
        if (!afterRegFill.submitButtonDisabled) {
          console.log('Step 6: Submitting registration form...');
          await page.click('button[type="submit"]');
          await page.waitForTimeout(5000);
          await page.screenshot({ path: 'screenshots/fix-04-after-registration-submit.png', fullPage: true });
        }
      }
    }
    
    console.log('✅ FORM FIX TEST COMPLETE');
  });
});