import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test
    await page.goto('/')
    await page.evaluate(() => localStorage.clear())
  })

  test('should redirect to login page when not authenticated', async ({ page }) => {
    await page.goto('/')
    
    // Should redirect to login page
    await expect(page).toHaveURL('/login')
    await expect(page.locator('h1')).toContainText('Welcome to PropertyAI')
  })

  test('should display login form correctly', async ({ page }) => {
    await page.goto('/login')
    
    // Check form elements
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
    
    // Check form labels
    await expect(page.locator('label')).toContainText('Email')
    await expect(page.locator('label')).toContainText('Password')
  })

  test('should handle login with valid credentials', async ({ page }) => {
    await page.goto('/login')
    
    // Fill login form
    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[type="password"]', 'password123')
    
    // Mock successful login response
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
    
    // Submit form
    await page.click('button[type="submit"]')
    
    // Should redirect to dashboard
    await expect(page).toHaveURL('/')
    await expect(page.locator('h1')).toContainText('Welcome to PropertyAI')
  })

  test('should handle login with invalid credentials', async ({ page }) => {
    await page.goto('/login')
    
    // Fill login form with invalid credentials
    await page.fill('input[type="email"]', 'invalid@example.com')
    await page.fill('input[type="password"]', 'wrongpassword')
    
    // Mock failed login response
    await page.route('**/api/v1/auth/login', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          message: 'Invalid credentials'
        })
      })
    })
    
    // Submit form
    await page.click('button[type="submit"]')
    
    // Should show error message
    await expect(page.locator('.text-red-500')).toBeVisible()
    await expect(page.locator('.text-red-500')).toContainText('Invalid credentials')
  })

  test('should handle registration flow', async ({ page }) => {
    await page.goto('/login')
    
    // Switch to registration mode
    await page.click('text=Create Account')
    
    // Fill registration form
    await page.fill('input[name="firstName"]', 'John')
    await page.fill('input[name="lastName"]', 'Doe')
    await page.fill('input[type="email"]', 'newuser@example.com')
    await page.fill('input[type="password"]', 'password123')
    
    // Mock successful registration response
    await page.route('**/api/v1/auth/register', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          access_token: 'mock-token',
          refresh_token: 'mock-refresh-token',
          user_id: '2',
          expires_in: 3600
        })
      })
    })
    
    // Submit form
    await page.click('button[type="submit"]')
    
    // Should redirect to onboarding for new users
    await expect(page).toHaveURL('/onboarding')
  })

  test('should handle logout', async ({ page }) => {
    // First login
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
    
    // Click logout button
    await page.click('[aria-label="Logout"]')
    
    // Should redirect to login page
    await expect(page).toHaveURL('/login')
  })

  test('should persist authentication state', async ({ page }) => {
    // Login first
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
    
    // Refresh page
    await page.reload()
    
    // Should still be on dashboard
    await expect(page).toHaveURL('/')
    await expect(page.locator('h1')).toContainText('Welcome to PropertyAI')
  })

  test('should show loading states during authentication', async ({ page }) => {
    await page.goto('/login')
    
    // Fill form
    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[type="password"]', 'password123')
    
    // Mock delayed response
    await page.route('**/api/v1/auth/login', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000))
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          access_token: 'mock-token',
          user_id: '1'
        })
      })
    })
    
    // Submit and check loading state
    await page.click('button[type="submit"]')
    
    // Should show loading indicator
    await expect(page.locator('button[type="submit"]')).toBeDisabled()
    await expect(page.locator('button[type="submit"]')).toContainText('Signing In...')
  })

  test('should validate form inputs', async ({ page }) => {
    await page.goto('/login')
    
    // Try to submit empty form
    await page.click('button[type="submit"]')
    
    // Should show validation errors
    await expect(page.locator('.text-red-500')).toBeVisible()
    
    // Fill invalid email
    await page.fill('input[type="email"]', 'invalid-email')
    await page.fill('input[type="password"]', 'password123')
    await page.click('button[type="submit"]')
    
    // Should show email validation error
    await expect(page.locator('.text-red-500')).toContainText('Invalid email')
  })
})
