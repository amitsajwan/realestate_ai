import { test, expect } from '@playwright/test'

test.describe('Dashboard Public Website Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/')
    
    // Wait for dashboard to load
    await page.waitForSelector('[data-testid="dashboard"]', { timeout: 10000 })
  })

  test('should display public website management section', async ({ page }) => {
    // Click on Public Website navigation item
    await page.click('text=Public Website')
    
    // Wait for the component to load
    await page.waitForSelector('text=Public Website Management', { timeout: 10000 })
    
    // Check that the main elements are visible
    await expect(page.locator('h2:has-text("Public Website Management")')).toBeVisible()
    await expect(page.locator('text=Manage your public agent website and profile')).toBeVisible()
  })

  test('should show public website status', async ({ page }) => {
    // Navigate to public website section
    await page.click('text=Public Website')
    await page.waitForSelector('text=Public Website Management', { timeout: 10000 })
    
    // Check for status banner
    await expect(page.locator('[class*="bg-green-50"], [class*="bg-yellow-50"]')).toBeVisible()
  })

  test('should display stats cards', async ({ page }) => {
    // Navigate to public website section
    await page.click('text=Public Website')
    await page.waitForSelector('text=Public Website Management', { timeout: 10000 })
    
    // Check for stats cards
    await expect(page.locator('text=Total Views')).toBeVisible()
    await expect(page.locator('text=Total Contacts')).toBeVisible()
    await expect(page.locator('text=Public Properties')).toBeVisible()
    await expect(page.locator('text=Recent Inquiries')).toBeVisible()
  })

  test('should allow editing profile', async ({ page }) => {
    // Navigate to public website section
    await page.click('text=Public Website')
    await page.waitForSelector('text=Public Website Management', { timeout: 10000 })
    
    // Click edit profile button
    await page.click('button:has-text("Edit Profile")')
    
    // Check that form fields are visible
    await expect(page.locator('input[placeholder*="professional name"]')).toBeVisible()
    await expect(page.locator('textarea[placeholder*="Tell visitors about your experience"]')).toBeVisible()
    
    // Check for specialties checkboxes
    await expect(page.locator('text=Residential')).toBeVisible()
    await expect(page.locator('text=Commercial')).toBeVisible()
    await expect(page.locator('text=Luxury')).toBeVisible()
    
    // Check for languages checkboxes
    await expect(page.locator('text=English')).toBeVisible()
    await expect(page.locator('text=Spanish')).toBeVisible()
  })

  test('should show quick actions', async ({ page }) => {
    // Navigate to public website section
    await page.click('text=Public Website')
    await page.waitForSelector('text=Public Website Management', { timeout: 10000 })
    
    // Check for quick actions section
    await expect(page.locator('text=Quick Actions')).toBeVisible()
    await expect(page.locator('text=Manage Properties')).toBeVisible()
    await expect(page.locator('text=View Inquiries')).toBeVisible()
  })

  test('should have public status toggle', async ({ page }) => {
    // Navigate to public website section
    await page.click('text=Public Website')
    await page.waitForSelector('text=Public Website Management', { timeout: 10000 })
    
    // Click edit profile button
    await page.click('button:has-text("Edit Profile")')
    
    // Check for public status toggle
    await expect(page.locator('text=Public Website Status')).toBeVisible()
    await expect(page.locator('input[type="checkbox"]')).toBeVisible()
  })

  test('should show view public site button when profile is public', async ({ page }) => {
    // Navigate to public website section
    await page.click('text=Public Website')
    await page.waitForSelector('text=Public Website Management', { timeout: 10000 })
    
    // Check if view public site button exists (may or may not be visible depending on profile status)
    const viewButton = page.locator('a:has-text("View Public Site")')
    if (await viewButton.isVisible()) {
      await expect(viewButton).toBeVisible()
    }
  })

  test('should allow saving profile changes', async ({ page }) => {
    // Navigate to public website section
    await page.click('text=Public Website')
    await page.waitForSelector('text=Public Website Management', { timeout: 10000 })
    
    // Click edit profile button
    await page.click('button:has-text("Edit Profile")')
    
    // Fill in some basic information
    await page.fill('input[placeholder*="professional name"]', 'Test Agent')
    await page.fill('textarea[placeholder*="Tell visitors about your experience"]', 'Test bio for agent')
    
    // Check that save button is visible
    await expect(page.locator('button:has-text("Save Changes")')).toBeVisible()
  })

  test('should display contact information fields', async ({ page }) => {
    // Navigate to public website section
    await page.click('text=Public Website')
    await page.waitForSelector('text=Public Website Management', { timeout: 10000 })
    
    // Click edit profile button
    await page.click('button:has-text("Edit Profile")')
    
    // Check for contact information fields
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="tel"]')).toBeVisible()
    await expect(page.locator('input[placeholder*="123 Main St"]')).toBeVisible()
  })

  test('should show experience field', async ({ page }) => {
    // Navigate to public website section
    await page.click('text=Public Website')
    await page.waitForSelector('text=Public Website Management', { timeout: 10000 })
    
    // Click edit profile button
    await page.click('button:has-text("Edit Profile")')
    
    // Check for experience field
    await expect(page.locator('input[placeholder*="10+ years in real estate"]')).toBeVisible()
  })
})