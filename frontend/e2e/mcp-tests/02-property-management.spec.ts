import { test, expect } from '@playwright/test';

/**
 * Natural Language Test: Property Management Flow
 * ==============================================
 * 
 * Test Description: "User can create, view, edit, and delete properties"
 * 
 * This test validates the complete property management journey:
 * - Create new property with all required fields
 * - View property in the properties list
 * - Edit property details
 * - Delete property
 * - Search and filter properties
 */

test.describe('Property Management Flow - Natural Language Testing', () => {
  test.beforeEach(async ({ page }) => {
    // Natural Language: "Login as authenticated user"
    await page.goto('/login');
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*dashboard/);
  });
  
  test('User can create and manage properties', async ({ page }) => {
    // Natural Language: "Navigate to properties management page"
    await page.click('text=Properties');
    await expect(page).toHaveURL(/.*properties/);
    
    // Natural Language: "Click add new property button"
    await page.click('button[data-testid="add-property-button"]');
    await expect(page.locator('text=Add New Property')).toBeVisible();
    
    // Natural Language: "Fill property form with complete details"
    await page.fill('input[name="title"]', 'Luxury Villa in Mumbai');
    await page.fill('textarea[name="description"]', 'Beautiful 4BHK villa with garden and pool');
    await page.fill('input[name="price"]', '15000000');
    await page.selectOption('select[name="propertyType"]', 'villa');
    await page.fill('input[name="location"]', 'Bandra West, Mumbai');
    await page.fill('input[name="bedrooms"]', '4');
    await page.fill('input[name="bathrooms"]', '3');
    await page.fill('input[name="areaSqft"]', '2500');
    
    // Natural Language: "Add property amenities and features"
    await page.check('input[name="amenities"][value="parking"]');
    await page.check('input[name="amenities"][value="garden"]');
    await page.check('input[name="amenities"][value="pool"]');
    await page.check('input[name="features"][value="modular_kitchen"]');
    await page.check('input[name="features"][value="wooden_flooring"]');
    
    // Natural Language: "Submit property and verify it was created"
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Property created successfully')).toBeVisible();
    
    // Natural Language: "Verify property appears in properties list"
    await expect(page.locator('text=Luxury Villa in Mumbai')).toBeVisible();
    await expect(page.locator('text=₹1,50,00,000')).toBeVisible();
    
    // Natural Language: "Edit the created property"
    await page.click('button[data-testid="edit-property-button"]');
    await page.fill('input[name="title"]', 'Updated Luxury Villa in Mumbai');
    await page.fill('input[name="price"]', '16000000');
    await page.click('button[type="submit"]');
    
    // Natural Language: "Verify property was updated"
    await expect(page.locator('text=Property updated successfully')).toBeVisible();
    await expect(page.locator('text=Updated Luxury Villa in Mumbai')).toBeVisible();
    await expect(page.locator('text=₹1,60,00,000')).toBeVisible();
    
    // Natural Language: "Search for the property"
    await page.fill('input[placeholder*="Search properties"]', 'Luxury Villa');
    await expect(page.locator('text=Updated Luxury Villa in Mumbai')).toBeVisible();
    
    // Natural Language: "Delete the property"
    await page.click('button[data-testid="delete-property-button"]');
    await page.click('button[data-testid="confirm-delete"]');
    await expect(page.locator('text=Property deleted successfully')).toBeVisible();
    await expect(page.locator('text=Updated Luxury Villa in Mumbai')).not.toBeVisible();
  });
});
