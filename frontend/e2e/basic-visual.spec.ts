import { test, expect } from '@playwright/test'

test.describe('Basic Visual Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the main dashboard
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test('main dashboard layout', async ({ page }) => {
    // Wait for the main content to load
    await page.waitForSelector('main', { timeout: 10000 })
    
    // Take full page screenshot
    await expect(page).toHaveScreenshot('dashboard-main-layout.png', {
      fullPage: true,
      animations: 'disabled',
    })
  })

  test('dashboard header', async ({ page }) => {
    await page.waitForSelector('header', { timeout: 10000 })
    
    // Screenshot of just the header
    const header = page.locator('header')
    await expect(header).toHaveScreenshot('dashboard-header.png', {
      animations: 'disabled',
    })
  })

  test('navigation sidebar', async ({ page }) => {
    await page.waitForSelector('nav', { timeout: 10000 })
    
    // Screenshot of the navigation sidebar
    const sidebar = page.locator('nav')
    await expect(sidebar).toHaveScreenshot('navigation-sidebar.png', {
      animations: 'disabled',
    })
  })

  test('responsive design - mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    await expect(page).toHaveScreenshot('mobile-layout.png', {
      fullPage: true,
      animations: 'disabled',
    })
  })

  test('responsive design - tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    await expect(page).toHaveScreenshot('tablet-layout.png', {
      fullPage: true,
      animations: 'disabled',
    })
  })

  test('responsive design - desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 })
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    await expect(page).toHaveScreenshot('desktop-layout.png', {
      fullPage: true,
      animations: 'disabled',
    })
  })

  test('dark mode', async ({ page }) => {
    // Enable dark mode
    await page.emulateMedia({ colorScheme: 'dark' })
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    await expect(page).toHaveScreenshot('dark-mode-dashboard.png', {
      fullPage: true,
      animations: 'disabled',
    })
  })
})