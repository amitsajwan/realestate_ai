# 🎭 E2E Visual Testing with Playwright

## **📋 Overview**

This directory contains comprehensive End-to-End (E2E) visual testing using Playwright for our real estate platform. These tests focus on visual regression, cross-browser compatibility, responsive design, and CSS functionality.

## **🎯 Testing Strategy**

### **What We Test:**
- ✅ **Visual Regression** - Screenshot comparisons across changes
- ✅ **Cross-Browser Compatibility** - Chrome, Firefox, Safari, Edge
- ✅ **Responsive Design** - Mobile, tablet, desktop layouts
- ✅ **CSS Functionality** - Glass morphism, gradients, animations
- ✅ **Accessibility** - Keyboard navigation, screen readers
- ✅ **Performance** - Load times, memory usage

### **What We DON'T Test:**
- ❌ **Unit/Integration Logic** - Handled by Jest tests
- ❌ **API Functionality** - Mocked for visual consistency
- ❌ **Business Logic** - Tested in component tests

## **🚀 Getting Started**

### **Installation**
```bash
# Install Playwright and browsers
npm run playwright:install

# Install system dependencies (Linux)
npm run playwright:install-deps
```

### **Running Tests**
```bash
# Run all E2E tests
npm run test:e2e

# Run specific test suites
npm run test:visual          # Visual regression tests
npm run test:cross-browser   # Cross-browser tests
npm run test:responsive      # Responsive design tests
npm run test:css            # CSS visual tests

# Run with UI (interactive mode)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Debug mode
npm run test:e2e:debug
```

## **📁 Test Structure**

```
e2e/
├── visual-regression.spec.ts    # Screenshot comparisons
├── cross-browser.spec.ts        # Browser compatibility
├── responsive-design.spec.ts    # Mobile/tablet/desktop
├── css-visual-tests.spec.ts     # CSS functionality
├── global-setup.ts              # Test setup
├── global-teardown.ts           # Test cleanup
├── test-data-attributes.md      # Required test IDs
└── README.md                    # This file
```

## **🎨 Visual Regression Testing**

### **Screenshot Comparisons**
- **Full Page Screenshots** - Complete page layouts
- **Component Screenshots** - Individual component states
- **Modal Screenshots** - Overlay and dialog states
- **Loading States** - Spinner and skeleton screens
- **Error States** - Error messages and fallbacks

### **Test Categories**
```typescript
// Dashboard layouts
test('main dashboard layout', async ({ page }) => {
  await expect(page).toHaveScreenshot('dashboard-main-layout.png')
})

// Component states
test('CRM lead detail modal', async ({ page }) => {
  await expect(modal).toHaveScreenshot('crm-lead-detail-modal.png')
})

// Responsive layouts
test('mobile layout - iPhone 12', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await expect(page).toHaveScreenshot('mobile-layout-iphone12.png')
})
```

## **🌐 Cross-Browser Testing**

### **Supported Browsers**
- **Chrome** - Latest stable
- **Firefox** - Latest stable
- **Safari/WebKit** - Latest stable
- **Edge** - Latest stable
- **Mobile Chrome** - Android
- **Mobile Safari** - iOS

### **Test Coverage**
```typescript
// Browser-specific tests
test('CRM functionality in Chrome', async ({ page, browserName }) => {
  test.skip(browserName !== 'chromium', 'Chrome specific test')
  // Chrome-specific functionality
})

// Cross-browser compatibility
test('Modal functionality - All browsers', async ({ page }) => {
  // Test that works across all browsers
})
```

## **📱 Responsive Design Testing**

### **Device Breakpoints**
- **Mobile**: 375px, 390px, 393px
- **Tablet**: 768px, 912px, 1024px
- **Desktop**: 1280px, 1440px, 1920px, 2560px

### **Test Scenarios**
```typescript
// Mobile navigation
test('iPhone SE (375x667)', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 })
  // Test mobile layout
})

// Tablet layout
test('iPad (768x1024)', async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 1024 })
  // Test tablet layout
})

// Desktop layout
test('Desktop Large (1920x1080)', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  // Test desktop layout
})
```

## **🎨 CSS Visual Testing**

### **CSS Features Tested**
- **Glass Morphism** - Backdrop blur effects
- **Gradient Backgrounds** - Linear and radial gradients
- **CSS Grid** - Responsive grid layouts
- **CSS Animations** - Hover and loading animations
- **CSS Custom Properties** - CSS variables
- **Dark Mode** - Color scheme switching
- **High Contrast** - Accessibility mode
- **Reduced Motion** - Animation preferences

### **Test Examples**
```typescript
// Glass morphism effects
test('Glass cards rendering', async ({ page }) => {
  const glassCards = page.locator('.crm-glass-card')
  await expect(glassCards).toHaveCount(6)
})

// CSS animations
test('Hover animations', async ({ page }) => {
  const button = page.locator('.crm-lead-action:first-child')
  await button.hover()
  const transform = await button.evaluate(el => getComputedStyle(el).transform)
  expect(transform).not.toBe('none')
})

// Dark mode
test('Dark mode variables', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'dark' })
  // Test dark mode styling
})
```

