import { test, expect } from '@playwright/test';

test.describe('Property Creation and Retrieval Proof', () => {
  test('should create property with correct price and retrieve it successfully', async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:3000');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Take screenshot of initial state
    await page.screenshot({ path: 'proof-initial-state.png', fullPage: true });
    
    // Navigate to property creation (assuming there's a way to get there)
    // This might be through a dashboard or direct navigation
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForLoadState('networkidle');
    
    // Look for "Add Property" button
    const addPropertyButton = page.locator('text=Add Property').first();
    await expect(addPropertyButton).toBeVisible();
    await addPropertyButton.click();
    
    // Wait for property form to load
    await page.waitForSelector('text=Add New Property', { timeout: 10000 });
    
    // Take screenshot of form start
    await page.screenshot({ path: 'proof-form-start.png', fullPage: true });
    
    // Step 1: Fill address information
    await page.fill('input[name="address"]', '123 Test Property Street');
    await page.fill('input[name="location"]', 'Test City, Test State');
    await page.click('button:has-text("Next")');
    
    // Wait for step 2
    await page.waitForSelector('text=Tell us about your property');
    await page.screenshot({ path: 'proof-step-2.png', fullPage: true });
    
    // Step 2: Fill basic property information
    await page.selectOption('select[name="propertyType"]', 'Apartment');
    await page.fill('input[name="area"]', '1200');
    await page.selectOption('select[name="bedrooms"]', '3');
    await page.selectOption('select[name="bathrooms"]', '2');
    await page.click('button:has-text("Next")');
    
    // Wait for step 3 (pricing)
    await page.waitForSelector('text=Set your price');
    await page.screenshot({ path: 'proof-step-3-pricing.png', fullPage: true });
    
    // Step 3: Fill pricing information with specific test price
    const testPrice = '5000000';
    await page.fill('input[name="price"]', testPrice);
    
    // Verify the price input is working correctly
    const priceInput = page.locator('input[name="price"]');
    await expect(priceInput).toHaveValue(5000000);
    await expect(priceInput).toHaveAttribute('type', 'number');
    
    await page.click('button:has-text("Next")');
    
    // Wait for step 4 (images)
    await page.waitForSelector('text=Add Property Images');
    await page.screenshot({ path: 'proof-step-4-images.png', fullPage: true });
    
    // Skip images step for now
    await page.click('button:has-text("Next")');
    
    // Wait for step 5 (description)
    await page.waitForSelector('text=Create compelling content');
    await page.screenshot({ path: 'proof-step-5-description.png', fullPage: true });
    
    // Step 5: Fill description
    await page.fill('input[name="title"]', 'Test Property - Proof of Concept');
    await page.fill('textarea[name="description"]', 'This is a test property created to prove the price and image functionality works correctly.');
    await page.fill('textarea[name="amenities"]', 'Test amenities: Pool, Gym, Parking');
    
    // Submit the form
    await page.click('button:has-text("Create Property")');
    
    // Wait for success message
    await page.waitForSelector('text=AI-powered property created successfully!', { timeout: 15000 });
    await page.screenshot({ path: 'proof-property-created.png', fullPage: true });
    
    // Now navigate to properties list to verify the property was created
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForLoadState('networkidle');
    
    // Look for the properties section
    await page.waitForSelector('text=Properties', { timeout: 10000 });
    await page.screenshot({ path: 'proof-properties-list.png', fullPage: true });
    
    // Verify the property appears in the list with correct price
    const propertyCard = page.locator('text=Test Property - Proof of Concept').first();
    await expect(propertyCard).toBeVisible();
    
    // Verify the price is displayed correctly (should show as ₹50L or similar)
    const priceDisplay = page.locator('text=₹50L').or(page.locator('text=₹5,000,000')).or(page.locator('text=₹50.0L'));
    await expect(priceDisplay).toBeVisible();
    
    // Click on the property to view details
    await propertyCard.click();
    
    // Wait for property details modal or page
    await page.waitForSelector('text=Test Property - Proof of Concept', { timeout: 5000 });
    await page.screenshot({ path: 'proof-property-details.png', fullPage: true });
    
    // Verify all the property details are correct
    await expect(page.locator('text=Test Property - Proof of Concept')).toBeVisible();
    await expect(page.locator('text=123 Test Property Street')).toBeVisible();
    await expect(page.locator('text=3')).toBeVisible(); // bedrooms
    await expect(page.locator('text=2')).toBeVisible(); // bathrooms
    await expect(page.locator('text=1200')).toBeVisible(); // area
    
    // Verify price is displayed correctly in details
    const detailPriceDisplay = page.locator('text=₹50L').or(page.locator('text=₹5,000,000')).or(page.locator('text=₹50.0L'));
    await expect(detailPriceDisplay).toBeVisible();
    
    // Take final proof screenshot
    await page.screenshot({ path: 'proof-final-verification.png', fullPage: true });
    
    console.log('✅ Property creation and retrieval proof completed successfully!');
    console.log('📸 Screenshots saved:');
    console.log('  - proof-initial-state.png');
    console.log('  - proof-form-start.png');
    console.log('  - proof-step-2.png');
    console.log('  - proof-step-3-pricing.png');
    console.log('  - proof-step-4-images.png');
    console.log('  - proof-step-5-description.png');
    console.log('  - proof-property-created.png');
    console.log('  - proof-properties-list.png');
    console.log('  - proof-property-details.png');
    console.log('  - proof-final-verification.png');
  });

  test('should handle price validation correctly', async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForLoadState('networkidle');
    
    // Navigate to property creation
    await page.click('text=Add Property');
    await page.waitForSelector('text=Add New Property');
    
    // Navigate to pricing step quickly
    await page.fill('input[name="address"]', 'Test Address');
    await page.fill('input[name="location"]', 'Test Location');
    await page.click('button:has-text("Next")');
    
    await page.selectOption('select[name="propertyType"]', 'Apartment');
    await page.fill('input[name="area"]', '1000');
    await page.selectOptions('select[name="bedrooms"]', '2');
    await page.selectOptions('select[name="bathrooms"]', '2');
    await page.click('button:has-text("Next")');
    
    // Test invalid price (negative)
    await page.fill('input[name="price"]', '-1000000');
    await page.click('button:has-text("Next")');
    
    // Should show validation error
    await expect(page.locator('text=Price must be a valid number greater than 0')).toBeVisible();
    await page.screenshot({ path: 'proof-price-validation-error.png', fullPage: true });
    
    // Test valid price
    await page.fill('input[name="price"]', '3000000');
    await page.click('button:has-text("Next")');
    
    // Should proceed to next step
    await page.waitForSelector('text=Add Property Images');
    await page.screenshot({ path: 'proof-price-validation-success.png', fullPage: true });
    
    console.log('✅ Price validation proof completed successfully!');
  });

  test('should handle image upload functionality', async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForLoadState('networkidle');
    
    // Navigate to property creation
    await page.click('text=Add Property');
    await page.waitForSelector('text=Add New Property');
    
    // Navigate to images step quickly
    await page.fill('input[name="address"]', 'Test Address');
    await page.fill('input[name="location"]', 'Test Location');
    await page.click('button:has-text("Next")');
    
    await page.selectOption('select[name="propertyType"]', 'Apartment');
    await page.fill('input[name="area"]', '1000');
    await page.selectOptions('select[name="bedrooms"]', '2');
    await page.selectOptions('select[name="bathrooms"]', '2');
    await page.click('button:has-text("Next")');
    
    await page.fill('input[name="price"]', '3000000');
    await page.click('button:has-text("Next")');
    
    // Verify images step is displayed
    await page.waitForSelector('text=Add Property Images');
    await expect(page.locator('text=Click to upload images')).toBeVisible();
    await expect(page.locator('text=Image Tips')).toBeVisible();
    
    await page.screenshot({ path: 'proof-image-upload-interface.png', fullPage: true });
    
    console.log('✅ Image upload interface proof completed successfully!');
  });
});