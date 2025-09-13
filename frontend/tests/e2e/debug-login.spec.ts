import { test, expect } from '@playwright/test';

test.describe('DEBUG LOGIN - Understanding the Issue', () => {
  test('Debug login page loading', async ({ page }) => {
    console.log('🔍 DEBUG: Understanding login page issue...');
    
    // Go to login page
    await page.goto('http://localhost:3001/login');
    await page.waitForTimeout(5000); // Wait longer for hydration
    
    // Take screenshot
    await page.screenshot({ path: 'screenshots/debug-01-login-page.png', fullPage: true });
    
    // Check what's actually on the page
    const pageState = await page.evaluate(() => {
      const loadingElement = document.querySelector('div:has-text("Loading")');
      const signUpButton = Array.from(document.querySelectorAll('button')).find(btn => 
        btn.textContent?.includes('Sign up') || btn.textContent?.includes('Sign Up')
      );
      const emailField = document.querySelector('input[type="email"]');
      const passwordField = document.querySelector('input[type="password"]');
      const submitButton = document.querySelector('button[type="submit"]');
      
      return {
        hasLoadingElement: !!loadingElement,
        loadingText: loadingElement ? loadingElement.textContent : null,
        hasSignUpButton: !!signUpButton,
        signUpButtonText: signUpButton ? signUpButton.textContent : null,
        hasEmailField: !!emailField,
        hasPasswordField: !!passwordField,
        hasSubmitButton: !!submitButton,
        allInputs: Array.from(document.querySelectorAll('input')).map(input => ({
          type: input.type,
          name: input.name,
          placeholder: input.placeholder,
          visible: input.offsetParent !== null
        }))
      };
    });
    
    console.log('Page state:', pageState);
    
    // Wait a bit more and check again
    console.log('Waiting 5 more seconds for hydration...');
    await page.waitForTimeout(5000);
    
    const pageStateAfter = await page.evaluate(() => {
      const loadingElement = document.querySelector('div:has-text("Loading")');
      const emailField = document.querySelector('input[type="email"]');
      const passwordField = document.querySelector('input[type="password"]');
      const submitButton = document.querySelector('button[type="submit"]');
      
      return {
        hasLoadingElement: !!loadingElement,
        loadingText: loadingElement ? loadingElement.textContent : null,
        hasEmailField: !!emailField,
        hasPasswordField: !!passwordField,
        hasSubmitButton: !!submitButton,
        formVisible: !!document.querySelector('form')
      };
    });
    
    console.log('Page state after wait:', pageStateAfter);
    
    // Take another screenshot
    await page.screenshot({ path: 'screenshots/debug-02-login-after-wait.png', fullPage: true });
    
    // Try to click sign up button if it exists
    if (pageState.hasSignUpButton) {
      console.log('Trying to click sign up button...');
      try {
        await page.click('button:has-text("Sign up")');
        await page.waitForTimeout(2000);
        await page.screenshot({ path: 'screenshots/debug-03-after-signup-click.png', fullPage: true });
        
        const afterSignUp = await page.evaluate(() => {
          const firstNameField = document.querySelector('input[name="firstName"]');
          const emailField = document.querySelector('input[type="email"]');
          const passwordField = document.querySelector('input[type="password"]');
          const confirmPasswordField = document.querySelector('input[name="confirmPassword"]');
          
          return {
            hasFirstNameField: !!firstNameField,
            hasEmailField: !!emailField,
            hasPasswordField: !!passwordField,
            hasConfirmPasswordField: !!confirmPasswordField,
            allInputs: Array.from(document.querySelectorAll('input')).map(input => ({
              type: input.type,
              name: input.name,
              placeholder: input.placeholder,
              visible: input.offsetParent !== null
            }))
          };
        });
        
        console.log('After sign up click:', afterSignUp);
        
      } catch (error) {
        console.log('Error clicking sign up button:', error.message);
      }
    }
    
    console.log('✅ DEBUG COMPLETE');
  });
});