import { test, expect } from '@playwright/test'

test.describe('Visual Regression Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the main dashboard
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test.describe('Dashboard Layout', () => {
    test('main dashboard layout', async ({ page }) => {
      // Wait for the main content to load
      await page.waitForSelector('[data-testid="main-content"]', { timeout: 10000 })
      
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
  })

  test.describe('CRM Component Visual Tests', () => {
    test.beforeEach(async ({ page }) => {
      // Navigate to CRM section
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Click on CRM navigation item
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
    })

    test('CRM dashboard layout', async ({ page }) => {
      await page.waitForSelector('[data-testid="crm-dashboard"]', { timeout: 10000 })
      
      await expect(page).toHaveScreenshot('crm-dashboard-layout.png', {
        fullPage: true,
        animations: 'disabled',
      })
    })

    test('CRM statistics cards', async ({ page }) => {
      await page.waitForSelector('[data-testid="crm-stats"]', { timeout: 10000 })
      
      const statsSection = page.locator('[data-testid="crm-stats"]')
      await expect(statsSection).toHaveScreenshot('crm-statistics-cards.png', {
        animations: 'disabled',
      })
    })

    test('CRM lead list', async ({ page }) => {
      await page.waitForSelector('[data-testid="crm-leads-list"]', { timeout: 10000 })
      
      const leadsList = page.locator('[data-testid="crm-leads-list"]')
      await expect(leadsList).toHaveScreenshot('crm-leads-list.png', {
        animations: 'disabled',
      })
    })

    test('CRM lead detail modal', async ({ page }) => {
      await page.waitForSelector('[data-testid="crm-leads-list"]', { timeout: 10000 })
      
      // Click on first lead to open modal
      await page.click('[data-testid="lead-view-button"]:first-child')
      await page.waitForSelector('[data-testid="lead-detail-modal"]', { timeout: 5000 })
      
      const modal = page.locator('[data-testid="lead-detail-modal"]')
      await expect(modal).toHaveScreenshot('crm-lead-detail-modal.png', {
        animations: 'disabled',
      })
    })

    test('CRM search and filters', async ({ page }) => {
      await page.waitForSelector('[data-testid="crm-search"]', { timeout: 10000 })
      
      const searchSection = page.locator('[data-testid="crm-search"]')
      await expect(searchSection).toHaveScreenshot('crm-search-filters.png', {
        animations: 'disabled',
      })
    })
  })

  test.describe('Analytics Component Visual Tests', () => {
    test.beforeEach(async ({ page }) => {
      // Navigate to Analytics section
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Click on Analytics navigation item
      await page.click('[data-testid="nav-analytics"]')
      await page.waitForLoadState('networkidle')
    })

    test('Analytics dashboard layout', async ({ page }) => {
      await page.waitForSelector('[data-testid="analytics-dashboard"]', { timeout: 10000 })
      
      await expect(page).toHaveScreenshot('analytics-dashboard-layout.png', {
        fullPage: true,
        animations: 'disabled',
      })
    })

    test('Analytics metrics cards', async ({ page }) => {
      await page.waitForSelector('[data-testid="analytics-metrics"]', { timeout: 10000 })
      
      const metricsSection = page.locator('[data-testid="analytics-metrics"]')
      await expect(metricsSection).toHaveScreenshot('analytics-metrics-cards.png', {
        animations: 'disabled',
      })
    })

    test('Analytics charts section', async ({ page }) => {
      await page.waitForSelector('[data-testid="analytics-charts"]', { timeout: 10000 })
      
      const chartsSection = page.locator('[data-testid="analytics-charts"]')
      await expect(chartsSection).toHaveScreenshot('analytics-charts-section.png', {
        animations: 'disabled',
      })
    })

    test('Analytics status breakdown', async ({ page }) => {
      await page.waitForSelector('[data-testid="analytics-status-breakdown"]', { timeout: 10000 })
      
      const statusSection = page.locator('[data-testid="analytics-status-breakdown"]')
      await expect(statusSection).toHaveScreenshot('analytics-status-breakdown.png', {
        animations: 'disabled',
      })
    })
  })

  test.describe('Team Management Component Visual Tests', () => {
    test.beforeEach(async ({ page }) => {
      // Navigate to Team Management section
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Click on Team Management navigation item
      await page.click('[data-testid="nav-team-management"]')
      await page.waitForLoadState('networkidle')
    })

    test('Team management dashboard', async ({ page }) => {
      await page.waitForSelector('[data-testid="team-management"]', { timeout: 10000 })
      
      await expect(page).toHaveScreenshot('team-management-dashboard.png', {
        fullPage: true,
        animations: 'disabled',
      })
    })

    test('Team statistics', async ({ page }) => {
      await page.waitForSelector('[data-testid="team-stats"]', { timeout: 10000 })
      
      const statsSection = page.locator('[data-testid="team-stats"]')
      await expect(statsSection).toHaveScreenshot('team-statistics.png', {
        animations: 'disabled',
      })
    })

    test('Team members list', async ({ page }) => {
      await page.waitForSelector('[data-testid="team-members-list"]', { timeout: 10000 })
      
      const membersList = page.locator('[data-testid="team-members-list"]')
      await expect(membersList).toHaveScreenshot('team-members-list.png', {
        animations: 'disabled',
      })
    })

    test('Team invitation modal', async ({ page }) => {
      await page.waitForSelector('[data-testid="team-management"]', { timeout: 10000 })
      
      // Click invite member button
      await page.click('[data-testid="invite-member-button"]')
      await page.waitForSelector('[data-testid="invite-modal"]', { timeout: 5000 })
      
      const modal = page.locator('[data-testid="invite-modal"]')
      await expect(modal).toHaveScreenshot('team-invitation-modal.png', {
        animations: 'disabled',
      })
    })
  })

  test.describe('Responsive Design Visual Tests', () => {
    test('mobile layout - iPhone 12', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      await expect(page).toHaveScreenshot('mobile-layout-iphone12.png', {
        fullPage: true,
        animations: 'disabled',
      })
    })

    test('tablet layout - iPad', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      await expect(page).toHaveScreenshot('tablet-layout-ipad.png', {
        fullPage: true,
        animations: 'disabled',
      })
    })

    test('desktop layout - 1920x1080', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      await expect(page).toHaveScreenshot('desktop-layout-1920x1080.png', {
        fullPage: true,
        animations: 'disabled',
      })
    })

    test('large desktop layout - 2560x1440', async ({ page }) => {
      await page.setViewportSize({ width: 2560, height: 1440 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      await expect(page).toHaveScreenshot('large-desktop-layout-2560x1440.png', {
        fullPage: true,
        animations: 'disabled',
      })
    })
  })

  test.describe('Dark Mode Visual Tests', () => {
    test.beforeEach(async ({ page }) => {
      // Enable dark mode
      await page.emulateMedia({ colorScheme: 'dark' })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
    })

    test('dark mode dashboard', async ({ page }) => {
      await page.waitForSelector('[data-testid="main-content"]', { timeout: 10000 })
      
      await expect(page).toHaveScreenshot('dark-mode-dashboard.png', {
        fullPage: true,
        animations: 'disabled',
      })
    })

    test('dark mode CRM', async ({ page }) => {
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      await expect(page).toHaveScreenshot('dark-mode-crm.png', {
        fullPage: true,
        animations: 'disabled',
      })
    })

    test('dark mode Analytics', async ({ page }) => {
      await page.click('[data-testid="nav-analytics"]')
      await page.waitForLoadState('networkidle')
      
      await expect(page).toHaveScreenshot('dark-mode-analytics.png', {
        fullPage: true,
        animations: 'disabled',
      })
    })
  })

  test.describe('High Contrast Mode Visual Tests', () => {
    test.beforeEach(async ({ page }) => {
      // Enable high contrast mode
      await page.emulateMedia({ forcedColors: 'active' })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
    })

    test('high contrast dashboard', async ({ page }) => {
      await page.waitForSelector('[data-testid="main-content"]', { timeout: 10000 })
      
      await expect(page).toHaveScreenshot('high-contrast-dashboard.png', {
        fullPage: true,
        animations: 'disabled',
      })
    })
  })

  test.describe('Loading States Visual Tests', () => {
    test('loading state - CRM', async ({ page }) => {
      // Intercept API calls to simulate slow loading
      await page.route('**/api/crm/**', async (route) => {
        await new Promise(resolve => setTimeout(resolve, 2000))
        await route.continue()
      })
      
      await page.goto('/')
      await page.click('[data-testid="nav-crm"]')
      
      // Take screenshot during loading state
      await expect(page).toHaveScreenshot('loading-state-crm.png', {
        fullPage: true,
        animations: 'disabled',
      })
    })

    test('error state - Analytics', async ({ page }) => {
      // Mock API to return error
      await page.route('**/api/crm/analytics/**', async (route) => {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal Server Error' }),
        })
      })
      
      await page.goto('/')
      await page.click('[data-testid="nav-analytics"]')
      await page.waitForLoadState('networkidle')
      
      await expect(page).toHaveScreenshot('error-state-analytics.png', {
        fullPage: true,
        animations: 'disabled',
      })
    })
  })
})