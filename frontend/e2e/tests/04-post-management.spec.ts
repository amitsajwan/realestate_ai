import { test, expect } from '@playwright/test';

test.describe('Post Management System', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication and navigate to dashboard
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('authState', JSON.stringify({
        isAuthenticated: true,
        user: { id: 'test-user-id', email: 'test@example.com' }
      }));
    });
  });

  test('should display post management dashboard', async ({ page }) => {
    // Navigate to post management
    await page.click('text=AI Tools');
    
    // Check if post management interface is visible
    await expect(page.locator('text=Post Management')).toBeVisible();
    await expect(page.locator('button[data-testid="create-post"]')).toBeVisible();
    await expect(page.locator('[data-testid="post-list"]')).toBeVisible();
  });

  test('should create new post', async ({ page }) => {
    // Navigate to post management
    await page.click('text=AI Tools');
    
    // Click create post button
    await page.click('button[data-testid="create-post"]');
    
    // Check if post creation form is visible
    await expect(page.locator('[data-testid="post-creation-form"]')).toBeVisible();
    await expect(page.locator('text=Create New Post')).toBeVisible();
  });

  test('should fill post creation form', async ({ page }) => {
    // Navigate to post management and open creation form
    await page.click('text=AI Tools');
    await page.click('button[data-testid="create-post"]');
    
    // Fill post details
    await page.fill('input[name="title"]', 'Amazing 3BR Apartment Available');
    await page.fill('textarea[name="content"]', 'Beautiful apartment with modern amenities in prime location');
    await page.selectOption('select[name="propertyId"]', 'property-1');
    await page.selectOption('select[name="language"]', 'en');
    
    // Select publishing channels
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    await page.check('input[name="channels"][value="linkedin"]');
    
    // Set scheduling
    await page.check('input[name="scheduled"]');
    await page.fill('input[name="scheduledAt"]', '2024-12-31T10:00');
    
    // Enable AI generation
    await page.check('input[name="aiGenerated"]');
    await page.fill('textarea[name="aiPrompt"]', 'Create an engaging social media post for this property');
  });

  test('should generate AI content', async ({ page }) => {
    // Navigate to post management and open creation form
    await page.click('text=AI Tools');
    await page.click('button[data-testid="create-post"]');
    
    // Fill basic post details
    await page.fill('input[name="title"]', 'Amazing 3BR Apartment Available');
    await page.selectOption('select[name="propertyId"]', 'property-1');
    await page.selectOption('select[name="language"]', 'en');
    
    // Enable AI generation
    await page.check('input[name="aiGenerated"]');
    await page.fill('textarea[name="aiPrompt"]', 'Create an engaging social media post for this property');
    
    // Click generate AI content button
    await page.click('button[data-testid="generate-ai-content"]');
    
    // Should show loading state
    await expect(page.locator('text=Generating AI content...')).toBeVisible();
    
    // Wait for AI content to generate
    await page.waitForSelector('[data-testid="ai-generated-content"]', { timeout: 10000 });
    
    // Should show generated content
    await expect(page.locator('[data-testid="ai-generated-content"]')).toBeVisible();
    await expect(page.locator('textarea[name="content"]')).not.toBeEmpty();
  });

  test('should preview post for different channels', async ({ page }) => {
    // Navigate to post management and open creation form
    await page.click('text=AI Tools');
    await page.click('button[data-testid="create-post"]');
    
    // Fill post details
    await page.fill('input[name="title"]', 'Amazing 3BR Apartment Available');
    await page.fill('textarea[name="content"]', 'Beautiful apartment with modern amenities in prime location');
    await page.selectOption('select[name="propertyId"]', 'property-1');
    await page.selectOption('select[name="language"]', 'en');
    
    // Select multiple channels
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    await page.check('input[name="channels"][value="linkedin"]');
    await page.check('input[name="channels"][value="twitter"]');
    
    // Click preview button
    await page.click('button[data-testid="preview-post"]');
    
    // Should show preview modal
    await expect(page.locator('[data-testid="post-preview-modal"]')).toBeVisible();
    
    // Check if all channel previews are shown
    await expect(page.locator('[data-testid="facebook-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="instagram-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="linkedin-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="twitter-preview"]')).toBeVisible();
  });

  test('should save post as draft', async ({ page }) => {
    // Navigate to post management and open creation form
    await page.click('text=AI Tools');
    await page.click('button[data-testid="create-post"]');
    
    // Fill post details
    await page.fill('input[name="title"]', 'Amazing 3BR Apartment Available');
    await page.fill('textarea[name="content"]', 'Beautiful apartment with modern amenities in prime location');
    await page.selectOption('select[name="propertyId"]', 'property-1');
    await page.selectOption('select[name="language"]', 'en');
    
    // Save as draft
    await page.click('button[data-testid="save-draft"]');
    
    // Should show success message
    await expect(page.locator('text=Post saved as draft')).toBeVisible();
    
    // Should close form and return to post list
    await expect(page.locator('[data-testid="post-list"]')).toBeVisible();
  });

  test('should publish post immediately', async ({ page }) => {
    // Navigate to post management and open creation form
    await page.click('text=AI Tools');
    await page.click('button[data-testid="create-post"]');
    
    // Fill post details
    await page.fill('input[name="title"]', 'Amazing 3BR Apartment Available');
    await page.fill('textarea[name="content"]', 'Beautiful apartment with modern amenities in prime location');
    await page.selectOption('select[name="propertyId"]', 'property-1');
    await page.selectOption('select[name="language"]', 'en');
    
    // Select publishing channels
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    
    // Publish immediately
    await page.click('button[data-testid="publish-now"]');
    
    // Should show confirmation dialog
    await expect(page.locator('[data-testid="publish-confirmation"]')).toBeVisible();
    await expect(page.locator('text=Are you sure you want to publish this post?')).toBeVisible();
    
    // Confirm publication
    await page.click('button[data-testid="confirm-publish"]');
    
    // Should show success message
    await expect(page.locator('text=Post published successfully')).toBeVisible();
  });

  test('should schedule post for later', async ({ page }) => {
    // Navigate to post management and open creation form
    await page.click('text=AI Tools');
    await page.click('button[data-testid="create-post"]');
    
    // Fill post details
    await page.fill('input[name="title"]', 'Amazing 3BR Apartment Available');
    await page.fill('textarea[name="content"]', 'Beautiful apartment with modern amenities in prime location');
    await page.selectOption('select[name="propertyId"]', 'property-1');
    await page.selectOption('select[name="language"]', 'en');
    
    // Select publishing channels
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    
    // Enable scheduling
    await page.check('input[name="scheduled"]');
    await page.fill('input[name="scheduledAt"]', '2024-12-31T10:00');
    
    // Schedule post
    await page.click('button[data-testid="schedule-post"]');
    
    // Should show success message
    await expect(page.locator('text=Post scheduled successfully')).toBeVisible();
  });

  test('should display post list with filters', async ({ page }) => {
    // Navigate to post management
    await page.click('text=AI Tools');
    
    // Check if post list is visible
    await expect(page.locator('[data-testid="post-list"]')).toBeVisible();
    
    // Check if filters are available
    await expect(page.locator('[data-testid="post-filters"]')).toBeVisible();
    await expect(page.locator('select[name="status"]')).toBeVisible();
    await expect(page.locator('select[name="language"]')).toBeVisible();
    await expect(page.locator('select[name="channel"]')).toBeVisible();
  });

  test('should filter posts by status', async ({ page }) => {
    // Navigate to post management
    await page.click('text=AI Tools');
    
    // Filter by draft status
    await page.selectOption('select[name="status"]', 'draft');
    
    // Should show only draft posts
    await expect(page.locator('[data-testid="post-item"][data-status="draft"]')).toBeVisible();
  });

  test('should filter posts by channel', async ({ page }) => {
    // Navigate to post management
    await page.click('text=AI Tools');
    
    // Filter by Facebook posts
    await page.selectOption('select[name="channel"]', 'facebook');
    
    // Should show only Facebook posts
    await expect(page.locator('[data-testid="post-item"][data-channel*="facebook"]')).toBeVisible();
  });

  test('should edit existing post', async ({ page }) => {
    // Navigate to post management
    await page.click('text=AI Tools');
    
    // Click edit button on first post
    await page.click('[data-testid="post-item"] button[data-testid="edit-post"]');
    
    // Should open edit form
    await expect(page.locator('[data-testid="edit-post-form"]')).toBeVisible();
    
    // Modify post content
    await page.fill('textarea[name="content"]', 'Updated post content');
    
    // Save changes
    await page.click('button[data-testid="save-post"]');
    
    // Should show success message
    await expect(page.locator('text=Post updated successfully')).toBeVisible();
  });

  test('should delete post', async ({ page }) => {
    // Navigate to post management
    await page.click('text=AI Tools');
    
    // Click delete button on first post
    await page.click('[data-testid="post-item"] button[data-testid="delete-post"]');
    
    // Should show confirmation dialog
    await expect(page.locator('[data-testid="delete-confirmation"]')).toBeVisible();
    await expect(page.locator('text=Are you sure you want to delete this post?')).toBeVisible();
    
    // Confirm deletion
    await page.click('button[data-testid="confirm-delete"]');
    
    // Should show success message
    await expect(page.locator('text=Post deleted successfully')).toBeVisible();
  });

  test('should view post analytics', async ({ page }) => {
    // Navigate to post management
    await page.click('text=AI Tools');
    
    // Click analytics button on first post
    await page.click('[data-testid="post-item"] button[data-testid="view-analytics"]');
    
    // Should open analytics modal
    await expect(page.locator('[data-testid="post-analytics"]')).toBeVisible();
    await expect(page.locator('text=Post Performance')).toBeVisible();
    await expect(page.locator('text=Views')).toBeVisible();
    await expect(page.locator('text=Engagement')).toBeVisible();
    await expect(page.locator('text=Shares')).toBeVisible();
  });

  test('should duplicate post', async ({ page }) => {
    // Navigate to post management
    await page.click('text=AI Tools');
    
    // Click duplicate button on first post
    await page.click('[data-testid="post-item"] button[data-testid="duplicate-post"]');
    
    // Should open creation form with pre-filled data
    await expect(page.locator('[data-testid="post-creation-form"]')).toBeVisible();
    await expect(page.locator('input[name="title"]')).not.toBeEmpty();
    await expect(page.locator('textarea[name="content"]')).not.toBeEmpty();
  });

  test('should handle AI content generation failure', async ({ page }) => {
    // Navigate to post management and open creation form
    await page.click('text=AI Tools');
    await page.click('button[data-testid="create-post"]');
    
    // Fill basic post details
    await page.fill('input[name="title"]', 'Amazing 3BR Apartment Available');
    await page.selectOption('select[name="propertyId"]', 'property-1');
    await page.selectOption('select[name="language"]', 'en');
    
    // Enable AI generation
    await page.check('input[name="aiGenerated"]');
    await page.fill('textarea[name="aiPrompt"]', 'Create an engaging social media post for this property');
    
    // Mock AI service failure
    await page.route('**/api/v1/posts/generate-ai-content', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'AI service unavailable' })
      });
    });
    
    // Click generate AI content button
    await page.click('button[data-testid="generate-ai-content"]');
    
    // Should show error message
    await expect(page.locator('text=Failed to generate AI content')).toBeVisible();
    
    // Should allow manual input
    await page.fill('textarea[name="content"]', 'Manual post content');
  });

  test('should handle publishing failure', async ({ page }) => {
    // Navigate to post management and open creation form
    await page.click('text=AI Tools');
    await page.click('button[data-testid="create-post"]');
    
    // Fill post details
    await page.fill('input[name="title"]', 'Amazing 3BR Apartment Available');
    await page.fill('textarea[name="content"]', 'Beautiful apartment with modern amenities in prime location');
    await page.selectOption('select[name="propertyId"]', 'property-1');
    await page.selectOption('select[name="language"]', 'en');
    
    // Select publishing channels
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    
    // Mock publishing failure
    await page.route('**/api/v1/posts/*/publish', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Publishing failed' })
      });
    });
    
    // Publish immediately
    await page.click('button[data-testid="publish-now"]');
    await page.click('button[data-testid="confirm-publish"]');
    
    // Should show error message
    await expect(page.locator('text=Failed to publish post')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Navigate to post management
    await page.click('text=AI Tools');
    
    // Check if post management is still usable on mobile
    await expect(page.locator('[data-testid="post-list"]')).toBeVisible();
    await expect(page.locator('button[data-testid="create-post"]')).toBeVisible();
    
    // Open post creation form
    await page.click('button[data-testid="create-post"]');
    
    // Check if form is usable on mobile
    await expect(page.locator('[data-testid="post-creation-form"]')).toBeVisible();
    await expect(page.locator('input[name="title"]')).toBeVisible();
  });
});