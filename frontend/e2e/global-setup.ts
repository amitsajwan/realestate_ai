import { chromium, FullConfig } from '@playwright/test'

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting E2E Test Setup...')
  
  // Launch browser for setup tasks
  const browser = await chromium.launch()
  const page = await browser.newPage()
  
  try {
    // Wait for the application to be ready
    console.log('⏳ Waiting for application to start...')
    await page.goto('http://localhost:3000')
    
    // Wait for the main content to load
    await page.waitForSelector('[data-testid="main-content"]', { timeout: 30000 })
    
    // Check if the application is responsive
    const isReady = await page.evaluate(() => {
      return document.readyState === 'complete'
    })
    
    if (!isReady) {
      throw new Error('Application failed to load properly')
    }
    
    console.log('✅ Application is ready for testing')
    
    // Set up test data if needed
    await setupTestData(page)
    
  } catch (error) {
    console.error('❌ Setup failed:', error)
    throw error
  } finally {
    await browser.close()
  }
}

async function setupTestData(page: any) {
  console.log('📊 Setting up test data...')
  
  try {
    // Mock API responses for consistent testing
    await page.route('**/api/**', async (route: any) => {
      const url = route.request().url()
      
      if (url.includes('/crm/leads')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            leads: [
              {
                id: '1',
                name: 'John Doe',
                email: 'john@example.com',
                phone: '+1234567890',
                status: 'new',
                urgency: 'high',
                score: 85,
                created_at: '2024-01-01T00:00:00Z',
                updated_at: '2024-01-01T00:00:00Z',
              },
              {
                id: '2',
                name: 'Jane Smith',
                email: 'jane@example.com',
                phone: '+1234567891',
                status: 'qualified',
                urgency: 'medium',
                score: 92,
                created_at: '2024-01-02T00:00:00Z',
                updated_at: '2024-01-02T00:00:00Z',
              },
            ],
            total: 2,
            page: 1,
            per_page: 20,
            total_pages: 1,
            filters_applied: {},
          }),
        })
      } else if (url.includes('/crm/analytics')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            overview_metrics: [
              {
                name: 'Total Properties',
                value: 10,
                type: 'count',
                change_percentage: 12,
                change_direction: 'up',
              },
              {
                name: 'Total Value',
                value: 5000000,
                type: 'sum',
                unit: 'USD',
                change_percentage: 8.2,
                change_direction: 'up',
              },
            ],
            property_analytics: {
              total_properties: 10,
              published_properties: 8,
              draft_properties: 2,
              archived_properties: 0,
              average_price: 500000,
              total_value: 5000000,
              conversion_rate: 0.15,
            },
            lead_analytics: {
              total_leads: 50,
              new_leads: 15,
              contacted_leads: 20,
              qualified_leads: 10,
              converted_leads: 5,
              lost_leads: 0,
              conversion_rate: 0.1,
              average_deal_value: 750000,
              total_pipeline_value: 3750000,
            },
            generated_at: '2024-01-01T00:00:00Z',
            period: 'this_month',
            date_range: {
              start: '2024-01-01T00:00:00Z',
              end: '2024-01-31T23:59:59Z',
            },
          }),
        })
      } else if (url.includes('/crm/teams')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'team-1',
              name: 'Sales Team',
              description: 'Main sales team',
              owner_id: 'user-1',
              members: [
                {
                  user_id: 'user-1',
                  email: 'admin@example.com',
                  role: 'admin',
                  joined_at: '2024-01-01T00:00:00Z',
                  is_active: true,
                  permissions: {},
                },
                {
                  user_id: 'user-2',
                  email: 'agent@example.com',
                  role: 'agent',
                  joined_at: '2024-01-02T00:00:00Z',
                  is_active: true,
                  permissions: {},
                },
              ],
              created_at: '2024-01-01T00:00:00Z',
              updated_at: '2024-01-01T00:00:00Z',
              member_count: 2,
            },
          ]),
        })
      } else {
        // Default response for other API calls
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({}),
        })
      }
    })
    
    console.log('✅ Test data setup complete')
  } catch (error) {
    console.error('❌ Test data setup failed:', error)
    throw error
  }
}

export default globalSetup