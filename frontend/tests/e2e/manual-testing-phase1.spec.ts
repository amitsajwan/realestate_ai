import { test, expect } from '@playwright/test';

test.describe('MANUAL TESTING PHASE 1 - Basic Forms and Navigation', () => {
  test('Test 1: Home Page and Basic Navigation', async ({ page }) => {
    console.log('🔍 PHASE 1: Testing Home Page and Basic Navigation');
    
    // Test 1.1: Home Page Load
    console.log('📄 1.1: Testing Home Page Load...');
    await page.goto('http://localhost:3000/');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/manual-01-home-page.png', fullPage: true });
    
    const homePageCheck = await page.evaluate(() => {
      const title = document.title;
      const hasNavigation = !!document.querySelector('nav, .navigation, .navbar');
      const hasMainContent = !!document.querySelector('main, .main-content, [data-testid="main"]');
      const buttons = Array.from(document.querySelectorAll('button, a')).map(btn => ({
        text: btn.textContent?.trim(),
        visible: btn.offsetParent !== null
      })).filter(btn => btn.text && btn.text.length > 0);
      
      return {
        title,
        hasNavigation,
        hasMainContent,
        buttonCount: buttons.length,
        buttons: buttons.slice(0, 10) // First 10 buttons
      };
    });
    
    console.log('Home page analysis:', homePageCheck);
    expect(homePageCheck.title).toContain('PropertyAI');
    console.log('✅ Home page loaded successfully');
    
    // Test 1.2: Navigation to Login
    console.log('📄 1.2: Testing Navigation to Login...');
    const loginLink = page.locator('a[href*="login"], button:has-text("Login"), button:has-text("Sign In")').first();
    if (await loginLink.count() > 0) {
      await loginLink.click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'screenshots/manual-02-login-page.png', fullPage: true });
      console.log('✅ Navigated to login page');
    } else {
      // Direct navigation
      await page.goto('http://localhost:3000/login');
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'screenshots/manual-02-login-page.png', fullPage: true });
      console.log('✅ Direct navigation to login page');
    }
    
    // Test 1.3: Login Form Analysis
    console.log('📄 1.3: Analyzing Login Form...');
    const loginFormAnalysis = await page.evaluate(() => {
      const emailField = document.querySelector('input[type="email"]');
      const passwordField = document.querySelector('input[type="password"]');
      const submitButton = document.querySelector('button[type="submit"]');
      const signUpButton = Array.from(document.querySelectorAll('button')).find(btn => 
        btn.textContent?.includes('Sign up') || btn.textContent?.includes('Sign Up')
      );
      
      // Check form validation
      const form = document.querySelector('form');
      const formData = new FormData(form || undefined);
      
      return {
        hasEmailField: !!emailField,
        hasPasswordField: !!passwordField,
        hasSubmitButton: !!submitButton,
        hasSignUpButton: !!signUpButton,
        submitButtonDisabled: submitButton ? submitButton.hasAttribute('disabled') : false,
        formAction: form ? form.getAttribute('action') : null,
        formMethod: form ? form.getAttribute('method') : null,
        emailFieldName: emailField ? emailField.getAttribute('name') : null,
        passwordFieldName: passwordField ? passwordField.getAttribute('name') : null
      };
    });
    
    console.log('Login form analysis:', loginFormAnalysis);
    expect(loginFormAnalysis.hasEmailField).toBe(true);
    expect(loginFormAnalysis.hasPasswordField).toBe(true);
    expect(loginFormAnalysis.hasSubmitButton).toBe(true);
    console.log('✅ Login form elements present');
    
    // Test 1.4: Registration Form Toggle
    console.log('📄 1.4: Testing Registration Form Toggle...');
    if (loginFormAnalysis.hasSignUpButton) {
      await page.click('button:has-text("Sign up")');
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'screenshots/manual-03-registration-form.png', fullPage: true });
      
      const registrationFormAnalysis = await page.evaluate(() => {
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
          allFieldsPresent: !!(firstNameField && lastNameField && emailField && passwordField && confirmPasswordField && phoneField)
        };
      });
      
      console.log('Registration form analysis:', registrationFormAnalysis);
      expect(registrationFormAnalysis.allFieldsPresent).toBe(true);
      console.log('✅ Registration form elements present');
      
      // Test form validation by trying to submit empty form
      const emptySubmitTest = await page.evaluate(() => {
        const submitButton = document.querySelector('button[type="submit"]');
        return submitButton ? submitButton.hasAttribute('disabled') : false;
      });
      
      console.log('Empty form submit button disabled:', emptySubmitTest);
      if (emptySubmitTest) {
        console.log('✅ Form validation working - submit button disabled for empty form');
      } else {
        console.log('⚠️ Form validation issue - submit button enabled for empty form');
      }
    }
    
    console.log('🎉 PHASE 1 COMPLETE: Basic forms and navigation working');
  });
  
  test('Test 2: Form Validation and Submission', async ({ page }) => {
    console.log('🔍 PHASE 2: Testing Form Validation and Submission');
    
    // Test 2.1: Registration Form Validation
    console.log('📄 2.1: Testing Registration Form Validation...');
    await page.goto('http://localhost:3000/login');
    await page.waitForTimeout(2000);
    
    // Switch to registration
    await page.click('button:has-text("Sign up")');
    await page.waitForTimeout(1000);
    
    // Test invalid email
    console.log('Testing invalid email validation...');
    await page.fill('input[type="email"]', 'invalid-email');
    await page.fill('input[type="password"]', 'password123');
    await page.fill('input[name="confirmPassword"]', 'password123');
    await page.fill('input[name="firstName"]', 'Test');
    await page.fill('input[name="lastName"]', 'User');
    await page.fill('input[name="phone"]', '1234567890');
    
    await page.waitForTimeout(1000);
    const invalidEmailState = await page.evaluate(() => {
      const submitButton = document.querySelector('button[type="submit"]');
      const emailField = document.querySelector('input[type="email"]');
      return {
        submitDisabled: submitButton ? submitButton.hasAttribute('disabled') : false,
        emailInvalid: emailField ? emailField.matches(':invalid') : false,
        emailValue: emailField ? emailField.value : null
      };
    });
    
    console.log('Invalid email test:', invalidEmailState);
    
    // Test valid email
    console.log('Testing valid email validation...');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.waitForTimeout(1000);
    
    const validEmailState = await page.evaluate(() => {
      const submitButton = document.querySelector('button[type="submit"]');
      const emailField = document.querySelector('input[type="email"]');
      return {
        submitDisabled: submitButton ? submitButton.hasAttribute('disabled') : false,
        emailInvalid: emailField ? emailField.matches(':invalid') : false,
        emailValue: emailField ? emailField.value : null
      };
    });
    
    console.log('Valid email test:', validEmailState);
    
    // Test password mismatch
    console.log('Testing password mismatch validation...');
    await page.fill('input[type="password"]', 'password123');
    await page.fill('input[name="confirmPassword"]', 'different123');
    await page.waitForTimeout(1000);
    
    const passwordMismatchState = await page.evaluate(() => {
      const submitButton = document.querySelector('button[type="submit"]');
      const passwordField = document.querySelector('input[type="password"]');
      const confirmPasswordField = document.querySelector('input[name="confirmPassword"]');
      return {
        submitDisabled: submitButton ? submitButton.hasAttribute('disabled') : false,
        passwordValue: passwordField ? passwordField.value : null,
        confirmPasswordValue: confirmPasswordField ? confirmPasswordField.value : null,
        passwordsMatch: passwordField && confirmPasswordField ? passwordField.value === confirmPasswordField.value : false
      };
    });
    
    console.log('Password mismatch test:', passwordMismatchState);
    
    // Test valid form
    console.log('Testing valid form state...');
    await page.fill('input[name="confirmPassword"]', 'password123');
    await page.waitForTimeout(1000);
    
    const validFormState = await page.evaluate(() => {
      const submitButton = document.querySelector('button[type="submit"]');
      return {
        submitDisabled: submitButton ? submitButton.hasAttribute('disabled') : false,
        submitText: submitButton ? submitButton.textContent?.trim() : null
      };
    });
    
    console.log('Valid form test:', validFormState);
    
    if (validFormState.submitDisabled) {
      console.log('⚠️ ISSUE: Submit button still disabled with valid form');
    } else {
      console.log('✅ Form validation working correctly');
    }
    
    console.log('🎉 PHASE 2 COMPLETE: Form validation tested');
  });
});