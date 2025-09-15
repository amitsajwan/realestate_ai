import { test, expect } from '@playwright/test';

test.describe('Onboarding Process', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication state
    await page.goto('/onboarding');
    
    // Mock user data
    await page.evaluate(() => {
      localStorage.setItem('authState', JSON.stringify({
        isAuthenticated: true,
        user: {
          id: 'test-user-id',
          email: 'test@example.com',
          firstName: 'John',
          lastName: 'Doe'
        }
      }));
    });
  });

  test('should display onboarding steps correctly', async ({ page }) => {
    // Check if step indicators are visible
    await expect(page.locator('[data-testid="step-indicator"]')).toBeVisible();
    
    // Check if first step is active
    await expect(page.locator('[data-testid="step-1"]')).toHaveClass(/active/);
    
    // Check if step titles are visible
    await expect(page.locator('text=Personal Info')).toBeVisible();
    await expect(page.locator('text=Company')).toBeVisible();
    await expect(page.locator('text=AI Branding')).toBeVisible();
    await expect(page.locator('text=Social')).toBeVisible();
    await expect(page.locator('text=Terms')).toBeVisible();
    await expect(page.locator('text=Photo')).toBeVisible();
  });

  test('should complete step 1 - Personal Info', async ({ page }) => {
    // Fill personal information
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="phone"]', '+1234567890');
    
    // Click next button
    await page.click('button[data-testid="next-button"]');
    
    // Should move to step 2
    await expect(page.locator('[data-testid="step-2"]')).toHaveClass(/active/);
    await expect(page.locator('text=Company Information')).toBeVisible();
  });

  test('should complete step 2 - Company Info', async ({ page }) => {
    // Navigate to step 2
    await page.click('button[data-testid="next-button"]');
    
    // Fill company information
    await page.fill('input[name="company"]', 'Test Real Estate');
    await page.fill('input[name="position"]', 'Senior Agent');
    await page.fill('input[name="licenseNumber"]', 'RE123456');
    
    // Click next button
    await page.click('button[data-testid="next-button"]');
    
    // Should move to step 3
    await expect(page.locator('[data-testid="step-3"]')).toHaveClass(/active/);
    await expect(page.locator('text=AI Branding')).toBeVisible();
  });

  test('should complete step 3 - AI Branding', async ({ page }) => {
    // Navigate to step 3
    await page.click('button[data-testid="next-button"]');
    await page.click('button[data-testid="next-button"]');
    
    // Check if AI branding section is visible
    await expect(page.locator('text=AI Branding Suggestions')).toBeVisible();
    
    // Click generate branding button
    await page.click('button[data-testid="generate-branding"]');
    
    // Should show loading state
    await expect(page.locator('text=Generating AI suggestions...')).toBeVisible();
    
    // Wait for AI suggestions to load
    await page.waitForSelector('[data-testid="branding-suggestions"]', { timeout: 10000 });
    
    // Should show branding suggestions
    await expect(page.locator('[data-testid="branding-suggestions"]')).toBeVisible();
    
    // Click next button
    await page.click('button[data-testid="next-button"]');
    
    // Should move to step 4
    await expect(page.locator('[data-testid="step-4"]')).toHaveClass(/active/);
  });

  test('should complete step 4 - Social Media', async ({ page }) => {
    // Navigate to step 4
    await page.click('button[data-testid="next-button"]');
    await page.click('button[data-testid="next-button"]');
    await page.click('button[data-testid="next-button"]');
    
    // Fill social media information
    await page.fill('input[name="facebookUrl"]', 'https://facebook.com/johndoe');
    await page.fill('input[name="instagramUrl"]', 'https://instagram.com/johndoe');
    await page.fill('input[name="linkedinUrl"]', 'https://linkedin.com/in/johndoe');
    await page.fill('input[name="twitterUrl"]', 'https://twitter.com/johndoe');
    
    // Click next button
    await page.click('button[data-testid="next-button"]');
    
    // Should move to step 5
    await expect(page.locator('[data-testid="step-5"]')).toHaveClass(/active/);
  });

  test('should complete step 5 - Terms and Conditions', async ({ page }) => {
    // Navigate to step 5
    await page.click('button[data-testid="next-button"]');
    await page.click('button[data-testid="next-button"]');
    await page.click('button[data-testid="next-button"]');
    await page.click('button[data-testid="next-button"]');
    
    // Check terms and conditions
    await expect(page.locator('text=Terms and Conditions')).toBeVisible();
    
    // Accept terms
    await page.check('input[name="acceptTerms"]');
    await page.check('input[name="acceptPrivacy"]');
    await page.check('input[name="acceptMarketing"]');
    
    // Click next button
    await page.click('button[data-testid="next-button"]');
    
    // Should move to step 6
    await expect(page.locator('[data-testid="step-6"]')).toHaveClass(/active/);
  });

  test('should complete step 6 - Photo Upload', async ({ page }) => {
    // Navigate to step 6
    await page.click('button[data-testid="next-button"]');
    await page.click('button[data-testid="next-button"]');
    await page.click('button[data-testid="next-button"]');
    await page.click('button[data-testid="next-button"]');
    await page.click('button[data-testid="next-button"]');
    
    // Check photo upload section
    await expect(page.locator('text=Upload Profile Photo')).toBeVisible();
    
    // Upload a test image
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test-photo.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.from('fake-image-data')
    });
    
    // Should show image preview
    await expect(page.locator('[data-testid="image-preview"]')).toBeVisible();
    
    // Click complete button
    await page.click('button[data-testid="complete-button"]');
    
    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
  });

  test('should allow going back to previous steps', async ({ page }) => {
    // Navigate to step 2
    await page.click('button[data-testid="next-button"]');
    
    // Click back button
    await page.click('button[data-testid="back-button"]');
    
    // Should go back to step 1
    await expect(page.locator('[data-testid="step-1"]')).toHaveClass(/active/);
    await expect(page.locator('text=Personal Information')).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    // Try to proceed without filling required fields
    await page.click('button[data-testid="next-button"]');
    
    // Should show validation errors
    await expect(page.locator('text=First name is required')).toBeVisible();
    await expect(page.locator('text=Last name is required')).toBeVisible();
    await expect(page.locator('text=Phone number is required')).toBeVisible();
  });

  test('should show progress indicator', async ({ page }) => {
    // Check if progress bar is visible
    await expect(page.locator('[data-testid="progress-bar"]')).toBeVisible();
    
    // Check initial progress
    await expect(page.locator('[data-testid="progress-bar"]')).toHaveAttribute('aria-valuenow', '16');
    
    // Complete step 1
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="phone"]', '+1234567890');
    await page.click('button[data-testid="next-button"]');
    
    // Check updated progress
    await expect(page.locator('[data-testid="progress-bar"]')).toHaveAttribute('aria-valuenow', '33');
  });

  test('should handle AI branding generation failure', async ({ page }) => {
    // Navigate to step 3
    await page.click('button[data-testid="next-button"]');
    await page.click('button[data-testid="next-button"]');
    
    // Mock API failure
    await page.route('**/api/v1/branding/suggestions', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'AI service unavailable' })
      });
    });
    
    // Click generate branding button
    await page.click('button[data-testid="generate-branding"]');
    
    // Should show error message
    await expect(page.locator('text=Failed to generate branding suggestions')).toBeVisible();
    
    // Should allow manual input
    await page.fill('input[name="tagline"]', 'Your Trusted Real Estate Partner');
    await page.fill('textarea[name="about"]', 'Professional real estate services');
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check if onboarding is still usable on mobile
    await expect(page.locator('[data-testid="step-indicator"]')).toBeVisible();
    await expect(page.locator('input[name="firstName"]')).toBeVisible();
    await expect(page.locator('button[data-testid="next-button"]')).toBeVisible();
  });

  test('should save progress between steps', async ({ page }) => {
    // Fill step 1 data
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="phone"]', '+1234567890');
    
    // Navigate to step 2
    await page.click('button[data-testid="next-button"]');
    
    // Go back to step 1
    await page.click('button[data-testid="back-button"]');
    
    // Check if data is preserved
    await expect(page.locator('input[name="firstName"]')).toHaveValue('John');
    await expect(page.locator('input[name="lastName"]')).toHaveValue('Doe');
    await expect(page.locator('input[name="phone"]')).toHaveValue('+1234567890');
  });
});