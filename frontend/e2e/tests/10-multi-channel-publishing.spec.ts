import { test, expect } from '@playwright/test';

test.describe('Multi-Channel Publishing System', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication and navigate to dashboard
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('authState', JSON.stringify({
        isAuthenticated: true,
        user: { id: 'test-user-id', email: 'test@example.com' }
      }));
    });

    // Mock publishing data
    await page.route('**/api/v1/posts/*/publish', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            facebook: { status: 'published', post_id: 'fb_123', url: 'https://facebook.com/posts/fb_123' },
            instagram: { status: 'published', post_id: 'ig_123', url: 'https://instagram.com/p/ig_123' },
            linkedin: { status: 'published', post_id: 'li_123', url: 'https://linkedin.com/posts/li_123' },
            twitter: { status: 'published', post_id: 'tw_123', url: 'https://twitter.com/status/tw_123' }
          }
        })
      });
    });
  });

  test('should display multi-channel publishing interface', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Check if multi-channel publishing is visible
    await expect(page.locator('text=Multi-Channel Publishing')).toBeVisible();
    await expect(page.locator('[data-testid="multi-channel-publishing"]')).toBeVisible();
  });

  test('should display available channels', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Check if channels are visible
    await expect(page.locator('[data-testid="publishing-channels"]')).toBeVisible();
    await expect(page.locator('text=Facebook')).toBeVisible();
    await expect(page.locator('text=Instagram')).toBeVisible();
    await expect(page.locator('text=LinkedIn')).toBeVisible();
    await expect(page.locator('text=Twitter')).toBeVisible();
  });

  test('should select publishing channels', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Select channels
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    await page.check('input[name="channels"][value="linkedin"]');
    
    // Should show selected channels
    await expect(page.locator('input[name="channels"][value="facebook"]')).toBeChecked();
    await expect(page.locator('input[name="channels"][value="instagram"]')).toBeChecked();
    await expect(page.locator('input[name="channels"][value="linkedin"]')).toBeChecked();
  });

  test('should configure channel settings', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Select Facebook channel
    await page.check('input[name="channels"][value="facebook"]');
    
    // Click configure button
    await page.click('button[data-testid="configure-facebook"]');
    
    // Should open configuration modal
    await expect(page.locator('[data-testid="channel-config-modal"]')).toBeVisible();
    await expect(page.locator('text=Facebook Configuration')).toBeVisible();
  });

  test('should fill channel configuration', async ({ page }) => {
    // Navigate to AI Tools and open Facebook configuration
    await page.click('text=AI Tools');
    await page.check('input[name="channels"][value="facebook"]');
    await page.click('button[data-testid="configure-facebook"]');
    
    // Fill configuration details
    await page.fill('input[name="pageId"]', '123456789');
    await page.fill('input[name="accessToken"]', 'fb_access_token_123');
    await page.check('input[name="autoPost"]');
    await page.check('input[name="includeHashtags"]');
    await page.fill('textarea[name="customMessage"]', 'Check out this amazing property!');
  });

  test('should save channel configuration', async ({ page }) => {
    // Navigate to AI Tools and open Facebook configuration
    await page.click('text=AI Tools');
    await page.check('input[name="channels"][value="facebook"]');
    await page.click('button[data-testid="configure-facebook"]');
    
    // Fill configuration details
    await page.fill('input[name="pageId"]', '123456789');
    await page.fill('input[name="accessToken"]', 'fb_access_token_123');
    await page.check('input[name="autoPost"]');
    await page.check('input[name="includeHashtags"]');
    await page.fill('textarea[name="customMessage"]', 'Check out this amazing property!');
    
    // Save configuration
    await page.click('button[data-testid="save-configuration"]');
    
    // Should show success message
    await expect(page.locator('text=Configuration saved successfully')).toBeVisible();
  });

  test('should preview post for different channels', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Select multiple channels
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    await page.check('input[name="channels"][value="linkedin"]');
    await page.check('input[name="channels"][value="twitter"]');
    
    // Fill post content
    await page.fill('textarea[name="content"]', 'Beautiful 3BR apartment available now!');
    await page.fill('input[name="hashtags"]', '#RealEstate #Apartment #Luxury');
    
    // Click preview button
    await page.click('button[data-testid="preview-post"]');
    
    // Should show preview modal
    await expect(page.locator('[data-testid="preview-modal"]')).toBeVisible();
    await expect(page.locator('text=Post Preview')).toBeVisible();
  });

  test('should display channel-specific previews', async ({ page }) => {
    // Navigate to AI Tools and open preview
    await page.click('text=AI Tools');
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    await page.check('input[name="channels"][value="linkedin"]');
    await page.check('input[name="channels"][value="twitter"]');
    await page.fill('textarea[name="content"]', 'Beautiful 3BR apartment available now!');
    await page.fill('input[name="hashtags"]', '#RealEstate #Apartment #Luxury');
    await page.click('button[data-testid="preview-post"]');
    
    // Check if channel previews are visible
    await expect(page.locator('[data-testid="facebook-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="instagram-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="linkedin-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="twitter-preview"]')).toBeVisible();
  });

  test('should publish to selected channels', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Select channels
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    await page.check('input[name="channels"][value="linkedin"]');
    await page.check('input[name="channels"][value="twitter"]');
    
    // Fill post content
    await page.fill('textarea[name="content"]', 'Beautiful 3BR apartment available now!');
    await page.fill('input[name="hashtags"]', '#RealEstate #Apartment #Luxury');
    
    // Publish post
    await page.click('button[data-testid="publish-post"]');
    
    // Should show confirmation dialog
    await expect(page.locator('[data-testid="publish-confirmation"]')).toBeVisible();
    await expect(page.locator('text=Are you sure you want to publish to all selected channels?')).toBeVisible();
    
    // Confirm publication
    await page.click('button[data-testid="confirm-publish"]');
    
    // Should show success message
    await expect(page.locator('text=Post published successfully to all channels')).toBeVisible();
  });

  test('should display publishing status', async ({ page }) => {
    // Navigate to AI Tools and publish post
    await page.click('text=AI Tools');
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    await page.check('input[name="channels"][value="linkedin"]');
    await page.check('input[name="channels"][value="twitter"]');
    await page.fill('textarea[name="content"]', 'Beautiful 3BR apartment available now!');
    await page.fill('input[name="hashtags"]', '#RealEstate #Apartment #Luxury');
    await page.click('button[data-testid="publish-post"]');
    await page.click('button[data-testid="confirm-publish"]');
    
    // Should show publishing status
    await expect(page.locator('[data-testid="publishing-status"]')).toBeVisible();
    await expect(page.locator('text=Publishing Status')).toBeVisible();
    await expect(page.locator('text=Facebook: Published')).toBeVisible();
    await expect(page.locator('text=Instagram: Published')).toBeVisible();
    await expect(page.locator('text=LinkedIn: Published')).toBeVisible();
    await expect(page.locator('text=Twitter: Published')).toBeVisible();
  });

  test('should display published post links', async ({ page }) => {
    // Navigate to AI Tools and publish post
    await page.click('text=AI Tools');
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    await page.check('input[name="channels"][value="linkedin"]');
    await page.check('input[name="channels"][value="twitter"]');
    await page.fill('textarea[name="content"]', 'Beautiful 3BR apartment available now!');
    await page.fill('input[name="hashtags"]', '#RealEstate #Apartment #Luxury');
    await page.click('button[data-testid="publish-post"]');
    await page.click('button[data-testid="confirm-publish"]');
    
    // Should show published post links
    await expect(page.locator('[data-testid="published-links"]')).toBeVisible();
    await expect(page.locator('text=Published Links')).toBeVisible();
    await expect(page.locator('a[href="https://facebook.com/posts/fb_123"]')).toBeVisible();
    await expect(page.locator('a[href="https://instagram.com/p/ig_123"]')).toBeVisible();
    await expect(page.locator('a[href="https://linkedin.com/posts/li_123"]')).toBeVisible();
    await expect(page.locator('a[href="https://twitter.com/status/tw_123"]')).toBeVisible();
  });

  test('should schedule post for later', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Select channels
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    await page.check('input[name="channels"][value="linkedin"]');
    await page.check('input[name="channels"][value="twitter"]');
    
    // Fill post content
    await page.fill('textarea[name="content"]', 'Beautiful 3BR apartment available now!');
    await page.fill('input[name="hashtags"]', '#RealEstate #Apartment #Luxury');
    
    // Enable scheduling
    await page.check('input[name="scheduled"]');
    await page.fill('input[name="scheduledAt"]', '2024-12-31T10:00');
    
    // Schedule post
    await page.click('button[data-testid="schedule-post"]');
    
    // Should show success message
    await expect(page.locator('text=Post scheduled successfully')).toBeVisible();
  });

  test('should handle publishing failure', async ({ page }) => {
    // Mock publishing failure
    await page.route('**/api/v1/posts/*/publish', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Publishing failed' })
      });
    });
    
    // Navigate to AI Tools and publish post
    await page.click('text=AI Tools');
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    await page.fill('textarea[name="content"]', 'Beautiful 3BR apartment available now!');
    await page.fill('input[name="hashtags"]', '#RealEstate #Apartment #Luxury');
    await page.click('button[data-testid="publish-post"]');
    await page.click('button[data-testid="confirm-publish"]');
    
    // Should show error message
    await expect(page.locator('text=Failed to publish post')).toBeVisible();
    await expect(page.locator('button[data-testid="retry-publish"]')).toBeVisible();
  });

  test('should retry failed publishing', async ({ page }) => {
    // Mock publishing failure first, then success
    let retryCount = 0;
    await page.route('**/api/v1/posts/*/publish', route => {
      if (retryCount === 0) {
        retryCount++;
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Publishing failed' })
        });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            data: {
              facebook: { status: 'published', post_id: 'fb_123', url: 'https://facebook.com/posts/fb_123' },
              instagram: { status: 'published', post_id: 'ig_123', url: 'https://instagram.com/p/ig_123' }
            }
          })
        });
      }
    });
    
    // Navigate to AI Tools and publish post
    await page.click('text=AI Tools');
    await page.check('input[name="channels"][value="facebook"]');
    await page.check('input[name="channels"][value="instagram"]');
    await page.fill('textarea[name="content"]', 'Beautiful 3BR apartment available now!');
    await page.fill('input[name="hashtags"]', '#RealEstate #Apartment #Luxury');
    await page.click('button[data-testid="publish-post"]');
    await page.click('button[data-testid="confirm-publish"]');
    
    // Should show error message
    await expect(page.locator('text=Failed to publish post')).toBeVisible();
    
    // Click retry button
    await page.click('button[data-testid="retry-publish"]');
    
    // Should publish successfully
    await expect(page.locator('text=Post published successfully to all channels')).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Try to publish without selecting channels
    await page.fill('textarea[name="content"]', 'Beautiful 3BR apartment available now!');
    await page.click('button[data-testid="publish-post"]');
    
    // Should show validation error
    await expect(page.locator('text=Please select at least one channel')).toBeVisible();
  });

  test('should display channel analytics', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Check if channel analytics are visible
    await expect(page.locator('[data-testid="channel-analytics"]')).toBeVisible();
    await expect(page.locator('text=Channel Analytics')).toBeVisible();
    await expect(page.locator('text=Facebook Performance')).toBeVisible();
    await expect(page.locator('text=Instagram Performance')).toBeVisible();
    await expect(page.locator('text=LinkedIn Performance')).toBeVisible();
    await expect(page.locator('text=Twitter Performance')).toBeVisible();
  });

  test('should display engagement metrics', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Check if engagement metrics are visible
    await expect(page.locator('[data-testid="engagement-metrics"]')).toBeVisible();
    await expect(page.locator('text=Total Views')).toBeVisible();
    await expect(page.locator('text=Total Likes')).toBeVisible();
    await expect(page.locator('text=Total Shares')).toBeVisible();
    await expect(page.locator('text=Total Comments')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Check if multi-channel publishing is still usable on mobile
    await expect(page.locator('[data-testid="multi-channel-publishing"]')).toBeVisible();
    await expect(page.locator('[data-testid="publishing-channels"]')).toBeVisible();
  });

  test('should display publishing history', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Check if publishing history is visible
    await expect(page.locator('[data-testid="publishing-history"]')).toBeVisible();
    await expect(page.locator('text=Publishing History')).toBeVisible();
  });

  test('should display post performance', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Click on previous post
    await page.click('[data-testid="publishing-history-item"]');
    
    // Should show post performance
    await expect(page.locator('[data-testid="post-performance"]')).toBeVisible();
    await expect(page.locator('text=Post Performance')).toBeVisible();
    await expect(page.locator('text=Views')).toBeVisible();
    await expect(page.locator('text=Engagement')).toBeVisible();
    await expect(page.locator('text=Reach')).toBeVisible();
  });

  test('should display channel comparison', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Check if channel comparison is visible
    await expect(page.locator('[data-testid="channel-comparison"]')).toBeVisible();
    await expect(page.locator('text=Channel Comparison')).toBeVisible();
  });

  test('should export publishing data', async ({ page }) => {
    // Navigate to AI Tools
    await page.click('text=AI Tools');
    
    // Click export button
    await page.click('button[data-testid="export-publishing-data"]');
    
    // Should show export options
    await expect(page.locator('[data-testid="export-options"]')).toBeVisible();
    await expect(page.locator('text=Export as CSV')).toBeVisible();
    await expect(page.locator('text=Export as Excel')).toBeVisible();
  });
});