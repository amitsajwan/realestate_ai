import { test, expect } from '@playwright/test';

test.describe('AI Content Generation System', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication and navigate to dashboard
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('authState', JSON.stringify({
        isAuthenticated: true,
        user: { id: 'test-user-id', email: 'test@example.com' }
      }));
    });

    // Mock AI content generation data
    await page.route('**/api/v1/posts/generate-ai-content', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            title: 'Stunning 3BR Apartment in Prime Location',
            content: 'Discover this beautiful 3-bedroom apartment featuring modern amenities, spacious living areas, and a prime location. Perfect for families looking for comfort and convenience.',
            hashtags: ['#RealEstate', '#Apartment', '#ModernLiving', '#PrimeLocation'],
            suggestions: [
              'Highlight the modern kitchen features',
              'Emphasize the proximity to schools and shopping',
              'Mention the building amenities'
            ]
          }
        })
      });
    });
  });

  test('should display AI content generation interface', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Check if AI content generation is visible
    await expect(page.locator('text=AI Content Generation')).toBeVisible();
    await expect(page.locator('[data-testid="ai-content-generator"]')).toBeVisible();
  });

  test('should open AI content generation form', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Click generate content button
    await page.click('button[data-testid="generate-content"]');
    
    // Check if AI form is visible
    await expect(page.locator('[data-testid="ai-content-form"]')).toBeVisible();
    await expect(page.locator('text=Generate AI Content')).toBeVisible();
  });

  test('should fill AI content generation form', async ({ page }) => {
    // Navigate to AI Tools and open form
    await page.click('text=AI Tools');
    await page.click('button[data-testid="generate-content"]');
    
    // Fill form details
    await page.fill('textarea[name="prompt"]', 'Create an engaging social media post for a luxury apartment');
    await page.selectOption('select[name="contentType"]', 'social_media');
    await page.selectOption('select[name="tone"]', 'professional');
    await page.selectOption('select[name="language"]', 'en');
    await page.fill('input[name="propertyId"]', 'property-1');
    await page.fill('input[name="targetAudience"]', 'Young professionals and families');
  });

  test('should generate AI content', async ({ page }) => {
    // Navigate to AI Tools and open form
    await page.click('text=AI Tools');
    await page.click('button[data-testid="generate-content"]');
    
    // Fill form details
    await page.fill('textarea[name="prompt"]', 'Create an engaging social media post for a luxury apartment');
    await page.selectOption('select[name="contentType"]', 'social_media');
    await page.selectOption('select[name="tone"]', 'professional');
    await page.selectOption('select[name="language"]', 'en');
    await page.fill('input[name="propertyId"]', 'property-1');
    await page.fill('input[name="targetAudience"]', 'Young professionals and families');
    
    // Click generate button
    await page.click('button[data-testid="generate-ai-content"]');
    
    // Should show loading state
    await expect(page.locator('text=Generating AI content...')).toBeVisible();
    
    // Wait for AI content to generate
    await page.waitForSelector('[data-testid="ai-generated-content"]', { timeout: 10000 });
    
    // Should show generated content
    await expect(page.locator('[data-testid="ai-generated-content"]')).toBeVisible();
    await expect(page.locator('text=Stunning 3BR Apartment in Prime Location')).toBeVisible();
  });

  test('should display generated content details', async ({ page }) => {
    // Navigate to AI Tools and generate content
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
    
    // Check if content details are visible
    await expect(page.locator('text=Generated Title')).toBeVisible();
    await expect(page.locator('text=Generated Content')).toBeVisible();
    await expect(page.locator('text=Hashtags')).toBeVisible();
    await expect(page.locator('text=#RealEstate')).toBeVisible();
    await expect(page.locator('text=#Apartment')).toBeVisible();
    await expect(page.locator('text=#ModernLiving')).toBeVisible();
    await expect(page.locator('text=#PrimeLocation')).toBeVisible();
  });

  test('should display AI suggestions', async ({ page }) => {
    // Navigate to AI Tools and generate content
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
    
    // Check if suggestions are visible
    await expect(page.locator('[data-testid="ai-suggestions"]')).toBeVisible();
    await expect(page.locator('text=AI Suggestions')).toBeVisible();
    await expect(page.locator('text=Highlight the modern kitchen features')).toBeVisible();
    await expect(page.locator('text=Emphasize the proximity to schools and shopping')).toBeVisible();
    await expect(page.locator('text=Mention the building amenities')).toBeVisible();
  });

  test('should edit generated content', async ({ page }) => {
    // Navigate to AI Tools and generate content
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
    
    // Edit generated content
    await page.fill('textarea[name="generatedContent"]', 'Updated content with custom modifications');
    
    // Should show updated content
    await expect(page.locator('textarea[name="generatedContent"]')).toHaveValue('Updated content with custom modifications');
  });

  test('should regenerate content with different parameters', async ({ page }) => {
    // Navigate to AI Tools and generate content
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
    
    // Change tone to casual
    await page.selectOption('select[name="tone"]', 'casual');
    
    // Regenerate content
    await page.click('button[data-testid="regenerate-content"]');
    
    // Should show loading state
    await expect(page.locator('text=Regenerating AI content...')).toBeVisible();
    
    // Wait for new content to generate
    await page.waitForSelector('[data-testid="ai-generated-content"]', { timeout: 10000 });
    
    // Should show new content
    await expect(page.locator('[data-testid="ai-generated-content"]')).toBeVisible();
  });

  test('should save generated content', async ({ page }) => {
    // Navigate to AI Tools and generate content
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
    
    // Save content
    await page.click('button[data-testid="save-content"]');
    
    // Should show success message
    await expect(page.locator('text=Content saved successfully')).toBeVisible();
  });

  test('should copy content to clipboard', async ({ page }) => {
    // Navigate to AI Tools and generate content
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
    
    // Copy content
    await page.click('button[data-testid="copy-content"]');
    
    // Should show success message
    await expect(page.locator('text=Content copied to clipboard')).toBeVisible();
  });

  test('should handle AI generation failure', async ({ page }) => {
    // Mock AI service failure
    await page.route('**/api/v1/posts/generate-ai-content', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'AI service unavailable' })
      });
    });
    
    // Navigate to AI Tools and open form
    await page.click('text=AI Tools');
    await page.click('button[data-testid="generate-content"]');
    
    // Fill form details
    await page.fill('textarea[name="prompt"]', 'Create an engaging social media post for a luxury apartment');
    await page.selectOption('select[name="contentType"]', 'social_media');
    await page.selectOption('select[name="tone"]', 'professional');
    await page.selectOption('select[name="language"]', 'en');
    await page.fill('input[name="propertyId"]', 'property-1');
    await page.fill('input[name="targetAudience"]', 'Young professionals and families');
    
    // Click generate button
    await page.click('button[data-testid="generate-ai-content"]');
    
    // Should show error message
    await expect(page.locator('text=Failed to generate AI content')).toBeVisible();
    await expect(page.locator('button[data-testid="retry-generation"]')).toBeVisible();
  });

  test('should retry AI generation on failure', async ({ page }) => {
    // Mock AI service failure first, then success
    let retryCount = 0;
    await page.route('**/api/v1/posts/generate-ai-content', route => {
      if (retryCount === 0) {
        retryCount++;
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'AI service unavailable' })
        });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            data: {
              title: 'Stunning 3BR Apartment in Prime Location',
              content: 'Discover this beautiful 3-bedroom apartment featuring modern amenities, spacious living areas, and a prime location. Perfect for families looking for comfort and convenience.',
              hashtags: ['#RealEstate', '#Apartment', '#ModernLiving', '#PrimeLocation'],
              suggestions: [
                'Highlight the modern kitchen features',
                'Emphasize the proximity to schools and shopping',
                'Mention the building amenities'
              ]
            }
          })
        });
      }
    });
    
    // Navigate to AI Tools and open form
    await page.click('text=AI Tools');
    await page.click('button[data-testid="generate-content"]');
    
    // Fill form details
    await page.fill('textarea[name="prompt"]', 'Create an engaging social media post for a luxury apartment');
    await page.selectOption('select[name="contentType"]', 'social_media');
    await page.selectOption('select[name="tone"]', 'professional');
    await page.selectOption('select[name="language"]', 'en');
    await page.fill('input[name="propertyId"]', 'property-1');
    await page.fill('input[name="targetAudience"]', 'Young professionals and families');
    
    // Click generate button
    await page.click('button[data-testid="generate-ai-content"]');
    
    // Should show error message
    await expect(page.locator('text=Failed to generate AI content')).toBeVisible();
    
    // Click retry button
    await page.click('button[data-testid="retry-generation"]');
    
    // Should generate content successfully
    await expect(page.locator('[data-testid="ai-generated-content"]')).toBeVisible();
  });

  test('should validate form inputs', async ({ page }) => {
    // Navigate to AI Tools and open form
    await page.click('text=AI Tools');
    await page.click('button[data-testid="generate-content"]');
    
    // Try to generate without filling required fields
    await page.click('button[data-testid="generate-ai-content"]');
    
    // Should show validation errors
    await expect(page.locator('text=Prompt is required')).toBeVisible();
    await expect(page.locator('text=Content type is required')).toBeVisible();
    await expect(page.locator('text=Tone is required')).toBeVisible();
    await expect(page.locator('text=Language is required')).toBeVisible();
  });

  test('should display content templates', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Check if content templates are visible
    await expect(page.locator('[data-testid="content-templates"]')).toBeVisible();
    await expect(page.locator('text=Content Templates')).toBeVisible();
    await expect(page.locator('text=Social Media Post')).toBeVisible();
    await expect(page.locator('text=Property Description')).toBeVisible();
    await expect(page.locator('text=Email Campaign')).toBeVisible();
    await expect(page.locator('text=Blog Post')).toBeVisible();
  });

  test('should use content template', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Click on social media post template
    await page.click('[data-testid="template-social-media"]');
    
    // Should open form with template pre-filled
    await expect(page.locator('[data-testid="ai-content-form"]')).toBeVisible();
    await expect(page.locator('select[name="contentType"]')).toHaveValue('social_media');
  });

  test('should display content history', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Check if content history is visible
    await expect(page.locator('[data-testid="content-history"]')).toBeVisible();
    await expect(page.locator('text=Content History')).toBeVisible();
  });

  test('should load previous content', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Click on previous content item
    await page.click('[data-testid="content-history-item"]');
    
    // Should load previous content
    await expect(page.locator('[data-testid="ai-generated-content"]')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Check if AI content generation is still usable on mobile
    await expect(page.locator('[data-testid="ai-content-generator"]')).toBeVisible();
    await expect(page.locator('button[data-testid="generate-content"]')).toBeVisible();
  });

  test('should display content quality score', async ({ page }) => {
    // Navigate to AI Tools and generate content
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
    
    // Check if quality score is visible
    await expect(page.locator('[data-testid="content-quality-score"]')).toBeVisible();
    await expect(page.locator('text=Content Quality Score')).toBeVisible();
    await expect(page.locator('text=85%')).toBeVisible();
  });

  test('should display content optimization tips', async ({ page }) => {
    // Navigate to AI Tools and generate content
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
    
    // Check if optimization tips are visible
    await expect(page.locator('[data-testid="optimization-tips"]')).toBeVisible();
    await expect(page.locator('text=Optimization Tips')).toBeVisible();
    await expect(page.locator('text=Consider adding more emotional appeal')).toBeVisible();
    await expect(page.locator('text=Include a call-to-action')).toBeVisible();
  });
});