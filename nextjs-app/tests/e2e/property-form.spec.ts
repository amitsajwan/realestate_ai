import { test, expect } from '@playwright/test'

test.describe('Property Form Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login')
    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[type="password"]', 'password123')
    
    await page.route('**/api/v1/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          access_token: 'mock-token',
          refresh_token: 'mock-refresh-token',
          user_id: '1',
          expires_in: 3600
        })
      })
    })
    
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL('/')
    
    // Navigate to Add Property section
    await page.click('text=Add Property')
  })

  test('should display property form correctly', async ({ page }) => {
    // Check form elements
    await expect(page.locator('h2')).toContainText('Add Property')
    await expect(page.locator('input[placeholder="Enter property title"]')).toBeVisible()
    await expect(page.locator('input[placeholder="₹50,00,000"]')).toBeVisible()
    await expect(page.locator('input[placeholder="Enter property address"]')).toBeVisible()
    await expect(page.locator('select')).toBeVisible()
    await expect(page.locator('textarea')).toBeVisible()
    await expect(page.locator('input[placeholder="Parking, Gym, Pool, etc."]')).toBeVisible()
    
    // Check form labels
    await expect(page.locator('label')).toContainText('Title *')
    await expect(page.locator('label')).toContainText('Price *')
    await expect(page.locator('label')).toContainText('Address *')
    await expect(page.locator('label')).toContainText('Bedrooms')
    await expect(page.locator('label')).toContainText('Bathrooms')
    await expect(page.locator('label')).toContainText('Area (sq ft)')
    await expect(page.locator('label')).toContainText('Description *')
    await expect(page.locator('label')).toContainText('Amenities')
  })

  test('should validate required fields', async ({ page }) => {
    // Try to submit empty form
    await page.click('text=Add Property')
    
    // Should show validation errors
    await expect(page.locator('.text-red-500')).toBeVisible()
    
    // Fill only title
    await page.fill('input[placeholder="Enter property title"]', 'Test Property')
    await page.click('text=Add Property')
    
    // Should still show validation errors for other required fields
    await expect(page.locator('.text-red-500')).toBeVisible()
  })

  test('should submit property form successfully', async ({ page }) => {
    // Mock successful property creation
    await page.route('**/api/v1/properties/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            id: 1,
            user_id: '1',
            title: 'Test Property',
            type: 'Apartment',
            bedrooms: '2',
            price: 5000000,
            price_unit: 'INR',
            city: 'Mumbai',
            area: '1200',
            address: '123 Test Street',
            description: 'A beautiful test property',
            amenities: ['Parking', 'Gym']
          }
        })
      })
    })
    
    // Fill form
    await page.fill('input[placeholder="Enter property title"]', 'Test Property')
    await page.fill('input[placeholder="₹50,00,000"]', '₹50,00,000')
    await page.fill('input[placeholder="Enter property address"]', '123 Test Street')
    await page.selectOption('select', '2') // Bedrooms
    await page.selectOption('select:nth-of-type(2)', '2') // Bathrooms
    await page.fill('input[type="number"]', '1200')
    await page.fill('textarea', 'A beautiful test property with modern amenities')
    await page.fill('input[placeholder="Parking, Gym, Pool, etc."]', 'Parking, Gym, Pool')
    
    // Submit form
    await page.click('text=Add Property')
    
    // Should show success message
    await expect(page.locator('.text-green-500')).toBeVisible()
    await expect(page.locator('.text-green-500')).toContainText('Property added successfully')
  })

  test('should handle AI auto-fill functionality', async ({ page }) => {
    // Mock AI suggestions API
    await page.route('**/api/v1/property/ai_suggest', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: [{
            title: 'AI Generated Property',
            price: '₹75,00,000',
            description: 'A stunning AI-generated property description with modern amenities and prime location.',
            amenities: 'Parking, Gym, Swimming Pool, Security'
          }]
        })
      })
    })
    
    // Click AI auto-fill button
    await page.click('text=Auto-Fill with AI')
    
    // Should show loading state
    await expect(page.locator('text=Generating AI Content...')).toBeVisible()
    
    // Wait for AI content to load
    await expect(page.locator('input[placeholder="Enter property title"]')).toHaveValue('AI Generated Property')
    await expect(page.locator('input[placeholder="₹50,00,000"]')).toHaveValue('₹75,00,000')
    await expect(page.locator('textarea')).toHaveValue(/A stunning AI-generated property description/)
    await expect(page.locator('input[placeholder="Parking, Gym, Pool, etc."]')).toHaveValue(/Parking, Gym, Swimming Pool/)
  })

  test('should handle form validation errors', async ({ page }) => {
    // Fill invalid price
    await page.fill('input[placeholder="Enter property title"]', 'Test Property')
    await page.fill('input[placeholder="₹50,00,000"]', 'invalid-price')
    await page.fill('input[placeholder="Enter property address"]', '123 Test Street')
    await page.fill('textarea', 'Test description')
    
    await page.click('text=Add Property')
    
    // Should show validation error for price
    await expect(page.locator('.text-red-500')).toContainText('Invalid price format')
  })

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/api/v1/properties/', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          error: 'Failed to create property'
        })
      })
    })
    
    // Fill and submit form
    await page.fill('input[placeholder="Enter property title"]', 'Test Property')
    await page.fill('input[placeholder="₹50,00,000"]', '₹50,00,000')
    await page.fill('input[placeholder="Enter property address"]', '123 Test Street')
    await page.fill('textarea', 'Test description')
    
    await page.click('text=Add Property')
    
    // Should show error message
    await expect(page.locator('.text-red-500')).toBeVisible()
    await expect(page.locator('.text-red-500')).toContainText('Failed to create property')
  })

  test('should handle AI API errors', async ({ page }) => {
    // Mock AI API error
    await page.route('**/api/v1/property/ai_suggest', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          error: 'Failed to generate AI content'
        })
      })
    })
    
    // Click AI auto-fill button
    await page.click('text=Auto-Fill with AI')
    
    // Should show error message
    await expect(page.locator('.text-red-500')).toBeVisible()
    await expect(page.locator('.text-red-500')).toContainText('Failed to generate AI content')
  })

  test('should format price input correctly', async ({ page }) => {
    // Test price formatting
    const priceInput = page.locator('input[placeholder="₹50,00,000"]')
    
    await priceInput.fill('5000000')
    await expect(priceInput).toHaveValue('₹50,00,000')
    
    await priceInput.fill('750000')
    await expect(priceInput).toHaveValue('₹7,50,000')
  })

  test('should handle back button navigation', async ({ page }) => {
    // Click back button
    await page.click('text=Back to Dashboard')
    
    // Should return to dashboard
    await expect(page).toHaveURL('/')
    await expect(page.locator('h1')).toContainText('🚀 Welcome to PropertyAI!')
  })

  test('should be responsive on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    
    // Check that form is still accessible
    await expect(page.locator('h2')).toContainText('Add Property')
    await expect(page.locator('input[placeholder="Enter property title"]')).toBeVisible()
    await expect(page.locator('input[placeholder="₹50,00,000"]')).toBeVisible()
    
    // Check that buttons are visible
    await expect(page.locator('text=Add Property')).toBeVisible()
    await expect(page.locator('text=Auto-Fill with AI')).toBeVisible()
    await expect(page.locator('text=Back to Dashboard')).toBeVisible()
  })

  test('should maintain form state during navigation', async ({ page }) => {
    // Fill some form fields
    await page.fill('input[placeholder="Enter property title"]', 'Test Property')
    await page.fill('input[placeholder="₹50,00,000"]', '₹50,00,000')
    
    // Navigate away and back
    await page.click('text=Dashboard')
    await page.click('text=Add Property')
    
    // Form should retain values
    await expect(page.locator('input[placeholder="Enter property title"]')).toHaveValue('Test Property')
    await expect(page.locator('input[placeholder="₹50,00,000"]')).toHaveValue('₹50,00,000')
  })
})
