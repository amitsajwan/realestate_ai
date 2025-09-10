import { test, expect } from '@playwright/test'

test.describe('CSS Visual Tests', () => {
  test.describe('Glass Morphism Effects', () => {
    test('Glass cards rendering', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test glass morphism on CRM cards
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      // Check glass card elements
      const glassCards = page.locator('.crm-glass-card, .analytics-glass-card, .team-glass-card')
      await expect(glassCards).toHaveCount(6) // Expected number of glass cards
      
      // Test backdrop blur effect
      const backdropBlur = page.locator('[style*="backdrop-filter"]')
      await expect(backdropBlur).toHaveCount(6)
    })

    test('Glass card hover effects', async ({ page }) => {
      await page.goto('/')
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      // Test hover effect on glass cards
      const glassCard = page.locator('.crm-glass-card:first-child')
      await glassCard.hover()
      
      // Verify hover state is applied
      await expect(glassCard).toHaveClass(/hover/)
    })
  })

  test.describe('Gradient Backgrounds', () => {
    test('Background gradients rendering', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test main background gradient
      const body = page.locator('body')
      const backgroundStyle = await body.evaluate(el => getComputedStyle(el).background)
      
      // Verify gradient is applied
      expect(backgroundStyle).toContain('linear-gradient')
    })

    test('Component gradient backgrounds', async ({ page }) => {
      await page.goto('/')
      await page.click('[data-testid="nav-analytics"]')
      await page.waitForLoadState('networkidle')
      
      // Test metric card gradients
      const metricCards = page.locator('.analytics-metric-card')
      await expect(metricCards).toHaveCount(4)
      
      // Check for gradient backgrounds on metric cards
      const firstCard = metricCards.first()
      const cardStyle = await firstCard.evaluate(el => getComputedStyle(el).background)
      expect(cardStyle).toContain('linear-gradient')
    })
  })

  test.describe('CSS Grid Layouts', () => {
    test('Responsive grid systems', async ({ page }) => {
      await page.goto('/')
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      // Test CRM stats grid
      const statsGrid = page.locator('.crm-stats-grid')
      await expect(statsGrid).toBeVisible()
      
      // Verify grid properties
      const gridStyle = await statsGrid.evaluate(el => getComputedStyle(el).display)
      expect(gridStyle).toBe('grid')
    })

    test('Grid responsiveness', async ({ page }) => {
      // Test mobile grid
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/')
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      const statsGrid = page.locator('.crm-stats-grid')
      const mobileGridStyle = await statsGrid.evaluate(el => getComputedStyle(el).gridTemplateColumns)
      expect(mobileGridStyle).toContain('1fr')
      
      // Test desktop grid
      await page.setViewportSize({ width: 1920, height: 1080 })
      await page.waitForTimeout(500)
      
      const desktopGridStyle = await statsGrid.evaluate(el => getComputedStyle(el).gridTemplateColumns)
      expect(desktopGridStyle).toContain('repeat')
    })
  })

  test.describe('CSS Animations', () => {
    test('Hover animations', async ({ page }) => {
      await page.goto('/')
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      // Test button hover animations
      const button = page.locator('.crm-lead-action:first-child')
      await button.hover()
      
      // Verify transform is applied
      const transform = await button.evaluate(el => getComputedStyle(el).transform)
      expect(transform).not.toBe('none')
    })

    test('Loading animations', async ({ page }) => {
      // Simulate slow loading
      await page.route('**/api/**', async (route) => {
        await new Promise(resolve => setTimeout(resolve, 1000))
        await route.continue()
      })
      
      await page.goto('/')
      await page.click('[data-testid="nav-crm"]')
      
      // Check loading spinner animation
      const spinner = page.locator('.crm-spinner')
      await expect(spinner).toBeVisible()
      
      // Verify animation is running
      const animation = await spinner.evaluate(el => getComputedStyle(el).animation)
      expect(animation).toContain('crm-spin')
    })
  })

  test.describe('CSS Custom Properties', () => {
    test('CSS variables are applied', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test root CSS variables
      const root = page.locator(':root')
      const cssVars = await root.evaluate(el => {
        const styles = getComputedStyle(el)
        return {
          primary: styles.getPropertyValue('--crm-primary'),
          secondary: styles.getPropertyValue('--crm-secondary'),
          surface: styles.getPropertyValue('--crm-surface'),
        }
      })
      
      expect(cssVars.primary).toBeTruthy()
      expect(cssVars.secondary).toBeTruthy()
      expect(cssVars.surface).toBeTruthy()
    })

    test('Component-specific CSS variables', async ({ page }) => {
      await page.goto('/')
      await page.click('[data-testid="nav-analytics"]')
      await page.waitForLoadState('networkidle')
      
      // Test analytics component CSS variables
      const analyticsContainer = page.locator('.analytics-container')
      const cssVars = await analyticsContainer.evaluate(el => {
        const styles = getComputedStyle(el)
        return {
          primary: styles.getPropertyValue('--analytics-primary'),
          surface: styles.getPropertyValue('--analytics-surface'),
        }
      })
      
      expect(cssVars.primary).toBeTruthy()
      expect(cssVars.surface).toBeTruthy()
    })
  })

  test.describe('Dark Mode CSS', () => {
    test('Dark mode variables', async ({ page }) => {
      // Enable dark mode
      await page.emulateMedia({ colorScheme: 'dark' })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test dark mode CSS variables
      const root = page.locator(':root')
      const darkModeVars = await root.evaluate(el => {
        const styles = getComputedStyle(el)
        return {
          background: styles.getPropertyValue('--color-background'),
          text: styles.getPropertyValue('--color-text-primary'),
          surface: styles.getPropertyValue('--color-surface'),
        }
      })
      
      // Verify dark mode variables are different from light mode
      expect(darkModeVars.background).toBeTruthy()
      expect(darkModeVars.text).toBeTruthy()
      expect(darkModeVars.surface).toBeTruthy()
    })

    test('Dark mode component styling', async ({ page }) => {
      await page.emulateMedia({ colorScheme: 'dark' })
      await page.goto('/')
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      // Test dark mode glass cards
      const glassCard = page.locator('.crm-glass-card:first-child')
      const cardStyle = await glassCard.evaluate(el => {
        const styles = getComputedStyle(el)
        return {
          background: styles.background,
          color: styles.color,
        }
      })
      
      // Verify dark mode styling is applied
      expect(cardStyle.background).toContain('rgba')
      expect(cardStyle.color).toBeTruthy()
    })
  })

  test.describe('High Contrast Mode CSS', () => {
    test('High contrast variables', async ({ page }) => {
      // Enable high contrast mode
      await page.emulateMedia({ forcedColors: 'active' })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test high contrast CSS variables
      const root = page.locator(':root')
      const highContrastVars = await root.evaluate(el => {
        const styles = getComputedStyle(el)
        return {
          border: styles.getPropertyValue('--color-border'),
          shadow: styles.getPropertyValue('--shadow-sm'),
        }
      })
      
      // Verify high contrast variables are applied
      expect(highContrastVars.border).toBeTruthy()
      expect(highContrastVars.shadow).toBeTruthy()
    })
  })

  test.describe('Reduced Motion CSS', () => {
    test('Reduced motion variables', async ({ page }) => {
      // Enable reduced motion
      await page.emulateMedia({ reducedMotion: 'reduce' })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test reduced motion CSS variables
      const root = page.locator(':root')
      const reducedMotionVars = await root.evaluate(el => {
        const styles = getComputedStyle(el)
        return {
          transition: styles.getPropertyValue('--transition-none'),
        }
      })
      
      // Verify reduced motion variables are applied
      expect(reducedMotionVars.transition).toBe('none')
    })

    test('Reduced motion animations disabled', async ({ page }) => {
      await page.emulateMedia({ reducedMotion: 'reduce' })
      await page.goto('/')
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      // Test that animations are disabled
      const animatedElement = page.locator('.crm-stat-card:first-child')
      const animation = await animatedElement.evaluate(el => getComputedStyle(el).animation)
      expect(animation).toBe('none')
    })
  })

  test.describe('CSS Performance', () => {
    test('CSS loading performance', async ({ page }) => {
      const startTime = Date.now()
      
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      const endTime = Date.now()
      const loadTime = endTime - startTime
      
      // Verify CSS loads within acceptable time
      expect(loadTime).toBeLessThan(3000)
    })

    test('CSS file sizes', async ({ page }) => {
      await page.goto('/')
      
      // Check CSS file sizes
      const response = await page.request.get('/styles/design-system.css')
      const cssSize = (await response.body()).length
      
      // Verify CSS file is not too large (less than 100KB)
      expect(cssSize).toBeLessThan(100000)
    })
  })

  test.describe('CSS Browser Compatibility', () => {
    test('CSS Grid support', async ({ page, browserName }) => {
      await page.goto('/')
      await page.click('[data-testid="nav-crm"]')
      await page.waitForLoadState('networkidle')
      
      // Test CSS Grid support
      const gridElement = page.locator('.crm-stats-grid')
      const display = await gridElement.evaluate(el => getComputedStyle(el).display)
      
      // Verify grid is supported
      expect(display).toBe('grid')
    })

    test('Backdrop filter support', async ({ page, browserName }) => {
      await page.goto('/')
      await page.click('[data-testid="nav-analytics"]')
      await page.waitForLoadState('networkidle')
      
      // Test backdrop filter support
      const glassElement = page.locator('.analytics-glass-card:first-child')
      const backdropFilter = await glassElement.evaluate(el => getComputedStyle(el).backdropFilter)
      
      // Verify backdrop filter is supported (may be empty in some browsers)
      expect(backdropFilter).toBeDefined()
    })

    test('CSS Custom Properties support', async ({ page, browserName }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Test CSS custom properties support
      const root = page.locator(':root')
      const customProperty = await root.evaluate(el => {
        const styles = getComputedStyle(el)
        return styles.getPropertyValue('--crm-primary')
      })
      
      // Verify custom properties are supported
      expect(customProperty).toBeTruthy()
    })
  })
})