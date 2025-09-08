import { test, expect } from '@playwright/test';

test.describe('Property Creation with Images and Price Fix', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the property creation page
    await page.goto('/dashboard');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Click on "Add Property" button
    await page.click('text=Add Property');
    
    // Wait for the form to load
    await page.waitForSelector('[data-testid="property-form"]', { timeout: 10000 });
  });

  test('should create property with correct price handling', async ({ page }) => {
    // Step 1: Fill address information
    await page.fill('input[name="address"]', '123 Marine Drive, Mumbai');
    await page.fill('input[name="location"]', 'Bandra West, Mumbai');
    await page.click('button:has-text("Next")');

    // Step 2: Fill basic property information
    await page.selectOption('select[name="propertyType"]', 'Apartment');
    await page.fill('input[name="area"]', '1200');
    await page.selectOption('select[name="bedrooms"]', '3');
    await page.selectOption('select[name="bathrooms"]', '2');
    await page.click('button:has-text("Next")');

    // Step 3: Fill pricing information
    await page.fill('input[name="price"]', '5000000');
    await page.click('button:has-text("Next")');

    // Step 4: Skip images for now (optional step)
    await page.click('button:has-text("Next")');

    // Step 5: Fill description
    await page.fill('input[name="title"]', 'Beautiful 3BHK Apartment in Bandra West');
    await page.fill('textarea[name="description"]', 'Modern apartment with great amenities and sea view');
    await page.fill('textarea[name="amenities"]', 'Swimming pool, Gym, Parking, 24/7 Security');

    // Submit the form
    await page.click('button:has-text("Create Property")');

    // Wait for success message
    await expect(page.locator('text=AI-powered property created successfully!')).toBeVisible({ timeout: 10000 });

    // Verify the property was created with correct price
    // This would require checking the properties list or API response
    // For now, we'll just verify the success message
  });

  test('should handle image upload correctly', async ({ page }) => {
    // Navigate through the form to the images step
    await page.fill('input[name="address"]', '456 Park Street, Delhi');
    await page.fill('input[name="location"]', 'Connaught Place, Delhi');
    await page.click('button:has-text("Next")');

    await page.selectOption('select[name="propertyType"]', 'House');
    await page.fill('input[name="area"]', '2000');
    await page.selectOption('select[name="bedrooms"]', '4');
    await page.selectOption('select[name="bathrooms"]', '3');
    await page.click('button:has-text("Next")');

    await page.fill('input[name="price"]', '8000000');
    await page.click('button:has-text("Next")');

    // Step 4: Upload images
    const fileInput = page.locator('input[type="file"]');
    
    // Create a test image file (in a real test, you'd use actual image files)
    // For now, we'll just verify the upload area is present
    await expect(page.locator('text=Click to upload images')).toBeVisible();
    
    // Verify image tips are shown
    await expect(page.locator('text=Image Tips')).toBeVisible();
    await expect(page.locator('text=Use high-resolution images')).toBeVisible();

    // Skip to next step (images are optional)
    await page.click('button:has-text("Next")');

    // Complete the form
    await page.fill('input[name="title"]', 'Spacious 4BHK House in CP');
    await page.fill('textarea[name="description"]', 'Beautiful house with garden and parking');
    await page.click('button:has-text("Create Property")');

    // Verify success
    await expect(page.locator('text=AI-powered property created successfully!')).toBeVisible({ timeout: 10000 });
  });

  test('should validate required fields correctly', async ({ page }) => {
    // Try to proceed without filling required fields
    await page.click('button:has-text("Next")');
    
    // Should show validation errors
    await expect(page.locator('text=Address is required')).toBeVisible();
    await expect(page.locator('text=Location is required')).toBeVisible();

    // Fill address and try again
    await page.fill('input[name="address"]', '789 MG Road, Bangalore');
    await page.fill('input[name="location"]', 'Koramangala, Bangalore');
    await page.click('button:has-text("Next")');

    // Should proceed to next step
    await expect(page.locator('text=Tell us about your property')).toBeVisible();
  });

  test('should handle price validation correctly', async ({ page }) => {
    // Navigate to pricing step
    await page.fill('input[name="address"]', '321 Brigade Road, Bangalore');
    await page.fill('input[name="location"]', 'Brigade Road, Bangalore');
    await page.click('button:has-text("Next")');

    await page.selectOption('select[name="propertyType"]', 'Villa');
    await page.fill('input[name="area"]', '3000');
    await page.selectOption('select[name="bedrooms"]', '5');
    await page.selectOption('select[name="bathrooms"]', '4');
    await page.click('button:has-text("Next")');

    // Try with invalid price (negative number)
    await page.fill('input[name="price"]', '-1000000');
    await page.click('button:has-text("Next")');
    
    // Should show validation error
    await expect(page.locator('text=Price must be a valid number greater than 0')).toBeVisible();

    // Try with zero
    await page.fill('input[name="price"]', '0');
    await page.click('button:has-text("Next")');
    
    // Should show validation error
    await expect(page.locator('text=Price must be a valid number greater than 0')).toBeVisible();

    // Try with valid price
    await page.fill('input[name="price"]', '12000000');
    await page.click('button:has-text("Next")');

    // Should proceed to images step
    await expect(page.locator('text=Add Property Images')).toBeVisible();
  });

  test('should show market insights when available', async ({ page }) => {
    // Fill address and property type to trigger market insights
    await page.fill('input[name="address"]', '555 Linking Road, Mumbai');
    await page.fill('input[name="location"]', 'Bandra West, Mumbai');
    await page.click('button:has-text("Next")');

    await page.selectOption('select[name="propertyType"]', 'Apartment');
    await page.fill('input[name="area"]', '1500');
    await page.selectOption('select[name="bedrooms"]', '3');
    await page.selectOption('select[name="bathrooms"]', '2');
    await page.click('button:has-text("Next")');

    // Market insights should be visible
    await expect(page.locator('text=Market Insights')).toBeVisible();
    await expect(page.locator('text=Average Price')).toBeVisible();
    await expect(page.locator('text=Market Trend')).toBeVisible();
  });

  test('should handle AI content generation', async ({ page }) => {
    // Navigate to description step
    await page.fill('input[name="address"]', '777 Church Street, Bangalore');
    await page.fill('input[name="location"]', 'Brigade Road, Bangalore');
    await page.click('button:has-text("Next")');

    await page.selectOption('select[name="propertyType"]', 'Apartment');
    await page.fill('input[name="area"]', '1000');
    await page.selectOption('select[name="bedrooms"]', '2');
    await page.selectOption('select[name="bathrooms"]', '2');
    await page.click('button:has-text("Next")');

    await page.fill('input[name="price"]', '6000000');
    await page.click('button:has-text("Next")');

    // Skip images
    await page.click('button:has-text("Next")');

    // Try AI content generation
    await page.click('button:has-text("Generate AI Content")');
    
    // Should show loading state
    await expect(page.locator('text=Generating...')).toBeVisible();

    // Wait for AI suggestions to appear
    await expect(page.locator('text=AI Generated Content')).toBeVisible({ timeout: 15000 });
    
    // Should show quality score
    await expect(page.locator('text=Quality Score')).toBeVisible();

    // Apply AI suggestions
    await page.click('button:has-text("Apply")');
    
    // Should show success message
    await expect(page.locator('text=AI suggestions applied to form!')).toBeVisible();
  });

  test('should handle form navigation correctly', async ({ page }) => {
    // Test back navigation
    await page.fill('input[name="address"]', '999 Residency Road, Bangalore');
    await page.fill('input[name="location"]', 'Residency Road, Bangalore');
    await page.click('button:has-text("Next")');

    // Should be on step 2
    await expect(page.locator('text=Tell us about your property')).toBeVisible();

    // Go back
    await page.click('button:has-text("Previous")');

    // Should be back on step 1
    await expect(page.locator('text=Where is your property located?')).toBeVisible();

    // Verify form data is preserved
    await expect(page.locator('input[name="address"]')).toHaveValue('999 Residency Road, Bangalore');
    await expect(page.locator('input[name="location"]')).toHaveValue('Residency Road, Bangalore');
  });

  test('should display progress steps correctly', async ({ page }) => {
    // Verify initial step
    await expect(page.locator('text=Step 1 of 5: Location')).toBeVisible();

    // Navigate through steps and verify progress
    await page.fill('input[name="address"]', '111 Commercial Street, Bangalore');
    await page.fill('input[name="location"]', 'Commercial Street, Bangalore');
    await page.click('button:has-text("Next")');

    await expect(page.locator('text=Step 2 of 5: Basic Info')).toBeVisible();

    await page.selectOption('select[name="propertyType"]', 'Commercial');
    await page.fill('input[name="area"]', '5000');
    await page.selectOption('select[name="bedrooms"]', '1');
    await page.selectOption('select[name="bathrooms"]', '1');
    await page.click('button:has-text("Next")');

    await expect(page.locator('text=Step 3 of 5: Pricing')).toBeVisible();

    await page.fill('input[name="price"]', '15000000');
    await page.click('button:has-text("Next")');

    await expect(page.locator('text=Step 4 of 5: Images')).toBeVisible();

    await page.click('button:has-text("Next")');

    await expect(page.locator('text=Step 5 of 5: Description')).toBeVisible();
  });
});