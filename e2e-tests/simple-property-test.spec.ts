import { test, expect } from '@playwright/test';

test.describe('Property Form Evidence', () => {
  test('Show property addition form without authentication', async ({ page }) => {
    console.log('=== Capturing Property Form Evidence ===');
    
    // Navigate directly to the smart form demo page (bypasses auth)
    console.log('Step 1: Navigating to Smart Form Demo page');
    await page.goto('/demo/smart-form');
    await page.waitForLoadState('networkidle');
    
    // Take screenshot of the page
    await page.screenshot({ path: 'property-form-evidence.png', fullPage: true });
    console.log('✓ Screenshot captured: property-form-evidence.png');
    
    // Verify we can see the form
    await expect(page.locator('h1:has-text("Smart Property Form Demo")')).toBeVisible();
    console.log('✓ Smart Form Demo page loaded');
    
    // Check for the wizard form
    await expect(page.locator('h2:has-text("Smart Property Form")')).toBeVisible();
    console.log('✓ Property form is visible');
    
    // Check for form steps
    await expect(page.locator('text=Step 1 of 3')).toBeVisible();
    console.log('✓ Form shows step progression');
    
    // Check for form fields
    const addressField = page.locator('input[placeholder*="address"], input[placeholder*="Address"]').first();
    await expect(addressField).toBeVisible();
    console.log('✓ Address field is visible');
    
    // Check for Next button (Add Property button appears on step 3)
    const nextButton = page.locator('button:has-text("Next")').first();
    await expect(nextButton).toBeVisible();
    console.log('✓ Next button is visible');
    
    // Try to fill out the form
    console.log('Step 2: Filling out property form');
    await addressField.fill('123 Test Street, Mumbai');
    
    // Look for property type field (it's a select dropdown)
    const typeField = page.locator('select[name="propertyType"]').first();
    if (await typeField.isVisible()) {
      await typeField.selectOption('Apartment');
      console.log('✓ Property type field filled');
    }
    
    console.log('✓ Form fields filled successfully');
    
    // Take another screenshot after filling
    await page.screenshot({ path: 'property-form-filled.png', fullPage: true });
    console.log('✓ Screenshot captured: property-form-filled.png');
    
    console.log('=== Property Form Evidence Collection Complete ===');
  });

  test('Show wizard navigation', async ({ page }) => {
    console.log('=== Capturing Wizard Navigation Evidence ===');
    
    // Navigate to smart form demo
    await page.goto('/demo/smart-form');
    await page.waitForLoadState('networkidle');
    
    // Take initial screenshot
    await page.screenshot({ path: 'wizard-step1.png', fullPage: true });
    console.log('✓ Step 1 screenshot captured');
    
    // Fill step 1 and proceed
    const addressField = page.locator('input[placeholder*="address"], input[placeholder*="Address"]').first();
    await addressField.fill('456 Demo Avenue, Delhi');
    
    // Look for property type field (it's a select dropdown)
    const typeField = page.locator('select[name="propertyType"]').first();
    if (await typeField.isVisible()) {
      await typeField.selectOption('Villa');
    }
    
    // Click Next button
    const nextButton = page.locator('button:has-text("Next")');
    if (await nextButton.isVisible()) {
      await nextButton.click();
      await page.waitForTimeout(1000);
      
      await page.screenshot({ path: 'wizard-step2.png', fullPage: true });
      console.log('✓ Step 2 screenshot captured');
    }
    
    console.log('=== Wizard Navigation Evidence Complete ===');
  });
});