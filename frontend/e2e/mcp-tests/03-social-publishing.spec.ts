import { test, expect } from '@playwright/test';

/**
 * Natural Language Test: Social Media Publishing Flow
 * ==================================================
 * 
 * Test Description: "User can generate AI content and publish to social media"
 * 
 * This test validates the complete social publishing journey:
 * - Select property for social media promotion
 * - Generate AI-powered content for different platforms
 * - Preview and customize the generated content
 * - Publish to multiple social media platforms
 * - Track publishing status and analytics
 */

test.describe('Social Media Publishing Flow - Natural Language Testing', () => {
  test.beforeEach(async ({ page }) => {
    // Natural Language: "Login and navigate to properties"
    await page.goto('/login');
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.click('button[type="submit"]');
    await page.click('text=Properties');
  });
  
  test('User can generate and publish AI content', async ({ page }) => {
    // Natural Language: "Select a property for social media promotion"
    await page.click('button[data-testid="promote-property-button"]');
    await expect(page.locator('text=Social Media Publishing')).toBeVisible();
    
    // Natural Language: "Choose target platforms for promotion"
    await page.check('input[name="platforms"][value="facebook"]');
    await page.check('input[name="platforms"][value="instagram"]');
    await page.check('input[name="platforms"][value="linkedin"]');
    
    // Natural Language: "Select content tone and style"
    await page.selectOption('select[name="tone"]', 'luxury');
    await page.selectOption('select[name="language"]', 'en');
    await page.selectOption('select[name="length"]', 'medium');
    
    // Natural Language: "Generate AI-powered content"
    await page.click('button[data-testid="generate-content-button"]');
    await expect(page.locator('text=Generating content')).toBeVisible();
    
    // Wait for AI generation to complete
    await expect(page.locator('text=Content generated successfully')).toBeVisible({ timeout: 30000 });
    
    // Natural Language: "Preview generated content for each platform"
    await expect(page.locator('[data-testid="facebook-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="instagram-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="linkedin-preview"]')).toBeVisible();
    
    // Natural Language: "Customize content if needed"
    await page.click('button[data-testid="edit-facebook-content"]');
    await page.fill('textarea[name="facebook-content"]', 'Customized Facebook content with property highlights');
    await page.click('button[data-testid="save-content"]');
    
    // Natural Language: "Schedule or publish immediately"
    await page.selectOption('select[name="publish-option"]', 'immediate');
    
    // Natural Language: "Publish to all selected platforms"
    await page.click('button[data-testid="publish-all-button"]');
    await expect(page.locator('text=Publishing to social media')).toBeVisible();
    
    // Natural Language: "Verify publishing status and success"
    await expect(page.locator('text=Published successfully to Facebook')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('text=Published successfully to Instagram')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('text=Published successfully to LinkedIn')).toBeVisible({ timeout: 30000 });
    
    // Natural Language: "Navigate to publishing history"
    await page.click('text=Publishing History');
    await expect(page.locator('text=Recent Publications')).toBeVisible();
    
    // Natural Language: "Verify published posts appear in history"
    await expect(page.locator('text=Facebook Post')).toBeVisible();
    await expect(page.locator('text=Instagram Post')).toBeVisible();
    await expect(page.locator('text=LinkedIn Post')).toBeVisible();
  });
  
  test('User can save content as draft', async ({ page }) => {
    // Natural Language: "Start social media publishing process"
    await page.click('button[data-testid="promote-property-button"]');
    
    // Natural Language: "Generate content but save as draft instead of publishing"
    await page.check('input[name="platforms"][value="facebook"]');
    await page.selectOption('select[name="tone"]', 'friendly');
    await page.click('button[data-testid="generate-content-button"]');
    await expect(page.locator('text=Content generated successfully')).toBeVisible({ timeout: 30000 });
    
    // Natural Language: "Save as draft instead of publishing"
    await page.click('button[data-testid="save-draft-button"]');
    await expect(page.locator('text=Draft saved successfully')).toBeVisible();
    
    // Natural Language: "Navigate to drafts and verify content was saved"
    await page.click('text=Drafts');
    await expect(page.locator('text=Saved Drafts')).toBeVisible();
    await expect(page.locator('text=Facebook Draft')).toBeVisible();
  });
});
