import { test, expect } from '@playwright/test';

// Dashboard Navigation Test
test('dashboard main navigation works correctly', async ({ page }) => {
  await page.goto('/');
  
  // Test all main navigation tabs
  const tabs = [
    { id: 'dashboard-tab', content: 'dashboard-content' },
    { id: 'leads-tab', content: 'leads-content' },
    { id: 'properties-tab', content: 'properties-content' },
    { id: 'ai-tools-tab', content: 'ai-tools-content' },
    { id: 'settings-tab', content: 'settings-content' }
  ];
  
  for (const tab of tabs) {
    await page.click(`[data-testid="${tab.id}"]`);
    await expect(page.locator(`[data-testid="${tab.content}"]`)).toBeVisible();
  }
});

// AI Post Generation Test  
test('AI post generation works from dashboard', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid="ai-tools-tab"]');
  
  // Fill property details
  await page.fill('[data-testid="property-address"]', '123 Main Street');
  await page.fill('[data-testid="property-price"]', '500000');
  await page.selectOption('[data-testid="post-template"]', 'just_listed');
  
  // Generate post
  await page.click('[data-testid="generate-post"]');
  
  // Wait for generation to complete (AI can take time)
  await page.waitForSelector('[data-testid="generated-content"]', { timeout: 15000 });
  
  // Verify content was generated
  const content = await page.textContent('[data-testid="generated-content"]');
  expect(content).toBeTruthy();
  expect(content.length).toBeGreaterThan(50);
});

// Lead Creation Test
test('lead creation form works correctly', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid="leads-tab"]');
  
  // Open new lead form
  await page.click('[data-testid="new-lead-button"]');
  
  // Fill required fields
  await page.fill('[data-testid="lead-name"]', 'Test Lead');
  await page.fill('[data-testid="lead-email"]', 'test@example.com');
  await page.fill('[data-testid="lead-phone"]', '555-0123');
  
  // Submit form
  await page.click('[data-testid="save-lead"]');
  
  // Verify success
  await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  await expect(page.locator('[data-testid="lead-list"]')).toContainText('Test Lead');
});

// Facebook Integration UI Test
test('facebook connection UI is present', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid="settings-tab"]');
  
  // Verify Facebook integration elements exist
  await expect(page.locator('[data-testid="facebook-connect"]')).toBeVisible();
  await expect(page.locator('[data-testid="facebook-status"]')).toBeVisible();
  
  // Note: We don't actually connect in tests, just verify UI
});

// Form Validation Test
test('form validation works correctly', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid="leads-tab"]');
  await page.click('[data-testid="new-lead-button"]');
  
  // Try to submit empty form
  await page.click('[data-testid="save-lead"]');
  
  // Verify validation errors appear
  await expect(page.locator('[data-testid="name-error"]')).toBeVisible();
  await expect(page.locator('[data-testid="email-error"]')).toBeVisible();
  
  // Test invalid email
  await page.fill('[data-testid="lead-name"]', 'Test');
  await page.fill('[data-testid="lead-email"]', 'invalid-email');
  await page.click('[data-testid="save-lead"]');
  
  await expect(page.locator('[data-testid="email-error"]')).toContainText('Invalid email');
});

// Responsive Design Test
test('dashboard works on mobile devices', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto('/');
  
  // Verify mobile navigation
  await page.click('[data-testid="mobile-menu-toggle"]');
  await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
  
  // Test mobile tab navigation
  await page.click('[data-testid="mobile-leads-tab"]');
  await expect(page.locator('[data-testid="leads-content"]')).toBeVisible();
});
