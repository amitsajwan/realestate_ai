import { test, expect } from '@playwright/test';

test.describe('Agent Website System', () => {
  test.beforeEach(async ({ page }) => {
    // Mock agent data
    await page.route('**/api/v1/agent/public/agent-public/*', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'agent-1',
          agent_name: 'John Doe',
          slug: 'john-doe',
          bio: 'Professional real estate agent with 10+ years of experience',
          photo: 'https://example.com/photo.jpg',
          phone: '+1234567890',
          email: 'john.doe@example.com',
          office_address: '123 Main St, New York, NY 10001',
          specialties: ['Residential', 'Commercial', 'Luxury'],
          experience: '10+ years in real estate',
          languages: ['English', 'Spanish'],
          view_count: 150,
          contact_count: 25,
          is_active: true,
          is_public: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z'
        })
      });
    });

    await page.route('**/api/v1/agent/public/agent-public/*/properties*', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          properties: [
            {
              id: 'property-1',
              title: 'Beautiful 3BR Apartment',
              price: 500000,
              property_type: 'apartment',
              location: 'New York, NY',
              bedrooms: 3,
              bathrooms: 2,
              area: 1200,
              images: ['https://example.com/property1.jpg']
            },
            {
              id: 'property-2',
              title: 'Luxury Penthouse',
              price: 1200000,
              property_type: 'penthouse',
              location: 'Manhattan, NY',
              bedrooms: 4,
              bathrooms: 3,
              area: 2000,
              images: ['https://example.com/property2.jpg']
            }
          ]
        })
      });
    });
  });

  test('should display agent public profile', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Check if agent profile is visible
    await expect(page.locator('h1')).toContainText('John Doe');
    await expect(page.locator('text=Professional real estate agent with 10+ years of experience')).toBeVisible();
    await expect(page.locator('text=+1234567890')).toBeVisible();
    await expect(page.locator('text=john.doe@example.com')).toBeVisible();
  });

  test('should display agent photo and status', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Check if agent photo is visible
    await expect(page.locator('[data-testid="agent-photo"]')).toBeVisible();
    
    // Check if online status indicator is visible
    await expect(page.locator('[data-testid="online-status"]')).toBeVisible();
  });

  test('should display agent stats', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Check if stats are visible
    await expect(page.locator('text=150 Views')).toBeVisible();
    await expect(page.locator('text=25 Clients')).toBeVisible();
    await expect(page.locator('text=5.0 Rating')).toBeVisible();
  });

  test('should display agent specialties', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Check if specialties are visible
    await expect(page.locator('text=Specialties')).toBeVisible();
    await expect(page.locator('text=Residential')).toBeVisible();
    await expect(page.locator('text=Commercial')).toBeVisible();
    await expect(page.locator('text=Luxury')).toBeVisible();
  });

  test('should display agent experience and languages', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Check if experience is visible
    await expect(page.locator('text=Experience')).toBeVisible();
    await expect(page.locator('text=10+ years in real estate')).toBeVisible();
    
    // Check if languages are visible
    await expect(page.locator('text=Languages')).toBeVisible();
    await expect(page.locator('text=English')).toBeVisible();
    await expect(page.locator('text=Spanish')).toBeVisible();
  });

  test('should display contact information', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Check if contact information is visible
    await expect(page.locator('text=Get In Touch')).toBeVisible();
    await expect(page.locator('text=+1234567890')).toBeVisible();
    await expect(page.locator('text=john.doe@example.com')).toBeVisible();
    await expect(page.locator('text=123 Main St, New York, NY 10001')).toBeVisible();
  });

  test('should display featured properties', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Check if properties section is visible
    await expect(page.locator('text=Featured Properties')).toBeVisible();
    
    // Check if properties are displayed
    await expect(page.locator('[data-testid="property-card"]')).toHaveCount(2);
    await expect(page.locator('text=Beautiful 3BR Apartment')).toBeVisible();
    await expect(page.locator('text=Luxury Penthouse')).toBeVisible();
  });

  test('should display property details', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Check if property details are visible
    await expect(page.locator('text=₹500,000')).toBeVisible();
    await expect(page.locator('text=3 bed')).toBeVisible();
    await expect(page.locator('text=2 bath')).toBeVisible();
    await expect(page.locator('text=1200 sq ft')).toBeVisible();
  });

  test('should display client testimonials', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Check if testimonials section is visible
    await expect(page.locator('text=What Clients Say')).toBeVisible();
    
    // Check if testimonials are displayed
    await expect(page.locator('[data-testid="testimonial"]')).toHaveCount(3);
    await expect(page.locator('text=Sarah Johnson')).toBeVisible();
    await expect(page.locator('text=Michael Rodriguez')).toBeVisible();
    await expect(page.locator('text=Anna Chen')).toBeVisible();
  });

  test('should display social proof stats', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Check if social proof stats are visible
    await expect(page.locator('text=50+')).toBeVisible();
    await expect(page.locator('text=Happy Clients')).toBeVisible();
    await expect(page.locator('text=₹2.5Cr+')).toBeVisible();
    await expect(page.locator('text=Properties Sold')).toBeVisible();
    await expect(page.locator('text=15')).toBeVisible();
    await expect(page.locator('text=Years Experience')).toBeVisible();
  });

  test('should handle contact button click', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Click contact button
    await page.click('button[data-testid="contact-button"]');
    
    // Should track contact click
    await expect(page.locator('text=Get In Touch')).toBeVisible();
  });

  test('should navigate to properties page', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Click view all properties button
    await page.click('text=View All Properties');
    
    // Should navigate to properties page
    await expect(page).toHaveURL('/agent/john-doe/properties');
  });

  test('should navigate to contact page', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Click contact button
    await page.click('text=Send Message');
    
    // Should navigate to contact page
    await expect(page).toHaveURL('/agent/john-doe/contact');
  });

  test('should display recent activity', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Check if recent activity section is visible
    await expect(page.locator('text=Recent Activity')).toBeVisible();
    await expect(page.locator('text=Property sold in Bandra West')).toBeVisible();
    await expect(page.locator('text=New listing added')).toBeVisible();
    await expect(page.locator('text=Received 5-star review')).toBeVisible();
  });

  test('should display social media links', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Check if social media section is visible
    await expect(page.locator('text=Follow Us')).toBeVisible();
    await expect(page.locator('text=Twitter')).toBeVisible();
    await expect(page.locator('text=LinkedIn')).toBeVisible();
    await expect(page.locator('text=Instagram')).toBeVisible();
  });

  test('should handle agent not found', async ({ page }) => {
    // Mock agent not found
    await page.route('**/api/v1/agent/public/agent-public/invalid-agent', route => {
      route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Agent not found' })
      });
    });
    
    // Navigate to invalid agent page
    await page.goto('/agent/invalid-agent');
    
    // Should show not found message
    await expect(page.locator('text=Agent Not Found')).toBeVisible();
    await expect(page.locator('text=The agent profile you\'re looking for doesn\'t exist or is not public.')).toBeVisible();
    await expect(page.locator('text=Back to Home')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Check if agent profile is still usable on mobile
    await expect(page.locator('h1')).toContainText('John Doe');
    await expect(page.locator('[data-testid="agent-photo"]')).toBeVisible();
    await expect(page.locator('text=Get In Touch')).toBeVisible();
  });

  test('should display navigation menu on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Click mobile menu button
    await page.click('[data-testid="mobile-menu-button"]');
    
    // Check if mobile menu is visible
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
    await expect(page.locator('text=Properties')).toBeVisible();
    await expect(page.locator('text=Contact')).toBeVisible();
  });

  test('should handle property image loading', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Check if property images are visible
    await expect(page.locator('[data-testid="property-image"]')).toBeVisible();
    
    // Check if image has proper alt text
    await expect(page.locator('[data-testid="property-image"]')).toHaveAttribute('alt', 'Beautiful 3BR Apartment');
  });

  test('should display property type badges', async ({ page }) => {
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Check if property type badges are visible
    await expect(page.locator('text=apartment')).toBeVisible();
    await expect(page.locator('text=penthouse')).toBeVisible();
  });

  test('should handle slow loading', async ({ page }) => {
    // Mock slow API response
    await page.route('**/api/v1/agent/public/agent-public/*', route => {
      setTimeout(() => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'agent-1',
            agent_name: 'John Doe',
            slug: 'john-doe',
            bio: 'Professional real estate agent with 10+ years of experience',
            photo: 'https://example.com/photo.jpg',
            phone: '+1234567890',
            email: 'john.doe@example.com',
            office_address: '123 Main St, New York, NY 10001',
            specialties: ['Residential', 'Commercial', 'Luxury'],
            experience: '10+ years in real estate',
            languages: ['English', 'Spanish'],
            view_count: 150,
            contact_count: 25,
            is_active: true,
            is_public: true,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z'
          })
        });
      }, 2000);
    });
    
    // Navigate to agent public page
    await page.goto('/agent/john-doe');
    
    // Should show loading state
    await expect(page.locator('text=Loading agent profile...')).toBeVisible();
    
    // Wait for content to load
    await page.waitForSelector('h1', { timeout: 10000 });
    
    // Should show agent name
    await expect(page.locator('h1')).toContainText('John Doe');
  });
});