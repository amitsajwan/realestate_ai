import { test, expect } from '@playwright/test';

test.describe('Full System Integration Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('authState', JSON.stringify({
        isAuthenticated: true,
        user: { id: 'test-user-id', email: 'test@example.com', role: 'admin' }
      }));
    });
  });

  test('should complete full user journey - registration to property publishing', async ({ page }) => {
    // Step 1: Registration
    await page.goto('/register');
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.fill('input[name="phone"]', '+1234567890');
    await page.fill('input[name="password"]', 'Password123!');
    await page.fill('input[name="confirmPassword"]', 'Password123!');
    await page.click('button[type="submit"]');
    
    // Should redirect to onboarding
    await expect(page).toHaveURL('/onboarding');
    
    // Step 2: Complete onboarding
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="phone"]', '+1234567890');
    await page.click('button[data-testid="next-button"]');
    
    await page.fill('input[name="company"]', 'Test Real Estate');
    await page.fill('input[name="position"]', 'Senior Agent');
    await page.fill('input[name="licenseNumber"]', 'RE123456');
    await page.click('button[data-testid="next-button"]');
    
    await page.click('button[data-testid="generate-branding"]');
    await page.waitForSelector('[data-testid="branding-suggestions"]', { timeout: 10000 });
    await page.click('button[data-testid="next-button"]');
    
    await page.fill('input[name="facebookUrl"]', 'https://facebook.com/johndoe');
    await page.fill('input[name="instagramUrl"]', 'https://instagram.com/johndoe');
    await page.fill('input[name="linkedinUrl"]', 'https://linkedin.com/in/johndoe');
    await page.click('button[data-testid="next-button"]');
    
    await page.check('input[name="acceptTerms"]');
    await page.check('input[name="acceptPrivacy"]');
    await page.click('button[data-testid="next-button"]');
    
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test-photo.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.from('fake-image-data')
    });
    await page.click('button[data-testid="complete-button"]');
    
    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    
    // Step 3: Create property
    await page.click('text=Add Property');
    await page.fill('input[name="title"]', 'Beautiful 3BR Apartment');
    await page.fill('textarea[name="description"]', 'Spacious apartment with modern amenities');
    await page.fill('input[name="price"]', '500000');
    await page.fill('input[name="location"]', '123 Main St, New York, NY');
    await page.selectOption('select[name="propertyType"]', 'apartment');
    await page.click('button[data-testid="next-step"]');
    
    await page.fill('input[name="bedrooms"]', '3');
    await page.fill('input[name="bathrooms"]', '2');
    await page.fill('input[name="areaSqft"]', '1200');
    await page.click('button[data-testid="next-step"]');
    
    await page.click('button[data-testid="next-step"]');
    await page.click('button[data-testid="next-step"]');
    await page.click('button[data-testid="create-property"]');
    
    // Should show success message
    await expect(page.locator('text=Property created successfully')).toBeVisible();
    
    // Step 4: Create and publish post
    await page.click('text=AI Tools');
    await page.click('button[data-testid="create-post"]');
    
    await page.fill('input[name="title"]', 'Amazing 3BR Apartment Available');
    await page.fill('textarea[name="content"]', 'Beautiful apartment with modern amenities in prime location');
    await page.selectOption('select[name="propertyId"]', 'property-1');
    await page.selectOption('select[name="language"]', 'en');
    
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    await page.check('input[name="channels"][value="linkedin"]');
    
    await page.click('button[data-testid="publish-now"]');
    await page.click('button[data-testid="confirm-publish"]');
    
    // Should show success message
    await expect(page.locator('text=Post published successfully')).toBeVisible();
  });

  test('should complete full agent workflow - profile to analytics', async ({ page }) => {
    // Step 1: Set up agent profile
    await page.click('text=Profile');
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.fill('input[name="phone"]', '+1234567890');
    await page.fill('textarea[name="bio"]', 'Professional real estate agent with 10+ years of experience');
    await page.click('button[data-testid="save-profile"]');
    
    // Should show success message
    await expect(page.locator('text=Profile saved successfully')).toBeVisible();
    
    // Step 2: Set up public website
    await page.click('text=Public Website');
    await page.fill('input[name="agent_name"]', 'John Doe');
    await page.fill('textarea[name="bio"]', 'Professional real estate agent with 10+ years of experience');
    await page.fill('input[name="phone"]', '+1234567890');
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.fill('input[name="office_address"]', '123 Main St, New York, NY 10001');
    await page.fill('input[name="specialties"]', 'Residential, Commercial, Luxury');
    await page.fill('input[name="experience"]', '10+ years in real estate');
    await page.fill('input[name="languages"]', 'English, Spanish');
    await page.check('input[name="is_public"]');
    await page.click('button[data-testid="save-public-profile"]');
    
    // Should show success message
    await expect(page.locator('text=Public profile updated successfully')).toBeVisible();
    
    // Step 3: View analytics
    await page.click('text=Analytics');
    await expect(page.locator('text=Analytics Dashboard')).toBeVisible();
    await expect(page.locator('[data-testid="analytics-dashboard"]')).toBeVisible();
  });

  test('should complete full CRM workflow - lead to conversion', async ({ page }) => {
    // Step 1: Create lead
    await page.click('text=CRM');
    await page.click('button[data-testid="add-lead"]');
    
    await page.fill('input[name="name"]', 'Jane Smith');
    await page.fill('input[name="email"]', 'jane.smith@example.com');
    await page.fill('input[name="phone"]', '+1234567891');
    await page.selectOption('select[name="status"]', 'new');
    await page.selectOption('select[name="source"]', 'website');
    await page.selectOption('select[name="priority"]', 'high');
    await page.fill('input[name="propertyInterest"]', '3BR Apartment');
    await page.fill('input[name="budget"]', '500000');
    await page.selectOption('select[name="timeline"]', '3 months');
    await page.fill('textarea[name="notes"]', 'Looking for family home');
    await page.click('button[data-testid="save-lead"]');
    
    // Should show success message
    await expect(page.locator('text=Lead created successfully')).toBeVisible();
    
    // Step 2: Update lead status
    await page.selectOption('[data-testid="lead-item"] select[name="status"]', 'contacted');
    await expect(page.locator('[data-testid="lead-item"][data-status="contacted"]')).toBeVisible();
    
    // Step 3: Add lead activity
    await page.click('[data-testid="lead-item"]');
    await page.click('button[data-testid="add-activity"]');
    
    await page.selectOption('select[name="activityType"]', 'call');
    await page.fill('textarea[name="description"]', 'Called client to discuss property requirements');
    await page.fill('input[name="scheduledAt"]', '2024-12-31T10:00');
    await page.click('button[data-testid="save-activity"]');
    
    // Should show success message
    await expect(page.locator('text=Activity added successfully')).toBeVisible();
  });

  test('should complete full team management workflow', async ({ page }) => {
    // Step 1: Invite team member
    await page.click('text=Team Management');
    await page.click('button[data-testid="invite-member"]');
    
    await page.fill('input[name="email"]', 'new.member@example.com');
    await page.fill('input[name="name"]', 'New Member');
    await page.selectOption('select[name="role"]', 'agent');
    await page.check('input[name="permissions"][value="read"]');
    await page.check('input[name="permissions"][value="write"]');
    await page.fill('textarea[name="message"]', 'Welcome to our team!');
    await page.click('button[data-testid="send-invitation"]');
    
    // Should show success message
    await expect(page.locator('text=Invitation sent successfully')).toBeVisible();
    
    // Step 2: Edit team member
    await page.click('[data-testid="member-item"] button[data-testid="edit-member"]');
    await page.selectOption('select[name="role"]', 'agent');
    await page.click('button[data-testid="save-member"]');
    
    // Should show success message
    await expect(page.locator('text=Member updated successfully')).toBeVisible();
  });

  test('should complete full AI content generation workflow', async ({ page }) => {
    // Step 1: Generate AI content
    await page.click('text=AI Tools');
    await page.click('button[data-testid="generate-content"]');
    
    await page.fill('textarea[name="prompt"]', 'Create an engaging social media post for a luxury apartment');
    await page.selectOption('select[name="contentType"]', 'social_media');
    await page.selectOption('select[name="tone"]', 'professional');
    await page.selectOption('select[name="language"]', 'en');
    await page.fill('input[name="propertyId"]', 'property-1');
    await page.fill('input[name="targetAudience"]', 'Young professionals and families');
    await page.click('button[data-testid="generate-ai-content"]');
    
    // Wait for content to generate
    await page.waitForSelector('[data-testid="ai-generated-content"]', { timeout: 10000 });
    
    // Should show generated content
    await expect(page.locator('[data-testid="ai-generated-content"]')).toBeVisible();
    
    // Step 2: Edit and save content
    await page.fill('textarea[name="generatedContent"]', 'Updated content with custom modifications');
    await page.click('button[data-testid="save-content"]');
    
    // Should show success message
    await expect(page.locator('text=Content saved successfully')).toBeVisible();
  });

  test('should complete full multi-channel publishing workflow', async ({ page }) => {
    // Step 1: Configure channels
    await page.click('text=AI Tools');
    await page.check('input[name="channels"][value="facebook"]');
    await page.click('button[data-testid="configure-facebook"]');
    
    await page.fill('input[name="pageId"]', '123456789');
    await page.fill('input[name="accessToken"]', 'fb_access_token_123');
    await page.check('input[name="autoPost"]');
    await page.check('input[name="includeHashtags"]');
    await page.fill('textarea[name="customMessage"]', 'Check out this amazing property!');
    await page.click('button[data-testid="save-configuration"]');
    
    // Should show success message
    await expect(page.locator('text=Configuration saved successfully')).toBeVisible();
    
    // Step 2: Publish to multiple channels
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    await page.check('input[name="channels"][value="linkedin"]');
    await page.check('input[name="channels"][value="twitter"]');
    
    await page.fill('textarea[name="content"]', 'Beautiful 3BR apartment available now!');
    await page.fill('input[name="hashtags"]', '#RealEstate #Apartment #Luxury');
    
    await page.click('button[data-testid="publish-post"]');
    await page.click('button[data-testid="confirm-publish"]');
    
    // Should show success message
    await expect(page.locator('text=Post published successfully to all channels')).toBeVisible();
  });

  test('should handle cross-component data flow', async ({ page }) => {
    // Step 1: Create property
    await page.click('text=Add Property');
    await page.fill('input[name="title"]', 'Beautiful 3BR Apartment');
    await page.fill('textarea[name="description"]', 'Spacious apartment with modern amenities');
    await page.fill('input[name="price"]', '500000');
    await page.fill('input[name="location"]', '123 Main St, New York, NY');
    await page.selectOption('select[name="propertyType"]', 'apartment');
    await page.click('button[data-testid="next-step"]');
    
    await page.fill('input[name="bedrooms"]', '3');
    await page.fill('input[name="bathrooms"]', '2');
    await page.fill('input[name="areaSqft"]', '1200');
    await page.click('button[data-testid="next-step"]');
    await page.click('button[data-testid="next-step"]');
    await page.click('button[data-testid="next-step"]');
    await page.click('button[data-testid="create-property"]');
    
    // Step 2: Create post referencing the property
    await page.click('text=AI Tools');
    await page.click('button[data-testid="create-post"]');
    
    await page.fill('input[name="title"]', 'Amazing 3BR Apartment Available');
    await page.fill('textarea[name="content"]', 'Beautiful apartment with modern amenities in prime location');
    await page.selectOption('select[name="propertyId"]', 'property-1');
    await page.selectOption('select[name="language"]', 'en');
    
    // Step 3: Generate AI content for the property
    await page.check('input[name="aiGenerated"]');
    await page.fill('textarea[name="aiPrompt"]', 'Create an engaging social media post for this property');
    await page.click('button[data-testid="generate-ai-content"]');
    
    // Wait for AI content to generate
    await page.waitForSelector('[data-testid="ai-generated-content"]', { timeout: 10000 });
    
    // Step 4: Publish to multiple channels
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    await page.check('input[name="channels"][value="linkedin"]');
    
    await page.click('button[data-testid="publish-now"]');
    await page.click('button[data-testid="confirm-publish"]');
    
    // Should show success message
    await expect(page.locator('text=Post published successfully')).toBeVisible();
    
    // Step 5: View analytics
    await page.click('text=Analytics');
    await expect(page.locator('text=Analytics Dashboard')).toBeVisible();
    
    // Step 6: Check CRM for leads
    await page.click('text=CRM');
    await expect(page.locator('text=CRM Dashboard')).toBeVisible();
  });

  test('should handle error recovery across components', async ({ page }) => {
    // Mock API error
    await page.route('**/api/v1/properties', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Service unavailable' })
      });
    });
    
    // Try to create property
    await page.click('text=Add Property');
    await page.fill('input[name="title"]', 'Beautiful 3BR Apartment');
    await page.fill('textarea[name="description"]', 'Spacious apartment with modern amenities');
    await page.fill('input[name="price"]', '500000');
    await page.fill('input[name="location"]', '123 Main St, New York, NY');
    await page.selectOption('select[name="propertyType"]', 'apartment');
    await page.click('button[data-testid="next-step"]');
    
    await page.fill('input[name="bedrooms"]', '3');
    await page.fill('input[name="bathrooms"]', '2');
    await page.fill('input[name="areaSqft"]', '1200');
    await page.click('button[data-testid="next-step"]');
    await page.click('button[data-testid="next-step"]');
    await page.click('button[data-testid="next-step"]');
    await page.click('button[data-testid="create-property"]');
    
    // Should show error message
    await expect(page.locator('text=Failed to create property')).toBeVisible();
    
    // Should show retry button
    await expect(page.locator('button[data-testid="retry-create-property"]')).toBeVisible();
  });

  test('should maintain state across navigation', async ({ page }) => {
    // Step 1: Start creating property
    await page.click('text=Add Property');
    await page.fill('input[name="title"]', 'Beautiful 3BR Apartment');
    await page.fill('textarea[name="description"]', 'Spacious apartment with modern amenities');
    await page.fill('input[name="price"]', '500000');
    await page.fill('input[name="location"]', '123 Main St, New York, NY');
    await page.selectOption('select[name="propertyType"]', 'apartment');
    
    // Step 2: Navigate away and back
    await page.click('text=Dashboard');
    await page.click('text=Add Property');
    
    // Should maintain form data
    await expect(page.locator('input[name="title"]')).toHaveValue('Beautiful 3BR Apartment');
    await expect(page.locator('textarea[name="description"]')).toHaveValue('Spacious apartment with modern amenities');
    await expect(page.locator('input[name="price"]')).toHaveValue('500000');
    await expect(page.locator('input[name="location"]')).toHaveValue('123 Main St, New York, NY');
    await expect(page.locator('select[name="propertyType"]')).toHaveValue('apartment');
  });

  test('should handle concurrent user actions', async ({ page }) => {
    // Step 1: Start multiple actions simultaneously
    await page.click('text=Add Property');
    await page.fill('input[name="title"]', 'Beautiful 3BR Apartment');
    await page.fill('textarea[name="description"]', 'Spacious apartment with modern amenities');
    await page.fill('input[name="price"]', '500000');
    await page.fill('input[name="location"]', '123 Main St, New York, NY');
    await page.selectOption('select[name="propertyType"]', 'apartment');
    
    // Step 2: Open another form in parallel
    await page.click('text=AI Tools');
    await page.click('button[data-testid="create-post"]');
    
    // Step 3: Both forms should be accessible
    await expect(page.locator('[data-testid="post-creation-form"]')).toBeVisible();
    
    // Step 4: Go back to property form
    await page.click('text=Add Property');
    await expect(page.locator('[data-testid="property-form"]')).toBeVisible();
    
    // Step 5: Form data should be preserved
    await expect(page.locator('input[name="title"]')).toHaveValue('Beautiful 3BR Apartment');
  });
});