import { test, expect } from '@playwright/test'

test.describe('Responsive Design Tests', () => {
  test.describe('Mobile Devices', () => {
    test('iPhone SE (375x667)', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test mobile navigation
      const mobileMenu = page.locator('[data-testid="mobile-menu-toggle"]')
      await expect(mobileMenu).toBeVisible()
      
      // Test mobile menu functionality
      await mobileMenu.click()
      const mobileNav = page.locator('[data-testid="mobile-navigation"]')
      await expect(mobileNav).toBeVisible()
      
      // Test mobile menu items
      const navItems = page.locator('[data-testid="mobile-nav-item"]')
      await expect(navItems).toHaveCount(6) // Expected number of nav items
      
      // Test mobile CRM layout
      await page.click('[data-testid="mobile-nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      // Verify mobile CRM layout
      const crmDashboard = page.locator('[data-testid="crm-dashboard"]')
      await expect(crmDashboard).toBeVisible()
      
      // Test mobile search
      const searchInput = page.locator('[data-testid="search-input"]')
      await expect(searchInput).toBeVisible()
      
      // Test mobile lead cards
      const leadCards = page.locator('[data-testid="lead-card"]')
      await expect(leadCards).toHaveCount(2)
      
      // Verify mobile lead card layout
      const firstLeadCard = leadCards.first()
      await expect(firstLeadCard).toBeVisible()
    })

    test('iPhone 12 (390x844)', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test Analytics on iPhone 12
      await page.click('[data-testid="mobile-menu-toggle"]')
      await page.click('[data-testid="mobile-nav-analytics"]')
      await page.waitForLoadState('networkidle')
      
      // Verify mobile analytics layout
      const analyticsDashboard = page.locator('[data-testid="analytics-dashboard"]')
      await expect(analyticsDashboard).toBeVisible()
      
      // Test mobile metrics grid
      const metricsGrid = page.locator('[data-testid="metrics-grid"]')
      await expect(metricsGrid).toBeVisible()
      
      // Verify metrics stack vertically on mobile
      const metricCards = page.locator('[data-testid="metric-card"]')
      await expect(metricCards).toHaveCount(4)
      
      // Test mobile charts
      const charts = page.locator('[data-testid="chart-container"]')
      await expect(charts).toHaveCount(2)
    })

    test('Pixel 5 (393x851)', async ({ page }) => {
      await page.setViewportSize({ width: 393, height: 851 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test Team Management on Pixel 5
      await page.click('[data-testid="mobile-menu-toggle"]')
      await page.click('[data-testid="mobile-nav-team-management"]')
      await page.waitForLoadState('networkidle')
      
      // Verify mobile team management layout
      const teamManagement = page.locator('[data-testid="team-management"]')
      await expect(teamManagement).toBeVisible()
      
      // Test mobile team stats
      const teamStats = page.locator('[data-testid="team-stats"]')
      await expect(teamStats).toBeVisible()
      
      // Test mobile team members list
      const membersList = page.locator('[data-testid="team-members-list"]')
      await expect(membersList).toBeVisible()
      
      // Test mobile invite button
      const inviteButton = page.locator('[data-testid="invite-member-button"]')
      await expect(inviteButton).toBeVisible()
    })
  })

  test.describe('Tablet Devices', () => {
    test('iPad (768x1024)', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test tablet navigation
      const desktopNav = page.locator('[data-testid="desktop-navigation"]')
      await expect(desktopNav).toBeVisible()
      
      // Test tablet CRM layout
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      // Verify tablet CRM layout
      const crmDashboard = page.locator('[data-testid="crm-dashboard"]')
      await expect(crmDashboard).toBeVisible()
      
      // Test tablet metrics grid (2 columns)
      const metricsGrid = page.locator('[data-testid="metrics-grid"]')
      await expect(metricsGrid).toBeVisible()
      
      // Test tablet lead cards
      const leadCards = page.locator('[data-testid="lead-card"]')
      await expect(leadCards).toHaveCount(2)
    })

    test('iPad Pro (1024x1366)', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 1366 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test Analytics on iPad Pro
      await page.click('[data-testid="nav-analytics"]')
      await page.waitForLoadState('networkidle')
      
      // Verify tablet analytics layout
      const analyticsDashboard = page.locator('[data-testid="analytics-dashboard"]')
      await expect(analyticsDashboard).toBeVisible()
      
      // Test tablet metrics grid (4 columns)
      const metricsGrid = page.locator('[data-testid="metrics-grid"]')
      await expect(metricsGrid).toBeVisible()
      
      // Test tablet charts layout
      const chartsGrid = page.locator('[data-testid="charts-grid"]')
      await expect(chartsGrid).toBeVisible()
    })

    test('Surface Pro (912x1368)', async ({ page }) => {
      await page.setViewportSize({ width: 912, height: 1368 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test Team Management on Surface Pro
      await page.click('[data-testid="nav-team-management"]')
      await page.waitForLoadState('networkidle')
      
      // Verify tablet team management layout
      const teamManagement = page.locator('[data-testid="team-management"]')
      await expect(teamManagement).toBeVisible()
      
      // Test tablet team stats (3 columns)
      const teamStats = page.locator('[data-testid="team-stats"]')
      await expect(teamStats).toBeVisible()
      
      // Test tablet team members list
      const membersList = page.locator('[data-testid="team-members-list"]')
      await expect(membersList).toBeVisible()
    })
  })

  test.describe('Desktop Devices', () => {
    test('Desktop Small (1280x720)', async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 720 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test desktop navigation
      const desktopNav = page.locator('[data-testid="desktop-navigation"]')
      await expect(desktopNav).toBeVisible()
      
      // Test CRM on small desktop
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      // Verify desktop CRM layout
      const crmDashboard = page.locator('[data-testid="crm-dashboard"]')
      await expect(crmDashboard).toBeVisible()
      
      // Test desktop metrics grid (4 columns)
      const metricsGrid = page.locator('[data-testid="metrics-grid"]')
      await expect(metricsGrid).toBeVisible()
    })

    test('Desktop Medium (1440x900)', async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 900 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test Analytics on medium desktop
      await page.click('[data-testid="nav-analytics"]')
      await page.waitForLoadState('networkidle')
      
      // Verify desktop analytics layout
      const analyticsDashboard = page.locator('[data-testid="analytics-dashboard"]')
      await expect(analyticsDashboard).toBeVisible()
      
      // Test desktop charts layout (2 columns)
      const chartsGrid = page.locator('[data-testid="charts-grid"]')
      await expect(chartsGrid).toBeVisible()
    })

    test('Desktop Large (1920x1080)', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test Team Management on large desktop
      await page.click('[data-testid="nav-team-management"]')
      await page.waitForLoadState('networkidle')
      
      // Verify desktop team management layout
      const teamManagement = page.locator('[data-testid="team-management"]')
      await expect(teamManagement).toBeVisible()
      
      // Test desktop team stats (3 columns)
      const teamStats = page.locator('[data-testid="team-stats"]')
      await expect(teamStats).toBeVisible()
    })

    test('Desktop Extra Large (2560x1440)', async ({ page }) => {
      await page.setViewportSize({ width: 2560, height: 1440 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test all sections on extra large desktop
      const sections = ['crm', 'analytics', 'team-management']
      
      for (const section of sections) {
        await page.click(`[data-testid="nav-${section}"]`)
        await page.waitForLoadState('networkidle')
        
        const dashboard = page.locator(`[data-testid="${section}-dashboard"]`)
        await expect(dashboard).toBeVisible()
      }
    })
  })

  test.describe('Orientation Changes', () => {
    test('Portrait to Landscape - Mobile', async ({ page }) => {
      // Start in portrait
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test portrait layout
      const mobileMenu = page.locator('[data-testid="mobile-menu-toggle"]')
      await expect(mobileMenu).toBeVisible()
      
      // Switch to landscape
      await page.setViewportSize({ width: 667, height: 375 })
      await page.waitForTimeout(500)
      
      // Test landscape layout
      const desktopNav = page.locator('[data-testid="desktop-navigation"]')
      await expect(desktopNav).toBeVisible()
    })

    test('Landscape to Portrait - Tablet', async ({ page }) => {
      // Start in landscape
      await page.setViewportSize({ width: 1024, height: 768 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test landscape layout
      const desktopNav = page.locator('[data-testid="desktop-navigation"]')
      await expect(desktopNav).toBeVisible()
      
      // Switch to portrait
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.waitForTimeout(500)
      
      // Test portrait layout
      const tabletNav = page.locator('[data-testid="tablet-navigation"]')
      await expect(tabletNav).toBeVisible()
    })
  })

  test.describe('Breakpoint Transitions', () => {
    test('Mobile to Tablet transition', async ({ page }) => {
      // Start mobile
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Verify mobile layout
      const mobileMenu = page.locator('[data-testid="mobile-menu-toggle"]')
      await expect(mobileMenu).toBeVisible()
      
      // Transition to tablet
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.waitForTimeout(500)
      
      // Verify tablet layout
      const desktopNav = page.locator('[data-testid="desktop-navigation"]')
      await expect(desktopNav).toBeVisible()
    })

    test('Tablet to Desktop transition', async ({ page }) => {
      // Start tablet
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Verify tablet layout
      const tabletNav = page.locator('[data-testid="tablet-navigation"]')
      await expect(tabletNav).toBeVisible()
      
      // Transition to desktop
      await page.setViewportSize({ width: 1280, height: 720 })
      await page.waitForTimeout(500)
      
      // Verify desktop layout
      const desktopNav = page.locator('[data-testid="desktop-navigation"]')
      await expect(desktopNav).toBeVisible()
    })
  })

  test.describe('Touch Interactions', () => {
    test('Touch gestures on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test touch navigation
      await page.tap('[data-testid="mobile-menu-toggle"]')
      const mobileNav = page.locator('[data-testid="mobile-navigation"]')
      await expect(mobileNav).toBeVisible()
      
      // Test touch on CRM
      await page.tap('[data-testid="mobile-nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      // Test touch on lead card
      const leadCard = page.locator('[data-testid="lead-card"]:first-child')
      await page.tap(leadCard)
      
      // Verify touch interaction worked
      const leadModal = page.locator('[data-testid="lead-detail-modal"]')
      await expect(leadModal).toBeVisible()
    })

    test('Swipe gestures on tablet', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test swipe on analytics charts
      await page.click('[data-testid="nav-analytics"]')
      await page.waitForLoadState('networkidle')
      
      const chart = page.locator('[data-testid="chart-container"]:first-child')
      
      // Simulate swipe gesture
      await page.hover(chart)
      await page.mouse.down()
      await page.mouse.move(100, 0)
      await page.mouse.up()
      
      // Verify chart interaction
      await expect(chart).toBeVisible()
    })
  })

  test.describe('Accessibility - Responsive', () => {
    test('Mobile accessibility', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test mobile keyboard navigation
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')
      
      // Verify focus is visible on mobile
      const focusedElement = page.locator(':focus')
      await expect(focusedElement).toBeVisible()
      
      // Test mobile screen reader
      const ariaLabels = page.locator('[aria-label]')
      await expect(ariaLabels).toHaveCount(4) // Expected number of aria labels
    })

    test('Tablet accessibility', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test tablet keyboard navigation
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')
      
      // Verify focus is visible on tablet
      const focusedElement = page.locator(':focus')
      await expect(focusedElement).toBeVisible()
    })
  })
})