## **♿ Accessibility Testing**

### **Accessibility Features**
- **Keyboard Navigation** - Tab order and focus management
- **Screen Reader Support** - ARIA labels and roles
- **Color Contrast** - WCAG compliance
- **Focus Indicators** - Visible focus states
- **Semantic HTML** - Proper heading hierarchy

### **Test Examples**
```typescript
// Keyboard navigation
test('Keyboard navigation - All browsers', async ({ page }) => {
  await page.keyboard.press('Tab')
  await page.keyboard.press('Tab')
  const focusedElement = page.locator(':focus')
  await expect(focusedElement).toBeVisible()
})

// Screen reader compatibility
test('Screen reader compatibility', async ({ page }) => {
  const ariaLabels = page.locator('[aria-label]')
  await expect(ariaLabels).toHaveCount(4)
})
```

## **⚡ Performance Testing**

### **Performance Metrics**
- **Page Load Time** - Initial page load
- **Component Render Time** - Individual component performance
- **Memory Usage** - Memory leaks and efficiency
- **Network Performance** - API response times

### **Test Examples**
```typescript
// Page load performance
test('Page load performance', async ({ page }) => {
  const startTime = Date.now()
  await page.goto('/')
  await page.waitForLoadState('networkidle')
  const endTime = Date.now()
  expect(endTime - startTime).toBeLessThan(5000)
})

// Memory usage
test('Memory usage', async ({ page }) => {
  // Navigate through different sections
  // Check for memory leaks
})
```

## **🔧 Configuration**

### **Playwright Config**
```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    // ... more browsers
  ],
})
```

### **Global Setup**
```typescript
// global-setup.ts
async function globalSetup(config: FullConfig) {
  // Start application
  // Set up test data
  // Configure mocks
}
```

## **📊 Test Data**

### **Mock Data**
- **API Responses** - Consistent test data
- **User Authentication** - Mock user sessions
- **Component States** - Loading, error, success states
- **Responsive Data** - Different screen sizes

### **Test IDs**
All components need `data-testid` attributes:
```tsx
<div data-testid="crm-dashboard">
  <div data-testid="crm-stats">
    <div data-testid="metric-card">
      {/* Content */}
    </div>
  </div>
</div>
```

## **🚀 CI/CD Integration**

### **GitHub Actions**
- **Visual Regression** - Screenshot comparisons
- **Cross-Browser** - Multi-browser testing
- **Responsive Design** - Device testing
- **CSS Visual** - Styling verification
- **Performance** - Load time testing
- **Accessibility** - A11y compliance

### **Artifacts**
- **Screenshots** - Visual comparison results
- **Videos** - Test execution recordings
- **Traces** - Debug information
- **Reports** - Test results and coverage

## **🐛 Debugging**

### **Debug Mode**
```bash
# Run tests in debug mode
npm run test:e2e:debug

# Run specific test in debug mode
npx playwright test visual-regression.spec.ts --debug
```

### **UI Mode**
```bash
# Interactive test runner
npm run test:e2e:ui
```

### **Headed Mode**
```bash
# See browser during tests
npm run test:e2e:headed
```

## **📈 Best Practices**

### **Test Organization**
- **Group related tests** in describe blocks
- **Use descriptive test names** that explain the scenario
- **Keep tests independent** - no shared state
- **Clean up after tests** - reset state

### **Screenshot Management**
- **Use consistent naming** for screenshots
- **Include viewport size** in mobile screenshots
- **Test all states** - loading, error, success
- **Update screenshots** when UI changes intentionally

### **Performance**
- **Run tests in parallel** when possible
- **Use page.goto()** instead of navigation
- **Wait for network idle** before taking screenshots
- **Disable animations** for consistent screenshots

## **🔍 Troubleshooting**

### **Common Issues**
1. **Screenshots don't match** - Check viewport size and timing
2. **Tests are flaky** - Add proper waits and timeouts
3. **Browser not found** - Run `npm run playwright:install`
4. **Application not starting** - Check port 3000 is available

### **Debug Tips**
- Use `page.screenshot()` for debugging
- Check browser console for errors
- Use `page.waitForSelector()` for dynamic content
- Verify test data attributes are present

## **📚 Resources**

- [Playwright Documentation](https://playwright.dev/)
- [Visual Testing Guide](https://playwright.dev/docs/test-snapshots)
- [Cross-Browser Testing](https://playwright.dev/docs/browsers)
- [Responsive Testing](https://playwright.dev/docs/emulation)
- [Accessibility Testing](https://playwright.dev/docs/accessibility-testing)

---

**Remember**: E2E tests should focus on **user experience** and **visual consistency**, not implementation details! 🎭✨