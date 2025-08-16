# Dashboard E2E Tests

## Core Dashboard Tests (`tests/e2e/dashboard/`)

### Main Dashboard Navigation
```javascript
// dashboard-navigation.spec.ts
test('Dashboard main navigation', async ({ page }) => {
  await page.goto('/');
  
  // Test all main navigation tabs
  const tabs = ['Dashboard', 'Leads', 'Properties', 'AI Tools', 'Settings'];
  
  for (const tab of tabs) {
    await page.click(`[data-testid="${tab.toLowerCase()}-tab"]`);
    await expect(page.locator(`[data-testid="${tab.toLowerCase()}-content"]`)).toBeVisible();
  }
});

test('Dashboard responsive design', async ({ page }) => {
  // Test mobile view
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto('/dashboard');
  
  // Verify mobile navigation works
  await page.click('[data-testid="mobile-menu-toggle"]');
  await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
});
```

### Dashboard Widgets and Components
```javascript
// dashboard-widgets.spec.ts
test('Dashboard statistics widgets', async ({ page }) => {
  await page.goto('/dashboard');
  
  // Verify key metrics are displayed
  await expect(page.locator('[data-testid="total-leads"]')).toBeVisible();
  await expect(page.locator('[data-testid="active-properties"]')).toBeVisible();
  await expect(page.locator('[data-testid="recent-activity"]')).toBeVisible();
});

test('Quick actions functionality', async ({ page }) => {
  await page.goto('/dashboard');
  
  // Test quick add lead
  await page.click('[data-testid="quick-add-lead"]');
  await expect(page.locator('[data-testid="lead-form-modal"]')).toBeVisible();
  
  // Test quick post generation
  await page.click('[data-testid="quick-generate-post"]');
  await expect(page.locator('[data-testid="post-generator-modal"]')).toBeVisible();
});
```

### Form Validations
```javascript
// dashboard-forms.spec.ts
test('Lead creation form validation', async ({ page }) => {
  await page.goto('/dashboard');
  await page.click('[data-testid="leads-tab"]');
  await page.click('[data-testid="new-lead-button"]');
  
  // Test required field validation
  await page.click('[data-testid="save-lead"]');
  await expect(page.locator('[data-testid="name-error"]')).toContainText('Name is required');
  
  // Test email validation
  await page.fill('[data-testid="lead-email"]', 'invalid-email');
  await page.click('[data-testid="save-lead"]');
  await expect(page.locator('[data-testid="email-error"]')).toContainText('Invalid email format');
});

test('AI post generation form', async ({ page }) => {
  await page.goto('/dashboard');
  await page.click('[data-testid="ai-tools-tab"]');
  
  // Test property details form
  await page.fill('[data-testid="property-address"]', '123 Main St');
  await page.selectOption('[data-testid="post-template"]', 'just_listed');
  
  await page.click('[data-testid="generate-post"]');
  
  // Verify generation started
  await expect(page.locator('[data-testid="generating-indicator"]')).toBeVisible();
  
  // Wait for completion
  await page.waitForSelector('[data-testid="generated-content"]', { timeout: 10000 });
  await expect(page.locator('[data-testid="generated-content"]')).not.toBeEmpty();
});
```

### User Interface Integration
```javascript
// dashboard-integration.spec.ts
test('Facebook integration UI', async ({ page }) => {
  await page.goto('/dashboard');
  await page.click('[data-testid="settings-tab"]');
  
  // Test Facebook connection button
  const facebookButton = page.locator('[data-testid="facebook-connect"]');
  await expect(facebookButton).toBeVisible();
  
  // Note: Don't actually connect in tests, just verify UI elements
});

test('Data persistence across navigation', async ({ page }) => {
  await page.goto('/dashboard');
  
  // Fill form in AI tools
  await page.click('[data-testid="ai-tools-tab"]');
  await page.fill('[data-testid="property-address"]', '456 Oak St');
  
  // Navigate to leads
  await page.click('[data-testid="leads-tab"]');
  
  // Navigate back to AI tools
  await page.click('[data-testid="ai-tools-tab"]');
  
  // Verify data persisted (if designed to)
  const addressValue = await page.inputValue('[data-testid="property-address"]');
  // This depends on whether the app is designed to persist form data
});
```

## Critical Test Scenarios
1. **Navigation Consistency** - All tabs load correct content
2. **Form Validation** - All forms properly validate input
3. **Data Loading** - Dashboard loads without errors
4. **Responsive Design** - Works on mobile and desktop
5. **Integration Points** - Facebook, AI, and Lead components work together

## Error Scenarios
- Network connectivity issues
- API endpoint failures
- Invalid user inputs
- Session timeouts

## Performance Tests
- Dashboard load time
- Large dataset handling
- Concurrent user actions
- Memory leaks in long sessions
