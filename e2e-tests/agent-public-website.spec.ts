import { test, expect } from '@playwright/test'

test.describe('Agent Public Website', () => {
  const testAgentSlug = 'john-doe-test'
  const testAgentName = 'John Doe Test'
  
  test.beforeEach(async ({ page }) => {
    // Mock the API responses for agent data
    await page.route('**/api/v1/agent-public/**', async (route) => {
      const url = route.request().url()
      
      if (url.includes('/agent-public/john-doe-test')) {
        if (url.includes('/properties')) {
          // Mock properties response
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              properties: [
                {
                  id: 'prop-1',
                  title: 'Beautiful 3BHK Apartment',
                  price: 5000000,
                  property_type: 'Apartment',
                  location: 'Mumbai, Maharashtra',
                  bedrooms: 3,
                  bathrooms: 2,
                  area: 1200,
                  images: ['https://example.com/prop1.jpg']
                },
                {
                  id: 'prop-2',
                  title: 'Luxury Villa with Garden',
                  price: 15000000,
                  property_type: 'Villa',
                  location: 'Bangalore, Karnataka',
                  bedrooms: 4,
                  bathrooms: 3,
                  area: 2500,
                  images: ['https://example.com/prop2.jpg']
                }
              ],
              total: 2,
              page: 1,
              limit: 12,
              total_pages: 1,
              agent_name: testAgentName
            })
          })
        } else {
          // Mock agent profile response
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 'agent-1',
              agent_name: testAgentName,
              slug: testAgentSlug,
              bio: 'Experienced real estate agent with 10+ years in the market.',
              photo: 'https://example.com/photo.jpg',
              phone: '+1234567890',
              email: 'john@example.com',
              office_address: '123 Main St, City, State',
              specialties: ['Residential', 'Commercial'],
              experience: '10+ years experience',
              languages: ['English', 'Spanish'],
              view_count: 150,
              contact_count: 25
            })
          })
        }
      } else {
        await route.continue()
      }
    })
  })

  test('should display agent profile page correctly', async ({ page }) => {
    await page.goto(`/agent/${testAgentSlug}`)
    
    // Check page title and header
    await expect(page.locator('h1')).toContainText(testAgentName)
    await expect(page.locator('text=PropertyAI')).toBeVisible()
    
    // Check agent information
    await expect(page.locator('text=Experienced real estate agent with 10+ years in the market.')).toBeVisible()
    await expect(page.locator('text=+1234567890')).toBeVisible()
    await expect(page.locator('text=john@example.com')).toBeVisible()
    await expect(page.locator('text=123 Main St, City, State')).toBeVisible()
    
    // Check specialties
    await expect(page.locator('text=Residential')).toBeVisible()
    await expect(page.locator('text=Commercial')).toBeVisible()
    
    // Check experience and languages
    await expect(page.locator('text=10+ years experience')).toBeVisible()
    await expect(page.locator('text=English, Spanish')).toBeVisible()
    
    // Check statistics
    await expect(page.locator('text=150 profile views')).toBeVisible()
    await expect(page.locator('text=25 inquiries')).toBeVisible()
  })

  test('should display featured properties section', async ({ page }) => {
    await page.goto(`/agent/${testAgentSlug}`)
    
    // Check featured properties section
    await expect(page.locator('text=Featured Properties')).toBeVisible()
    
    // Check property cards
    await expect(page.locator('text=Beautiful 3BHK Apartment')).toBeVisible()
    await expect(page.locator('text=Luxury Villa with Garden')).toBeVisible()
    
    // Check property details
    await expect(page.locator('text=Mumbai, Maharashtra')).toBeVisible()
    await expect(page.locator('text=Bangalore, Karnataka')).toBeVisible()
    await expect(page.locator('text=₹50L')).toBeVisible()
    await expect(page.locator('text=₹1.5Cr')).toBeVisible()
    
    // Check property features
    await expect(page.locator('text=3 bed')).toBeVisible()
    await expect(page.locator('text=2 bath')).toBeVisible()
    await expect(page.locator('text=1200 sq ft')).toBeVisible()
  })

  test('should have working navigation links', async ({ page }) => {
    await page.goto(`/agent/${testAgentSlug}`)
    
    // Check header navigation
    await expect(page.locator('a[href="/"]')).toBeVisible()
    await expect(page.locator(`a[href="/agent/${testAgentSlug}/properties"]`)).toBeVisible()
    await expect(page.locator(`a[href="/agent/${testAgentSlug}/contact"]`)).toBeVisible()
    
    // Check contact card links
    await expect(page.locator(`a[href="/agent/${testAgentSlug}/contact"]`).filter({ hasText: 'Send Message' })).toBeVisible()
    await expect(page.locator(`a[href="/agent/${testAgentSlug}/properties"]`).filter({ hasText: 'View Properties' })).toBeVisible()
    
    // Check "View All Properties" link
    await expect(page.locator(`a[href="/agent/${testAgentSlug}/properties"]`).filter({ hasText: 'View All Properties' })).toBeVisible()
  })

  test('should have working contact information links', async ({ page }) => {
    await page.goto(`/agent/${testAgentSlug}`)
    
    // Check phone link
    const phoneLink = page.locator('a[href="tel:+1234567890"]')
    await expect(phoneLink).toBeVisible()
    await expect(phoneLink).toContainText('+1234567890')
    
    // Check email link
    const emailLink = page.locator('a[href="mailto:john@example.com"]')
    await expect(emailLink).toBeVisible()
    await expect(emailLink).toContainText('john@example.com')
  })

  test('should handle agent not found error', async ({ page }) => {
    // Mock 404 response
    await page.route('**/api/v1/agent-public/nonexistent-agent', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Agent not found' })
      })
    })
    
    await page.goto('/agent/nonexistent-agent')
    
    // Check error page
    await expect(page.locator('text=Agent Not Found')).toBeVisible()
    await expect(page.locator('text=The agent profile you\'re looking for doesn\'t exist or is not public.')).toBeVisible()
    await expect(page.locator('a[href="/"]').filter({ hasText: 'Back to Home' })).toBeVisible()
  })

  test('should display loading state initially', async ({ page }) => {
    // Mock delayed response
    await page.route('**/api/v1/agent-public/**', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000))
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'agent-1',
          agent_name: testAgentName,
          slug: testAgentSlug,
          bio: 'Test bio',
          photo: null,
          phone: null,
          email: null,
          office_address: null,
          specialties: [],
          experience: null,
          languages: [],
          view_count: 0,
          contact_count: 0
        })
      })
    })
    
    await page.goto(`/agent/${testAgentSlug}`)
    
    // Check loading state
    await expect(page.locator('text=Loading agent profile...')).toBeVisible()
    
    // Wait for content to load
    await expect(page.locator('text=Loading agent profile...')).not.toBeVisible()
    await expect(page.locator('h1')).toContainText(testAgentName)
  })

  test('should handle missing agent photo gracefully', async ({ page }) => {
    // Mock response without photo
    await page.route('**/api/v1/agent-public/john-doe-test', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'agent-1',
          agent_name: testAgentName,
          slug: testAgentSlug,
          bio: 'Test bio',
          photo: null,
          phone: '+1234567890',
          email: 'john@example.com',
          office_address: '123 Main St',
          specialties: ['Residential'],
          experience: '5 years',
          languages: ['English'],
          view_count: 50,
          contact_count: 10
        })
      })
    })
    
    await page.goto(`/agent/${testAgentSlug}`)
    
    // Check that default user icon is shown instead of photo
    await expect(page.locator('svg')).toBeVisible() // User icon
    await expect(page.locator('img[src="https://example.com/photo.jpg"]')).not.toBeVisible()
  })

  test('should track contact button clicks', async ({ page }) => {
    let trackContactCalled = false
    
    // Mock track contact endpoint
    await page.route('**/api/v1/agent-public/john-doe-test/track-contact', async (route) => {
      trackContactCalled = true
      const request = route.request()
      const body = JSON.parse(request.postData() || '{}')
      
      expect(body.action).toBe('contact_button_click')
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'Action tracked successfully' })
      })
    })
    
    await page.goto(`/agent/${testAgentSlug}`)
    
    // Click contact button
    await page.click('text=Send Message')
    
    // Verify tracking was called
    expect(trackContactCalled).toBe(true)
  })

  test('should be mobile responsive', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    
    await page.goto(`/agent/${testAgentSlug}`)
    
    // Check that content is still visible and properly laid out
    await expect(page.locator('h1')).toContainText(testAgentName)
    await expect(page.locator('text=Featured Properties')).toBeVisible()
    
    // Check that navigation is accessible
    await expect(page.locator('text=Properties')).toBeVisible()
    await expect(page.locator('text=Contact')).toBeVisible()
    
    // Check that contact card is still visible
    await expect(page.locator('text=Contact Information')).toBeVisible()
    await expect(page.locator('text=Send Message')).toBeVisible()
  })

  test('should handle empty properties list', async ({ page }) => {
    // Mock response with no properties
    await page.route('**/api/v1/agent-public/john-doe-test/properties**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          properties: [],
          total: 0,
          page: 1,
          limit: 12,
          total_pages: 0,
          agent_name: testAgentName
        })
      })
    })
    
    await page.goto(`/agent/${testAgentSlug}`)
    
    // Check that agent profile is still displayed
    await expect(page.locator('h1')).toContainText(testAgentName)
    
    // Check that featured properties section is not shown
    await expect(page.locator('text=Featured Properties')).not.toBeVisible()
  })

  test('should handle network errors gracefully', async ({ page }) => {
    // Mock network error
    await page.route('**/api/v1/agent-public/**', async (route) => {
      await route.abort('failed')
    })
    
    await page.goto(`/agent/${testAgentSlug}`)
    
    // Check error page is displayed
    await expect(page.locator('text=Agent Not Found')).toBeVisible()
    await expect(page.locator('a[href="/"]').filter({ hasText: 'Back to Home' })).toBeVisible()
  })
})