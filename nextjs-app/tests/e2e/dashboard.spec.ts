import { test, expect } from '@playwright/test'

test.describe('Dashboard Functionality', () => {
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
  })

  test('should display dashboard with correct stats', async ({ page }) => {
    // Mock dashboard stats API
    await page.route('**/api/v1/dashboard/stats', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            total_properties: 12,
            active_listings: 8,
            total_leads: 24,
            total_users: 5,
            total_views: 1247,
            monthly_leads: 8,
            revenue: '₹45,00,000'
          }
        })
      })
    })
    
    // Refresh page to load stats
    await page.reload()
    
    // Check welcome section
    await expect(page.locator('h1')).toContainText('🚀 Welcome to PropertyAI!')
    await expect(page.locator('p')).toContainText('Your AI-powered real estate assistant')
    
    // Check setup progress
    for (let i = 1; i <= 7; i++) {
      await expect(page.locator(`text=Step ${i}`)).toBeVisible()
    }
    
    // Check stats cards
    await expect(page.locator('text=Total Properties')).toBeVisible()
    await expect(page.locator('text=12')).toBeVisible()
    await expect(page.locator('text=Property Views')).toBeVisible()
    await expect(page.locator('text=1,247')).toBeVisible()
    await expect(page.locator('text=Active Leads')).toBeVisible()
    await expect(page.locator('text=24')).toBeVisible()
    await expect(page.locator('text=Revenue')).toBeVisible()
    await expect(page.locator('text=₹45,00,000')).toBeVisible()
  })

  test('should navigate between dashboard sections', async ({ page }) => {
    // Check navigation sidebar
    await expect(page.locator('text=Dashboard')).toBeVisible()
    await expect(page.locator('text=Add Property')).toBeVisible()
    await expect(page.locator('text=AI Tools')).toBeVisible()
    await expect(page.locator('text=Analytics')).toBeVisible()
    await expect(page.locator('text=CRM')).toBeVisible()
    await expect(page.locator('text=Facebook')).toBeVisible()
    await expect(page.locator('text=Profile')).toBeVisible()
    
    // Click on Add Property section
    await page.click('text=Add Property')
    await expect(page.locator('h2')).toContainText('Add Property')
    
    // Click on AI Tools section
    await page.click('text=AI Tools')
    await expect(page.locator('h2')).toContainText('AI Content Generator')
    
    // Click on Analytics section
    await page.click('text=Analytics')
    await expect(page.locator('h2')).toContainText('Analytics Dashboard')
    
    // Click on CRM section
    await page.click('text=CRM')
    await expect(page.locator('h2')).toContainText('Customer Relationship Management')
    
    // Click on Facebook section
    await page.click('text=Facebook')
    await expect(page.locator('h2')).toContainText('Facebook Integration')
    
    // Click on Profile section
    await page.click('text=Profile')
    await expect(page.locator('h2')).toContainText('Profile Settings')
    
    // Return to Dashboard
    await page.click('text=Dashboard')
    await expect(page.locator('h1')).toContainText('🚀 Welcome to PropertyAI!')
  })

  test('should display user information in header', async ({ page }) => {
    // Check header elements
    await expect(page.locator('text=PropertyAI')).toBeVisible()
    await expect(page.locator('text=Agent Name')).toBeVisible() // Default name
    
    // Check logout button
    await expect(page.locator('[aria-label="Logout"]')).toBeVisible()
  })

  test('should handle quick action buttons', async ({ page }) => {
    // Check quick action cards
    await expect(page.locator('text=Add Properties')).toBeVisible()
    await expect(page.locator('text=AI Tools')).toBeVisible()
    await expect(page.locator('text=Analytics')).toBeVisible()
    
    // Click Add Property quick action
    await page.click('text=Add Property')
    await expect(page.locator('h2')).toContainText('Add Property')
    
    // Go back to dashboard
    await page.click('text=Dashboard')
    
    // Click AI Tools quick action
    await page.click('text=AI Tools')
    await expect(page.locator('h2')).toContainText('AI Content Generator')
    
    // Go back to dashboard
    await page.click('text=Dashboard')
    
    // Click View Analytics quick action
    await page.click('text=View Analytics')
    await expect(page.locator('h2')).toContainText('Analytics Dashboard')
  })

  test('should show loading state while fetching data', async ({ page }) => {
    // Mock delayed API response
    await page.route('**/api/v1/dashboard/stats', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000))
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            total_properties: 12,
            active_listings: 8,
            total_leads: 24,
            total_users: 5,
            total_views: 1247,
            monthly_leads: 8,
            revenue: '₹45,00,000'
          }
        })
      })
    })
    
    // Refresh page
    await page.reload()
    
    // Should show loading spinner initially
    await expect(page.locator('.animate-spin')).toBeVisible()
    
    // Wait for data to load
    await expect(page.locator('text=12')).toBeVisible({ timeout: 5000 })
  })

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/api/v1/dashboard/stats', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          error: 'Internal server error'
        })
      })
    })
    
    // Refresh page
    await page.reload()
    
    // Should still show dashboard with fallback data
    await expect(page.locator('h1')).toContainText('🚀 Welcome to PropertyAI!')
    await expect(page.locator('text=Total Properties')).toBeVisible()
  })

  test('should be responsive on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    
    // Check that navigation is accessible
    await expect(page.locator('text=Dashboard')).toBeVisible()
    await expect(page.locator('text=Add Property')).toBeVisible()
    
    // Check that stats are displayed properly
    await expect(page.locator('text=Total Properties')).toBeVisible()
    await expect(page.locator('text=Property Views')).toBeVisible()
    
    // Check that quick actions are visible
    await expect(page.locator('text=Add Properties')).toBeVisible()
    await expect(page.locator('text=AI Tools')).toBeVisible()
  })

  test('should maintain state during navigation', async ({ page }) => {
    // Navigate to different sections
    await page.click('text=Add Property')
    await expect(page.locator('h2')).toContainText('Add Property')
    
    await page.click('text=AI Tools')
    await expect(page.locator('h2')).toContainText('AI Content Generator')
    
    // Refresh page
    await page.reload()
    
    // Should still be on the same section
    await expect(page.locator('h2')).toContainText('AI Content Generator')
  })
})
