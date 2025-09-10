import { test, expect } from '@playwright/test'

test.describe('Cross-Browser Compatibility', () => {
  test.describe('Chrome', () => {
    test('CRM functionality in Chrome', async ({ page, browserName }) => {
      test.skip(browserName !== 'chromium', 'Chrome specific test')
      
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Navigate to CRM
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      // Test search functionality
      await page.fill('[data-testid="search-input"]', 'John')
      await page.waitForTimeout(500)
      
      // Verify search results
      const searchResults = page.locator('[data-testid="lead-item"]')
      await expect(searchResults).toHaveCount(1)
      
      // Test lead modal
      await page.click('[data-testid="lead-view-button"]:first-child')
      await page.waitForSelector('[data-testid="lead-detail-modal"]')
      
      const modal = page.locator('[data-testid="lead-detail-modal"]')
      await expect(modal).toBeVisible()
    })

    test('Analytics charts in Chrome', async ({ page, browserName }) => {
      test.skip(browserName !== 'chromium', 'Chrome specific test')
      
      await page.goto('/')
      await page.click('[data-testid="nav-analytics"]')
      await page.waitForLoadState('networkidle')
      
      // Test chart rendering
      const charts = page.locator('[data-testid="chart-container"]')
      await expect(charts).toHaveCount(2)
      
      // Test period selector
      await page.selectOption('[data-testid="period-selector"]', 'this_week')
      await page.waitForLoadState('networkidle')
      
      // Verify data updates
      const metrics = page.locator('[data-testid="metric-card"]')
      await expect(metrics).toHaveCount(4)
    })
  })

  test.describe('Firefox', () => {
    test('CRM functionality in Firefox', async ({ page, browserName }) => {
      test.skip(browserName !== 'firefox', 'Firefox specific test')
      
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Navigate to CRM
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      // Test filtering
      await page.click('[data-testid="filters-button"]')
      await page.selectOption('[data-testid="status-filter"]', 'new')
      await page.waitForLoadState('networkidle')
      
      // Verify filter results
      const filteredLeads = page.locator('[data-testid="lead-item"]')
      await expect(filteredLeads).toHaveCount(1)
    })

    test('Team management in Firefox', async ({ page, browserName }) => {
      test.skip(browserName !== 'firefox', 'Firefox specific test')
      
      await page.goto('/')
      await page.click('[data-testid="nav-team-management"]')
      await page.waitForLoadState('networkidle')
      
      // Test team member role change
      const roleSelect = page.locator('[data-testid="member-role-select"]:first-child')
      await roleSelect.selectOption('assistant')
      
      // Verify success message
      await expect(page.locator('[data-testid="success-message"]')).toBeVisible()
    })
  })

  test.describe('Safari/WebKit', () => {
    test('Analytics in Safari', async ({ page, browserName }) => {
      test.skip(browserName !== 'webkit', 'Safari specific test')
      
      await page.goto('/')
      await page.click('[data-testid="nav-analytics"]')
      await page.waitForLoadState('networkidle')
      
      // Test responsive layout
      await page.setViewportSize({ width: 1024, height: 768 })
      await page.waitForTimeout(500)
      
      // Verify layout adapts correctly
      const metricsGrid = page.locator('[data-testid="metrics-grid"]')
      await expect(metricsGrid).toBeVisible()
    })

    test('Modal functionality in Safari', async ({ page, browserName }) => {
      test.skip(browserName !== 'webkit', 'Safari specific test')
      
      await page.goto('/')
      await page.click('[data-testid="nav-team-management"]')
      await page.waitForLoadState('networkidle')
      
      // Test modal opening
      await page.click('[data-testid="invite-member-button"]')
      await page.waitForSelector('[data-testid="invite-modal"]')
      
      // Test modal form
      await page.fill('[data-testid="invite-email"]', 'test@example.com')
      await page.selectOption('[data-testid="invite-role"]', 'agent')
      
      // Test modal closing
      await page.click('[data-testid="modal-close"]')
      await expect(page.locator('[data-testid="invite-modal"]')).not.toBeVisible()
    })
  })

  test.describe('Mobile Browsers', () => {
    test('Mobile Chrome - CRM', async ({ page, browserName }) => {
      test.skip(browserName !== 'chromium', 'Mobile Chrome test')
      
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test mobile navigation
      await page.click('[data-testid="mobile-menu-toggle"]')
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      // Test mobile search
      await page.fill('[data-testid="search-input"]', 'test')
      await page.waitForTimeout(500)
      
      // Verify mobile layout
      const leadCards = page.locator('[data-testid="lead-card"]')
      await expect(leadCards).toHaveCount(2)
    })

    test('Mobile Safari - Analytics', async ({ page, browserName }) => {
      test.skip(browserName !== 'webkit', 'Mobile Safari test')
      
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test mobile navigation
      await page.click('[data-testid="mobile-menu-toggle"]')
      await page.click('[data-testid="nav-analytics"]')
      await page.waitForLoadState('networkidle')
      
      // Test mobile charts
      const charts = page.locator('[data-testid="chart-container"]')
      await expect(charts).toHaveCount(2)
      
      // Test mobile period selector
      await page.selectOption('[data-testid="period-selector"]', 'this_week')
      await page.waitForLoadState('networkidle')
    })
  })

  test.describe('Edge Cases', () => {
    test('Slow network - All browsers', async ({ page }) => {
      // Simulate slow network
      await page.route('**/api/**', async (route) => {
        await new Promise(resolve => setTimeout(resolve, 2000))
        await route.continue()
      })
      
      await page.goto('/')
      await page.click('[data-testid="nav-crm"]')
      
      // Verify loading state
      await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible()
      
      // Wait for content to load
      await page.waitForSelector('[data-testid="crm-dashboard"]', { timeout: 10000 })
      await expect(page.locator('[data-testid="loading-spinner"]')).not.toBeVisible()
    })

    test('Offline mode - All browsers', async ({ page }) => {
      // Go offline
      await page.context().setOffline(true)
      
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Verify error handling
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
      
      // Go back online
      await page.context().setOffline(false)
      await page.reload()
      await page.waitForLoadState('networkidle')
      
      // Verify recovery
      await expect(page.locator('[data-testid="error-message"]')).not.toBeVisible()
    })

    test('High DPI displays - All browsers', async ({ page }) => {
      // Test high DPI rendering
      await page.setViewportSize({ width: 1920, height: 1080 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test zoom levels
      await page.evaluate(() => {
        document.body.style.zoom = '1.5'
      })
      
      await page.waitForTimeout(500)
      
      // Verify layout still works
      const mainContent = page.locator('[data-testid="main-content"]')
      await expect(mainContent).toBeVisible()
    })
  })

  test.describe('Accessibility - Cross Browser', () => {
    test('Keyboard navigation - All browsers', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test tab navigation
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')
      
      // Verify focus is visible
      const focusedElement = page.locator(':focus')
      await expect(focusedElement).toBeVisible()
      
      // Test Enter key
      await page.keyboard.press('Enter')
      
      // Verify navigation worked
      await page.waitForLoadState('networkidle')
    })

    test('Screen reader compatibility - All browsers', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Check for proper ARIA labels
      const buttons = page.locator('button[aria-label]')
      await expect(buttons).toHaveCount(4) // Expected number of buttons with aria-labels
      
      // Check for proper headings
      const headings = page.locator('h1, h2, h3, h4, h5, h6')
      await expect(headings).toHaveCount(6) // Expected number of headings
      
      // Check for proper form labels
      const formInputs = page.locator('input[aria-label], input[aria-labelledby]')
      await expect(formInputs).toHaveCount(2) // Expected number of labeled inputs
    })
  })

  test.describe('Performance - Cross Browser', () => {
    test('Page load performance - All browsers', async ({ page }) => {
      const startTime = Date.now()
      
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      const endTime = Date.now()
      const loadTime = endTime - startTime
      
      // Verify page loads within acceptable time (5 seconds)
      expect(loadTime).toBeLessThan(5000)
    })

    test('Memory usage - All browsers', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Navigate through different sections
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      await page.click('[data-testid="nav-analytics"]')
      await page.waitForLoadState('networkidle')
      
      await page.click('[data-testid="nav-team-management"]')
      await page.waitForLoadState('networkidle')
      
      // Check for memory leaks by ensuring page still works
      await page.click('[data-testid="nav-crm"]')
      await expect(page.locator('[data-testid="crm-dashboard"]')).toBeVisible()
    })
  })
})