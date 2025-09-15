import { test, expect } from '@playwright/test';

test.describe('Analytics Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication and navigate to dashboard
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('authState', JSON.stringify({
        isAuthenticated: true,
        user: { id: 'test-user-id', email: 'test@example.com' }
      }));
    });

    // Mock analytics data
    await page.route('**/api/v1/dashboard/stats', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            total_properties: 25,
            active_listings: 18,
            total_leads: 150,
            total_users: 5,
            total_views: 2500,
            monthly_leads: 45,
            revenue: '₹2,500,000',
            properties: [
              {
                id: 'property-1',
                title: 'Beautiful 3BR Apartment',
                views: 150,
                inquiries: 12,
                shares: 8,
                status: 'active'
              },
              {
                id: 'property-2',
                title: 'Luxury Penthouse',
                views: 200,
                inquiries: 18,
                shares: 15,
                status: 'active'
              }
            ]
          }
        })
      });
    });
  });

  test('should display analytics dashboard', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if analytics dashboard is visible
    await expect(page.locator('text=Analytics Dashboard')).toBeVisible();
    await expect(page.locator('[data-testid="analytics-dashboard"]')).toBeVisible();
  });

  test('should display key metrics cards', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if metric cards are visible
    await expect(page.locator('[data-testid="metric-card"]')).toHaveCount(7);
    await expect(page.locator('text=Total Properties')).toBeVisible();
    await expect(page.locator('text=25')).toBeVisible();
    await expect(page.locator('text=Active Listings')).toBeVisible();
    await expect(page.locator('text=18')).toBeVisible();
    await expect(page.locator('text=Total Leads')).toBeVisible();
    await expect(page.locator('text=150')).toBeVisible();
    await expect(page.locator('text=Total Users')).toBeVisible();
    await expect(page.locator('text=5')).toBeVisible();
    await expect(page.locator('text=Total Views')).toBeVisible();
    await expect(page.locator('text=2,500')).toBeVisible();
    await expect(page.locator('text=Monthly Leads')).toBeVisible();
    await expect(page.locator('text=45')).toBeVisible();
    await expect(page.locator('text=Revenue')).toBeVisible();
    await expect(page.locator('text=₹2,500,000')).toBeVisible();
  });

  test('should display performance charts', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if charts are visible
    await expect(page.locator('[data-testid="views-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="leads-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="revenue-chart"]')).toBeVisible();
  });

  test('should display property performance table', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if property performance table is visible
    await expect(page.locator('[data-testid="property-performance-table"]')).toBeVisible();
    await expect(page.locator('text=Property Performance')).toBeVisible();
    await expect(page.locator('text=Beautiful 3BR Apartment')).toBeVisible();
    await expect(page.locator('text=Luxury Penthouse')).toBeVisible();
  });

  test('should display property metrics', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if property metrics are visible
    await expect(page.locator('text=Views')).toBeVisible();
    await expect(page.locator('text=Inquiries')).toBeVisible();
    await expect(page.locator('text=Shares')).toBeVisible();
    await expect(page.locator('text=150')).toBeVisible();
    await expect(page.locator('text=12')).toBeVisible();
    await expect(page.locator('text=8')).toBeVisible();
  });

  test('should filter analytics by date range', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if date range filter is visible
    await expect(page.locator('[data-testid="date-range-filter"]')).toBeVisible();
    
    // Select different date range
    await page.selectOption('select[name="dateRange"]', 'last_month');
    
    // Should update analytics data
    await expect(page.locator('[data-testid="analytics-dashboard"]')).toBeVisible();
  });

  test('should filter analytics by property type', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if property type filter is visible
    await expect(page.locator('[data-testid="property-type-filter"]')).toBeVisible();
    
    // Select property type
    await page.selectOption('select[name="propertyType"]', 'apartment');
    
    // Should update analytics data
    await expect(page.locator('[data-testid="analytics-dashboard"]')).toBeVisible();
  });

  test('should display lead conversion metrics', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if lead conversion metrics are visible
    await expect(page.locator('text=Lead Conversion')).toBeVisible();
    await expect(page.locator('text=Conversion Rate')).toBeVisible();
    await expect(page.locator('text=Average Response Time')).toBeVisible();
    await expect(page.locator('text=Lead Quality Score')).toBeVisible();
  });

  test('should display social media performance', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if social media performance is visible
    await expect(page.locator('text=Social Media Performance')).toBeVisible();
    await expect(page.locator('text=Facebook')).toBeVisible();
    await expect(page.locator('text=Instagram')).toBeVisible();
    await expect(page.locator('text=LinkedIn')).toBeVisible();
    await expect(page.locator('text=Twitter')).toBeVisible();
  });

  test('should display engagement metrics', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if engagement metrics are visible
    await expect(page.locator('text=Engagement Metrics')).toBeVisible();
    await expect(page.locator('text=Likes')).toBeVisible();
    await expect(page.locator('text=Comments')).toBeVisible();
    await expect(page.locator('text=Shares')).toBeVisible();
    await expect(page.locator('text=Click-through Rate')).toBeVisible();
  });

  test('should export analytics data', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Click export button
    await page.click('button[data-testid="export-analytics"]');
    
    // Should show export options
    await expect(page.locator('[data-testid="export-options"]')).toBeVisible();
    await expect(page.locator('text=Export as CSV')).toBeVisible();
    await expect(page.locator('text=Export as PDF')).toBeVisible();
    await expect(page.locator('text=Export as Excel')).toBeVisible();
  });

  test('should display real-time updates', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if real-time indicator is visible
    await expect(page.locator('[data-testid="real-time-indicator"]')).toBeVisible();
    await expect(page.locator('text=Live Data')).toBeVisible();
  });

  test('should handle analytics loading state', async ({ page }) => {
    // Mock slow API response
    await page.route('**/api/v1/dashboard/stats', route => {
      setTimeout(() => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            data: {
              total_properties: 25,
              active_listings: 18,
              total_leads: 150,
              total_users: 5,
              total_views: 2500,
              monthly_leads: 45,
              revenue: '₹2,500,000'
            }
          })
        });
      }, 2000);
    });
    
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Should show loading state
    await expect(page.locator('text=Loading analytics...')).toBeVisible();
    
    // Wait for data to load
    await page.waitForSelector('[data-testid="analytics-dashboard"]', { timeout: 10000 });
    
    // Should show analytics data
    await expect(page.locator('text=Total Properties')).toBeVisible();
  });

  test('should handle analytics error', async ({ page }) => {
    // Mock API error
    await page.route('**/api/v1/dashboard/stats', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Analytics service unavailable' })
      });
    });
    
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Should show error message
    await expect(page.locator('text=Failed to load analytics data')).toBeVisible();
    await expect(page.locator('button[data-testid="retry-analytics"]')).toBeVisible();
  });

  test('should retry analytics on error', async ({ page }) => {
    // Mock API error first, then success
    let retryCount = 0;
    await page.route('**/api/v1/dashboard/stats', route => {
      if (retryCount === 0) {
        retryCount++;
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Analytics service unavailable' })
        });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            data: {
              total_properties: 25,
              active_listings: 18,
              total_leads: 150,
              total_users: 5,
              total_views: 2500,
              monthly_leads: 45,
              revenue: '₹2,500,000'
            }
          })
        });
      }
    });
    
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Should show error message
    await expect(page.locator('text=Failed to load analytics data')).toBeVisible();
    
    // Click retry button
    await page.click('button[data-testid="retry-analytics"]');
    
    // Should load analytics data
    await expect(page.locator('text=Total Properties')).toBeVisible();
  });

  test('should display property comparison', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if property comparison is visible
    await expect(page.locator('text=Property Comparison')).toBeVisible();
    
    // Select properties to compare
    await page.check('input[name="compare-property"][value="property-1"]');
    await page.check('input[name="compare-property"][value="property-2"]');
    
    // Click compare button
    await page.click('button[data-testid="compare-properties"]');
    
    // Should show comparison chart
    await expect(page.locator('[data-testid="property-comparison-chart"]')).toBeVisible();
  });

  test('should display trend analysis', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if trend analysis is visible
    await expect(page.locator('text=Trend Analysis')).toBeVisible();
    await expect(page.locator('text=Views Trend')).toBeVisible();
    await expect(page.locator('text=Leads Trend')).toBeVisible();
    await expect(page.locator('text=Revenue Trend')).toBeVisible();
  });

  test('should display geographic analytics', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if geographic analytics is visible
    await expect(page.locator('text=Geographic Analytics')).toBeVisible();
    await expect(page.locator('[data-testid="geographic-map"]')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if analytics is still usable on mobile
    await expect(page.locator('[data-testid="analytics-dashboard"]')).toBeVisible();
    await expect(page.locator('[data-testid="metric-card"]')).toBeVisible();
  });

  test('should display performance insights', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Check if performance insights are visible
    await expect(page.locator('text=Performance Insights')).toBeVisible();
    await expect(page.locator('text=Top Performing Properties')).toBeVisible();
    await expect(page.locator('text=Areas for Improvement')).toBeVisible();
    await expect(page.locator('text=Recommendations')).toBeVisible();
  });

  test('should display custom date range picker', async ({ page }) => {
    // Navigate to analytics
    await page.click('text=Analytics');
    
    // Click custom date range
    await page.click('button[data-testid="custom-date-range"]');
    
    // Should show date picker
    await expect(page.locator('[data-testid="date-picker"]')).toBeVisible();
    
    // Select custom dates
    await page.fill('input[name="startDate"]', '2024-01-01');
    await page.fill('input[name="endDate"]', '2024-12-31');
    
    // Apply custom range
    await page.click('button[data-testid="apply-date-range"]');
    
    // Should update analytics data
    await expect(page.locator('[data-testid="analytics-dashboard"]')).toBeVisible();
  });
});