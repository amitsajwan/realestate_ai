import { test, expect } from '@playwright/test';

/**
 * Natural Language Test: Analytics Dashboard Flow
 * ==============================================
 * 
 * Test Description: "User can view and interact with analytics dashboard"
 * 
 * This test validates the analytics dashboard functionality:
 * - View key performance metrics
 * - Interact with charts and visualizations
 * - Filter data by time periods
 * - Export analytics reports
 * - View AI-powered insights and recommendations
 */

test.describe('Analytics Dashboard Flow - Natural Language Testing', () => {
  test.beforeEach(async ({ page }) => {
    // Natural Language: "Login and navigate to analytics"
    await page.goto('/login');
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.click('button[type="submit"]');
    await page.click('text=Analytics');
  });
  
  test('User can view and interact with analytics dashboard', async ({ page }) => {
    // Natural Language: "Verify analytics dashboard loads with key metrics"
    await expect(page.locator('text=Analytics Dashboard')).toBeVisible();
    await expect(page.locator('[data-testid="total-properties"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-views"]')).toBeVisible();
    await expect(page.locator('[data-testid="conversion-rate"]')).toBeVisible();
    await expect(page.locator('[data-testid="revenue"]')).toBeVisible();
    
    // Natural Language: "View property performance charts"
    await page.click('text=Property Performance');
    await expect(page.locator('[data-testid="property-performance-chart"]')).toBeVisible();
    
    // Natural Language: "Filter data by time period"
    await page.selectOption('select[name="time-period"]', 'last-30-days');
    await expect(page.locator('text=Last 30 Days')).toBeVisible();
    
    // Natural Language: "View revenue trends"
    await page.click('text=Revenue Trends');
    await expect(page.locator('[data-testid="revenue-chart"]')).toBeVisible();
    
    // Natural Language: "Interact with chart elements"
    await page.hover('[data-testid="revenue-chart"] .recharts-bar');
    await expect(page.locator('.recharts-tooltip')).toBeVisible();
    
    // Natural Language: "View user analytics"
    await page.click('text=User Analytics');
    await expect(page.locator('[data-testid="user-analytics-chart"]')).toBeVisible();
    
    // Natural Language: "Access AI insights and recommendations"
    await page.click('text=AI Insights');
    await expect(page.locator('[data-testid="ai-insights-panel"]')).toBeVisible();
    await expect(page.locator('text=AI-Powered Recommendations')).toBeVisible();
    
    // Natural Language: "View market insights and trends"
    await expect(page.locator('[data-testid="market-insights"]')).toBeVisible();
    await expect(page.locator('text=Market Trends')).toBeVisible();
    
    // Natural Language: "Export analytics report"
    await page.click('button[data-testid="export-report-button"]');
    await page.selectOption('select[name="report-format"]', 'pdf');
    await page.click('button[data-testid="download-report"]');
    
    // Natural Language: "Verify report download started"
    await expect(page.locator('text=Report download started')).toBeVisible();
  });
  
  test('User can view detailed property analytics', async ({ page }) => {
    // Natural Language: "Navigate to property-specific analytics"
    await page.click('text=Property Analytics');
    await expect(page.locator('text=Property Performance')).toBeVisible();
    
    // Natural Language: "Select a specific property for detailed view"
    await page.click('[data-testid="property-selector"]');
    await page.click('text=Luxury Villa in Mumbai');
    
    // Natural Language: "View property-specific metrics and charts"
    await expect(page.locator('[data-testid="property-views-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="property-inquiries-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="property-engagement-chart"]')).toBeVisible();
    
    // Natural Language: "View property comparison with similar properties"
    await page.click('text=Compare Properties');
    await expect(page.locator('[data-testid="property-comparison-chart"]')).toBeVisible();
    
    // Natural Language: "View social media performance for this property"
    await page.click('text=Social Media Performance');
    await expect(page.locator('[data-testid="social-performance-chart"]')).toBeVisible();
    await expect(page.locator('text=Facebook Performance')).toBeVisible();
    await expect(page.locator('text=Instagram Performance')).toBeVisible();
  });
});
