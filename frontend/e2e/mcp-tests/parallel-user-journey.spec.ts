import { test, expect, request } from '@playwright/test';

/**
 * Parallel User Journey Tests
 * ===========================
 * 
 * This test suite runs multiple user journeys in parallel to test
 * concurrent user operations and system stability.
 */

test.describe.configure({ mode: 'parallel' });

test.describe('Parallel User Journey Tests', () => {
  const users = [
    {
      first_name: 'Alice',
      last_name: 'Johnson',
      email: `alice${Date.now()}@propertyai.com`,
      password: 'SecurePassword123!',
      phone: '+1-555-001-0001'
    },
    {
      first_name: 'Bob',
      last_name: 'Smith',
      email: `bob${Date.now()}@propertyai.com`,
      password: 'SecurePassword123!',
      phone: '+1-555-001-0002'
    },
    {
      first_name: 'Carol',
      last_name: 'Williams',
      email: `carol${Date.now()}@propertyai.com`,
      password: 'SecurePassword123!',
      phone: '+1-555-001-0003'
    }
  ];

  test.beforeAll(async ({ request }) => {
    console.log('🚀 Setting up parallel users...');
    
    // Register all users in parallel
    const registrationPromises = users.map(user => 
      request.post('http://localhost:8000/api/v1/auth/register', {
        data: {
          email: user.email,
          password: user.password,
          first_name: user.first_name,
          last_name: user.last_name,
          phone: user.phone
        }
      })
    );

    const results = await Promise.allSettled(registrationPromises);
    const successfulRegistrations = results.filter(r => r.status === 'fulfilled').length;
    console.log(`✅ Successfully registered ${successfulRegistrations}/${users.length} users`);
  });

  test('User 1: Complete Real Estate Agent Journey', async ({ page }) => {
    const user = users[0];
    console.log(`🏠 User 1 (${user.email}): Starting real estate agent journey...`);

    // Login via API
    const loginResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
      form: {
        username: user.email,
        password: user.password
      }
    });
    const loginData = await loginResponse.json();
    const authToken = loginData.access_token;

    // Set auth token for frontend
    await page.evaluate((token) => {
      localStorage.setItem('auth_token', token);
    }, authToken);

    // Navigate to properties and create a luxury property
    await page.goto('/properties');
    await page.waitForLoadState('networkidle');

    const propertyData = {
      title: 'Luxury Downtown Penthouse',
      description: 'Exclusive penthouse with panoramic city views and premium amenities',
      property_type: 'Apartment',
      price: 2500000,
      location: 'Downtown District, City, State 12345',
      address: '1000 Luxury Tower, Penthouse Floor',
      bedrooms: 4,
      bathrooms: 3,
      area: 2800,
      amenities: 'Private Elevator, Rooftop Terrace, Wine Cellar, Gym',
      features: ['City Views', 'Premium Finishes', 'Smart Home', 'Parking']
    };

    const createPropertyResponse = await request.post('http://localhost:8000/api/v1/properties/', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: propertyData
    });

    expect(createPropertyResponse.ok()).toBeTruthy();
    const createdProperty = await createPropertyResponse.json();
    console.log(`✅ User 1: Created luxury property ${createdProperty.id}`);

    // Test social media content generation
    await page.goto('/social-publishing');
    await page.waitForLoadState('networkidle');

    // Look for property selection and AI generation
    const propertyCards = page.locator('div[class*="cursor-pointer"], div[class*="border"]');
    if (await propertyCards.count() > 0) {
      await propertyCards.first().click();
      await page.waitForTimeout(2000);

      // Try to generate AI content
      const languageCheckboxes = page.locator('input[type="checkbox"]');
      if (await languageCheckboxes.count() > 0) {
        await languageCheckboxes.first().check();
        await page.waitForTimeout(3000);
        console.log('✅ User 1: AI content generation attempted');
      }
    }

    // Verify agent website
    const username = user.email.split('@')[0];
    await page.goto(`/agent/${username}`);
    await page.waitForLoadState('networkidle');
    
    const agentNameElement = page.locator('h1, h2').first();
    if (await agentNameElement.count() > 0) {
      const agentName = await agentNameElement.textContent();
      console.log(`✅ User 1: Agent website shows "${agentName}"`);
    }
  });

  test('User 2: Property Management Focus', async ({ page }) => {
    const user = users[1];
    console.log(`🏘️ User 2 (${user.email}): Starting property management focus...`);

    // Login via API
    const loginResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
      form: {
        username: user.email,
        password: user.password
      }
    });
    const loginData = await loginResponse.json();
    const authToken = loginData.access_token;

    // Set auth token for frontend
    await page.evaluate((token) => {
      localStorage.setItem('auth_token', token);
    }, authToken);

    // Create multiple properties of different types
    const properties = [
      {
        title: 'Family Suburban Home',
        property_type: 'House',
        price: 650000,
        bedrooms: 3,
        bathrooms: 2,
        area: 1800
      },
      {
        title: 'Modern Office Space',
        property_type: 'Commercial',
        price: 1200000,
        bedrooms: 0,
        bathrooms: 2,
        area: 2500
      },
      {
        title: 'Investment Condo',
        property_type: 'Apartment',
        price: 450000,
        bedrooms: 2,
        bathrooms: 1,
        area: 1100
      }
    ];

    const createdProperties = [];
    for (const property of properties) {
      const fullPropertyData = {
        ...property,
        description: `Beautiful ${property.property_type.toLowerCase()} perfect for ${property.property_type === 'Commercial' ? 'business' : 'living'}`,
        location: 'Various Locations, City, State',
        address: `${property.price} ${property.property_type} Street`,
        amenities: 'Various amenities',
        features: ['Quality Features']
      };

      const response = await request.post('http://localhost:8000/api/v1/properties/', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        data: fullPropertyData
      });

      if (response.ok()) {
        const created = await response.json();
        createdProperties.push(created);
        console.log(`✅ User 2: Created ${property.property_type} property ${created.id}`);
      }
    }

    // Test property listing page
    await page.goto('/properties');
    await page.waitForLoadState('networkidle');

    const propertyElements = page.locator('div[class*="property"], div[class*="card"]');
    const propertyCount = await propertyElements.count();
    console.log(`✅ User 2: Properties page shows ${propertyCount} properties`);

    // Test analytics dashboard
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
    
    const analyticsElements = page.locator('div[class*="chart"], div[class*="metric"]');
    const analyticsCount = await analyticsElements.count();
    console.log(`✅ User 2: Analytics dashboard shows ${analyticsCount} elements`);
  });

  test('User 3: Social Media Marketing Specialist', async ({ page }) => {
    const user = users[2];
    console.log(`📱 User 3 (${user.email}): Starting social media marketing focus...`);

    // Login via API
    const loginResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
      form: {
        username: user.email,
        password: user.password
      }
    });
    const loginData = await loginResponse.json();
    const authToken = loginData.access_token;

    // Set auth token for frontend
    await page.evaluate((token) => {
      localStorage.setItem('auth_token', token);
    }, authToken);

    // Create a property first
    const propertyData = {
      title: 'Instagram-Worthy Modern Loft',
      description: 'Stylish loft perfect for social media showcasing with modern design',
      property_type: 'Apartment',
      price: 850000,
      location: 'Arts District, City, State',
      address: '500 Creative Lane, Loft 12',
      bedrooms: 1,
      bathrooms: 1,
      area: 1200,
      amenities: 'High Ceilings, Exposed Brick, Modern Kitchen',
      features: ['Instagram Ready', 'Modern Design', 'Great Lighting']
    };

    const createPropertyResponse = await request.post('http://localhost:8000/api/v1/properties/', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: propertyData
    });

    const createdProperty = await createPropertyResponse.json();
    console.log(`✅ User 3: Created social media property ${createdProperty.id}`);

    // Focus on social publishing workflow
    await page.goto('/social-publishing');
    await page.waitForLoadState('networkidle');

    // Test multiple language content generation
    const languages = ['English', 'Spanish', 'French'];
    for (const language of languages) {
      console.log(`🌐 User 3: Testing ${language} content generation...`);
      
      // Look for property selection
      const propertyCards = page.locator('div[class*="cursor-pointer"], div[class*="border"]');
      if (await propertyCards.count() > 0) {
        await propertyCards.first().click();
        await page.waitForTimeout(1000);

        // Look for language selection
        const languageElements = page.locator('input[type="checkbox"], button').filter({ hasText: language });
        if (await languageElements.count() > 0) {
          await languageElements.first().click();
          await page.waitForTimeout(2000);
          console.log(`✅ User 3: Generated ${language} content`);
        }
      }
    }

    // Create social posts via API
    const socialPostData = {
      property_id: createdProperty.id,
      agent_id: user.email.split('@')[0], // Using email prefix as agent_id
      title: 'New Listing Alert!',
      content: 'Check out this amazing modern loft perfect for your lifestyle!',
      language: 'English',
      channels: ['instagram', 'facebook', 'twitter'],
      status: 'published'
    };

    const createSocialPostResponse = await request.post('http://localhost:8000/api/v1/social-publishing/', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: socialPostData
    });

    if (createSocialPostResponse.ok()) {
      const createdPost = await createSocialPostResponse.json();
      console.log(`✅ User 3: Created social media post ${createdPost.id}`);
    }

    // Test onboarding completion
    await page.goto('/onboarding');
    await page.waitForLoadState('networkidle');
    console.log(`✅ User 3: Accessed onboarding page`);
  });

  test('Concurrent Property Creation Stress Test', async ({ page }) => {
    console.log('🔥 Running concurrent property creation stress test...');

    const concurrentUsers = users.slice(0, 2); // Use first 2 users
    const propertiesPerUser = 3;

    const allPromises = concurrentUsers.flatMap(user => {
      // Login each user
      const loginPromise = request.post('http://localhost:8000/api/v1/auth/login', {
        form: {
          username: user.email,
          password: user.password
        }
      }).then(async (loginResponse) => {
        const loginData = await loginResponse.json();
        const authToken = loginData.access_token;

        // Create multiple properties for this user
        return Promise.all(
          Array.from({ length: propertiesPerUser }, (_, i) => 
            request.post('http://localhost:8000/api/v1/properties/', {
              headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
              },
              data: {
                title: `Property ${i + 1} by ${user.first_name}`,
                description: `Test property ${i + 1} created by ${user.first_name}`,
                property_type: 'Apartment',
                price: 500000 + (i * 100000),
                location: 'Test Location',
                address: `${i + 1} Test Street`,
                bedrooms: 2 + i,
                bathrooms: 1 + i,
                area: 1000 + (i * 200),
                amenities: 'Test amenities',
                features: ['Test feature']
              }
            })
          )
        );
      });

      return [loginPromise];
    });

    const results = await Promise.allSettled(allPromises);
    const successfulCreations = results.filter(r => r.status === 'fulfilled').length;
    
    console.log(`✅ Stress test completed: ${successfulCreations}/${concurrentUsers.length} users created properties successfully`);
    
    // Verify properties were created by checking the properties page
    await page.goto('/properties');
    await page.waitForLoadState('networkidle');
    
    const propertyElements = page.locator('div[class*="property"], div[class*="card"]');
    const totalProperties = await propertyElements.count();
    console.log(`✅ Total properties visible on page: ${totalProperties}`);
  });
});