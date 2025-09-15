import { test, expect } from '@playwright/test';

test.describe('Property Management System', () => {
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

  test('should display property management dashboard', async ({ page }) => {
    // Navigate to properties section
    await page.click('text=Properties');
    
    // Check if property management interface is visible
    await expect(page.locator('text=Property Management')).toBeVisible();
    await expect(page.locator('button[data-testid="add-property"]')).toBeVisible();
    await expect(page.locator('[data-testid="property-list"]')).toBeVisible();
  });

  test('should open smart property form', async ({ page }) => {
    // Navigate to add property
    await page.click('text=Add Property');
    
    // Check if smart property form is visible
    await expect(page.locator('text=Smart Property Form')).toBeVisible();
    await expect(page.locator('[data-testid="property-form"]')).toBeVisible();
    
    // Check if form steps are visible
    await expect(page.locator('[data-testid="step-1"]')).toBeVisible();
    await expect(page.locator('text=Basic Information')).toBeVisible();
  });

  test('should complete step 1 - Basic Information', async ({ page }) => {
    // Open property form
    await page.click('text=Add Property');
    
    // Fill basic information
    await page.fill('input[name="title"]', 'Beautiful 3BR Apartment');
    await page.fill('textarea[name="description"]', 'Spacious apartment with modern amenities');
    await page.fill('input[name="price"]', '500000');
    await page.fill('input[name="location"]', '123 Main St, New York, NY');
    await page.selectOption('select[name="propertyType"]', 'apartment');
    
    // Click next button
    await page.click('button[data-testid="next-step"]');
    
    // Should move to step 2
    await expect(page.locator('[data-testid="step-2"]')).toBeVisible();
    await expect(page.locator('text=Property Details')).toBeVisible();
  });

  test('should complete step 2 - Property Details', async ({ page }) => {
    // Open property form and complete step 1
    await page.click('text=Add Property');
    await page.fill('input[name="title"]', 'Beautiful 3BR Apartment');
    await page.fill('textarea[name="description"]', 'Spacious apartment with modern amenities');
    await page.fill('input[name="price"]', '500000');
    await page.fill('input[name="location"]', '123 Main St, New York, NY');
    await page.selectOption('select[name="propertyType"]', 'apartment');
    await page.click('button[data-testid="next-step"]');
    
    // Fill property details
    await page.fill('input[name="bedrooms"]', '3');
    await page.fill('input[name="bathrooms"]', '2');
    await page.fill('input[name="areaSqft"]', '1200');
    await page.fill('input[name="yearBuilt"]', '2020');
    await page.fill('input[name="parkingSpaces"]', '1');
    
    // Add features
    await page.check('input[name="features"][value="balcony"]');
    await page.check('input[name="features"][value="gym"]');
    await page.check('input[name="features"][value="pool"]');
    
    // Click next button
    await page.click('button[data-testid="next-step"]');
    
    // Should move to step 3
    await expect(page.locator('[data-testid="step-3"]')).toBeVisible();
    await expect(page.locator('text=AI Suggestions')).toBeVisible();
  });

  test('should generate AI suggestions', async ({ page }) => {
    // Open property form and complete steps 1-2
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
    
    // Click generate AI suggestions
    await page.click('button[data-testid="generate-ai-suggestions"]');
    
    // Should show loading state
    await expect(page.locator('text=Generating AI suggestions...')).toBeVisible();
    
    // Wait for AI suggestions to load
    await page.waitForSelector('[data-testid="ai-suggestions"]', { timeout: 10000 });
    
    // Should show AI suggestions
    await expect(page.locator('[data-testid="ai-suggestions"]')).toBeVisible();
    await expect(page.locator('text=Suggested Title')).toBeVisible();
    await expect(page.locator('text=Suggested Description')).toBeVisible();
    await expect(page.locator('text=Market Insights')).toBeVisible();
  });

  test('should upload property images', async ({ page }) => {
    // Open property form and complete steps 1-3
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
    
    // Should be on step 4 - Images
    await expect(page.locator('[data-testid="step-4"]')).toBeVisible();
    await expect(page.locator('text=Property Images')).toBeVisible();
    
    // Upload test images
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles([
      {
        name: 'property1.jpg',
        mimeType: 'image/jpeg',
        buffer: Buffer.from('fake-image-data-1')
      },
      {
        name: 'property2.jpg',
        mimeType: 'image/jpeg',
        buffer: Buffer.from('fake-image-data-2')
      }
    ]);
    
    // Should show image previews
    await expect(page.locator('[data-testid="image-preview"]')).toHaveCount(2);
    
    // Should allow reordering images
    await page.dragAndDrop(
      page.locator('[data-testid="image-preview"]').first(),
      page.locator('[data-testid="image-preview"]').last()
    );
  });

  test('should create property successfully', async ({ page }) => {
    // Complete full property creation flow
    await page.click('text=Add Property');
    
    // Step 1: Basic Information
    await page.fill('input[name="title"]', 'Beautiful 3BR Apartment');
    await page.fill('textarea[name="description"]', 'Spacious apartment with modern amenities');
    await page.fill('input[name="price"]', '500000');
    await page.fill('input[name="location"]', '123 Main St, New York, NY');
    await page.selectOption('select[name="propertyType"]', 'apartment');
    await page.click('button[data-testid="next-step"]');
    
    // Step 2: Property Details
    await page.fill('input[name="bedrooms"]', '3');
    await page.fill('input[name="bathrooms"]', '2');
    await page.fill('input[name="areaSqft"]', '1200');
    await page.click('button[data-testid="next-step"]');
    
    // Step 3: AI Suggestions (skip)
    await page.click('button[data-testid="next-step"]');
    
    // Step 4: Images (skip)
    await page.click('button[data-testid="next-step"]');
    
    // Should be on final step
    await expect(page.locator('[data-testid="step-5"]')).toBeVisible();
    await expect(page.locator('text=Review & Create')).toBeVisible();
    
    // Click create property button
    await page.click('button[data-testid="create-property"]');
    
    // Should show success message
    await expect(page.locator('text=Property created successfully')).toBeVisible();
    
    // Should redirect to property list
    await expect(page.locator('[data-testid="property-list"]')).toBeVisible();
  });

  test('should display property list with filters', async ({ page }) => {
    // Navigate to properties
    await page.click('text=Properties');
    
    // Check if property list is visible
    await expect(page.locator('[data-testid="property-list"]')).toBeVisible();
    
    // Check if filters are available
    await expect(page.locator('[data-testid="property-filters"]')).toBeVisible();
    await expect(page.locator('select[name="propertyType"]')).toBeVisible();
    await expect(page.locator('select[name="status"]')).toBeVisible();
    await expect(page.locator('input[name="priceRange"]')).toBeVisible();
  });

  test('should filter properties by type', async ({ page }) => {
    // Navigate to properties
    await page.click('text=Properties');
    
    // Filter by apartment type
    await page.selectOption('select[name="propertyType"]', 'apartment');
    
    // Should show filtered results
    await expect(page.locator('[data-testid="property-item"]')).toHaveCount(0); // No apartments in test data
  });

  test('should search properties by location', async ({ page }) => {
    // Navigate to properties
    await page.click('text=Properties');
    
    // Search by location
    await page.fill('input[name="search"]', 'New York');
    await page.click('button[data-testid="search-button"]');
    
    // Should show search results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
  });

  test('should edit existing property', async ({ page }) => {
    // Navigate to properties
    await page.click('text=Properties');
    
    // Click edit button on first property
    await page.click('[data-testid="property-item"] button[data-testid="edit-property"]');
    
    // Should open edit form
    await expect(page.locator('[data-testid="edit-property-form"]')).toBeVisible();
    
    // Modify property details
    await page.fill('input[name="title"]', 'Updated Property Title');
    await page.fill('input[name="price"]', '600000');
    
    // Save changes
    await page.click('button[data-testid="save-property"]');
    
    // Should show success message
    await expect(page.locator('text=Property updated successfully')).toBeVisible();
  });

  test('should delete property', async ({ page }) => {
    // Navigate to properties
    await page.click('text=Properties');
    
    // Click delete button on first property
    await page.click('[data-testid="property-item"] button[data-testid="delete-property"]');
    
    // Should show confirmation dialog
    await expect(page.locator('[data-testid="delete-confirmation"]')).toBeVisible();
    await expect(page.locator('text=Are you sure you want to delete this property?')).toBeVisible();
    
    // Confirm deletion
    await page.click('button[data-testid="confirm-delete"]');
    
    // Should show success message
    await expect(page.locator('text=Property deleted successfully')).toBeVisible();
  });

  test('should show property analytics', async ({ page }) => {
    // Navigate to properties
    await page.click('text=Properties');
    
    // Click analytics button on first property
    await page.click('[data-testid="property-item"] button[data-testid="view-analytics"]');
    
    // Should open analytics modal
    await expect(page.locator('[data-testid="property-analytics"]')).toBeVisible();
    await expect(page.locator('text=Property Performance')).toBeVisible();
    await expect(page.locator('text=Views')).toBeVisible();
    await expect(page.locator('text=Inquiries')).toBeVisible();
    await expect(page.locator('text=Shares')).toBeVisible();
  });

  test('should handle AI suggestions failure', async ({ page }) => {
    // Open property form
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
    
    // Mock AI service failure
    await page.route('**/api/v1/properties/ai-suggestions', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'AI service unavailable' })
      });
    });
    
    // Click generate AI suggestions
    await page.click('button[data-testid="generate-ai-suggestions"]');
    
    // Should show error message
    await expect(page.locator('text=Failed to generate AI suggestions')).toBeVisible();
    
    // Should allow manual input
    await page.fill('input[name="customTitle"]', 'Custom Property Title');
    await page.fill('textarea[name="customDescription"]', 'Custom property description');
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Navigate to properties
    await page.click('text=Properties');
    
    // Check if property management is still usable on mobile
    await expect(page.locator('[data-testid="property-list"]')).toBeVisible();
    await expect(page.locator('button[data-testid="add-property"]')).toBeVisible();
    
    // Open property form
    await page.click('text=Add Property');
    
    // Check if form is usable on mobile
    await expect(page.locator('[data-testid="property-form"]')).toBeVisible();
    await expect(page.locator('input[name="title"]')).toBeVisible();
  });
});