import { test, expect } from '@playwright/test';

test.describe('Post Creation Evidence', () => {
  test('Show post creation form', async ({ page }) => {
    console.log('=== Capturing Post Creation Evidence ===');
    
    // Navigate to the AI Content Generator page
    console.log('Step 1: Navigating to AI Content Generator page');
    await page.goto('/demo/ai-content');
    await page.waitForLoadState('networkidle');
    
    // Take screenshot of the page
    await page.screenshot({ path: 'post-creation-evidence.png', fullPage: true });
    console.log('✓ Screenshot captured: post-creation-evidence.png');
    
    // Check if we can see post creation elements
    const pageTitle = page.locator('h1, h2, h3').first();
    if (await pageTitle.isVisible()) {
      const title = await pageTitle.textContent();
      console.log(`✓ Page title: ${title}`);
    }
    
    // Look for any form elements
    const forms = page.locator('form');
    const formCount = await forms.count();
    console.log(`✓ Found ${formCount} form(s) on the page`);
    
    // Look for input fields
    const inputs = page.locator('input, textarea, select');
    const inputCount = await inputs.count();
    console.log(`✓ Found ${inputCount} input field(s) on the page`);
    
    // Look for buttons
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    console.log(`✓ Found ${buttonCount} button(s) on the page`);
    
    console.log('=== Post Creation Evidence Collection Complete ===');
  });

  test('Show property promotion flow', async ({ page }) => {
    console.log('=== Capturing Property Promotion Evidence ===');
    
    // Navigate to the main dashboard to see promotion options
    console.log('Step 1: Navigating to dashboard');
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Take screenshot of the page
    await page.screenshot({ path: 'property-promotion-evidence.png', fullPage: true });
    console.log('✓ Screenshot captured: property-promotion-evidence.png');
    
    // Check what's visible on the page
    const pageContent = page.locator('body');
    const content = await pageContent.textContent();
    console.log(`✓ Page content preview: ${content?.substring(0, 200)}...`);
    
    console.log('=== Property Promotion Evidence Collection Complete ===');
  });
});