import { test, expect } from '@playwright/test';

test.describe('Agent Profile Creation Test', () => {
  let testUser: { email: string; password: string; first_name: string; last_name: string; phone: string };
  let authToken: string;
  let userId: string;

  test.beforeAll(async ({ request }) => {
    // Create a user via API for a clean test
    const timestamp = Date.now();
    testUser = {
      first_name: 'John',
      last_name: 'Doe',
      email: `profiletest${timestamp}@propertyai.com`,
      password: 'SecurePassword123!',
      phone: '+1-555-123-4567'
    };

    // Register user
    await request.post('http://localhost:8000/api/v1/auth/register', {
      data: {
        email: testUser.email,
        password: testUser.password,
        first_name: testUser.first_name,
        last_name: testUser.last_name,
        phone: testUser.phone
      }
    });

    // Login to get token
    const loginResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
      form: {
        username: testUser.email,
        password: testUser.password
      }
    });
    const loginData = await loginResponse.json();
    authToken = loginData.access_token;
    
    // Get user info to get user ID
    const userResponse = await request.get('http://localhost:8000/api/v1/auth/me', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    const userData = await userResponse.json();
    userId = userData.id;
  });

  test('Test agent profile creation during onboarding completion', async ({ page }) => {
    console.log('🚀 Starting Agent Profile Creation Test...');
    console.log(`📧 Test User: ${testUser.email}`);
    console.log(`🆔 User ID: ${userId}`);

    // First, let's test the agent public profile API directly
    console.log('\n🔧 ===========================================');
    console.log('🔧 PHASE 1: TEST AGENT PUBLIC PROFILE API');
    console.log('🔧 ===========================================');

    // Try to get agent profile before onboarding completion
    const username = testUser.email.split('@')[0];
    console.log(`🔍 Checking agent profile before onboarding: /agent/${username}`);
    
    const agentResponseBefore = await page.request.get(`http://localhost:8000/api/v1/agent/public/${username}`);
    console.log(`📊 Agent profile before onboarding: ${agentResponseBefore.status()}`);
    
    if (agentResponseBefore.status() === 404) {
      console.log('✅ Agent profile correctly not found before onboarding');
    } else {
      console.log('⚠️ Agent profile found before onboarding (unexpected)');
    }

    // Complete onboarding via API
    console.log('\n🎯 ===========================================');
    console.log('🎯 PHASE 2: COMPLETE ONBOARDING');
    console.log('🎯 ===========================================');
    
    const onboardingResponse = await page.request.post(`http://localhost:8000/api/v1/onboarding/${userId}/complete`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    console.log(`📊 Onboarding completion status: ${onboardingResponse.status()}`);
    
    if (onboardingResponse.ok()) {
      const onboardingResult = await onboardingResponse.json();
      console.log('✅ Onboarding completed successfully');
      console.log(`📝 Onboarding result: ${JSON.stringify(onboardingResult)}`);
    } else {
      const errorText = await onboardingResponse.text();
      console.log(`❌ Onboarding failed: ${errorText}`);
      throw new Error('Onboarding completion failed');
    }

    // Now check if agent profile exists after onboarding completion
    console.log('\n🌐 ===========================================');
    console.log('🌐 PHASE 3: CHECK AGENT PROFILE AFTER ONBOARDING');
    console.log('🌐 ===========================================');
    
    const agentResponseAfter = await page.request.get(`http://localhost:8000/api/v1/agent/public/${username}`);
    console.log(`📊 Agent profile after onboarding: ${agentResponseAfter.status()}`);
    
    if (agentResponseAfter.ok()) {
      const agentData = await agentResponseAfter.json();
      console.log('✅ Agent profile found after onboarding!');
      console.log(`👤 Agent Name: ${agentData.agent_name}`);
      console.log(`🔗 Agent Slug: ${agentData.slug}`);
      console.log(`📧 Agent Email: ${agentData.email}`);
      console.log(`📞 Agent Phone: ${agentData.phone}`);
      console.log(`🏢 Agent Bio: ${agentData.bio}`);
      console.log(`🌍 Agent Public: ${agentData.is_public}`);
      
      // Verify the agent website loads
      console.log('\n🌐 ===========================================');
      console.log('🌐 PHASE 4: VERIFY AGENT WEBSITE');
      console.log('🌐 ===========================================');
      
      await page.goto(`/agent/${username}`);
      await page.waitForLoadState('networkidle');
      
      const pageTitle = await page.title();
      console.log(`📄 Agent Website Title: "${pageTitle}"`);
      
      // Check if agent name is displayed
      const agentNameElement = page.locator('h1:has-text("John Doe"), h2:has-text("John Doe")').first();
      const agentNameVisible = await agentNameElement.isVisible();
      console.log(`👤 Agent Name Visible: ${agentNameVisible}`);
      
      if (agentNameVisible) {
        const agentName = await agentNameElement.textContent();
        console.log(`✅ Agent Name Displayed: "${agentName}"`);
      } else {
        console.log('⚠️ Agent name not visible on website');
        // Take a screenshot for debugging
        await page.screenshot({ path: 'agent-website-debug.png' });
      }
      
      // Check if bio is displayed
      const bioElement = page.locator('p').filter({ hasText: /professional|real estate|agent/i }).first();
      const bioVisible = await bioElement.isVisible();
      console.log(`📝 Bio Visible: ${bioVisible}`);
      
      if (bioVisible) {
        const bioText = await bioElement.textContent();
        console.log(`✅ Bio Displayed: "${bioText}"`);
      }
      
      console.log('\n✅ Agent Profile Creation Test PASSED!');
      expect(agentResponseAfter.status()).toBe(200);
      expect(agentData.agent_name).toContain('John Doe');
      expect(agentData.is_public).toBe(true);
      
    } else {
      const errorText = await agentResponseAfter.text();
      console.log(`❌ Agent profile not found after onboarding: ${errorText}`);
      
      // Let's check what's in the database
      console.log('\n🔍 ===========================================');
      console.log('🔍 DEBUGGING: CHECK DATABASE DIRECTLY');
      console.log('🔍 ===========================================');
      
      // Try to create agent profile manually
      const manualProfileData = {
        agent_id: userId,
        agent_name: `${testUser.first_name} ${testUser.last_name}`,
        slug: username,
        bio: `Professional Real Estate Agent at Real Estate Pro`,
        photo: '',
        phone: testUser.phone,
        email: testUser.email,
        office_address: '',
        specialties: ['Residential', 'Commercial'],
        experience: 'Professional',
        languages: ['English'],
        view_count: 0,
        contact_count: 0,
        is_public: true
      };
      
      console.log(`🔧 Attempting manual agent profile creation...`);
      const manualCreateResponse = await page.request.post('http://localhost:8000/api/v1/agent/public/create', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        data: manualProfileData
      });
      
      console.log(`📊 Manual creation status: ${manualCreateResponse.status()}`);
      
      if (manualCreateResponse.ok()) {
        console.log('✅ Manual agent profile creation successful');
        
        // Check again
        const finalCheckResponse = await page.request.get(`http://localhost:8000/api/v1/agent/public/${username}`);
        console.log(`📊 Final check status: ${finalCheckResponse.status()}`);
        
        if (finalCheckResponse.ok()) {
          const finalAgentData = await finalCheckResponse.json();
          console.log('✅ Agent profile now exists!');
          console.log(`👤 Final Agent Name: ${finalAgentData.agent_name}`);
        }
      } else {
        const manualErrorText = await manualCreateResponse.text();
        console.log(`❌ Manual creation failed: ${manualErrorText}`);
      }
      
      throw new Error('Agent profile was not created during onboarding completion');
    }
  });
});