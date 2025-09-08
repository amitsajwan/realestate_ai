#!/usr/bin/env node

/**
 * Comprehensive User Flow Test
 * Tests the complete user journey: Registration → Login → Onboarding → Dashboard
 * This will help identify exactly where the onboarding loop issue occurs.
 */

const axios = require('axios');

const API_BASE = 'http://localhost:8000';
const FRONTEND_BASE = 'http://localhost:3000';

// Test configuration
const TEST_USER = {
  email: `test_${Date.now()}@example.com`,
  password: 'TestPass123!',
  first_name: 'Test',
  last_name: 'User',
  phone: '+1234567890'
};

console.log('🧪 COMPREHENSIVE USER FLOW TEST');
console.log('================================');
console.log(`Testing with user: ${TEST_USER.email}`);
console.log('');

async function waitForServices() {
  console.log('🔍 Checking if services are running...');
  
  // Check backend
  try {
    const response = await axios.get(`${API_BASE}/docs`, { timeout: 5000 });
    console.log('✅ Backend is running');
  } catch (error) {
    console.log('❌ Backend not responding. Please start: cd backend && uvicorn app.main:app --reload');
    process.exit(1);
  }
  
  // Check frontend
  try {
    const response = await axios.get(`${FRONTEND_BASE}`, { timeout: 5000 });
    console.log('✅ Frontend is running');
  } catch (error) {
    console.log('❌ Frontend not responding. Please start: cd frontend && npm run dev');
    process.exit(1);
  }
  
  console.log('');
}

async function testRegistration() {
  console.log('1️⃣ TESTING USER REGISTRATION');
  console.log('----------------------------');
  
  try {
    const response = await axios.post(`${API_BASE}/api/v1/auth/register`, {
      email: TEST_USER.email,
      password: TEST_USER.password,
      first_name: TEST_USER.first_name,
      last_name: TEST_USER.last_name,
      phone: TEST_USER.phone
    });
    
    console.log('✅ Registration successful');
    console.log(`   User ID: ${response.data.user?.id || 'Not provided'}`);
    console.log(`   Email: ${response.data.user?.email}`);
    console.log(`   Onboarding completed: ${response.data.user?.onboarding_completed || false}`);
    console.log(`   Onboarding step: ${response.data.user?.onboarding_step || 1}`);
    
    return response.data;
  } catch (error) {
    console.log('❌ Registration failed');
    console.log(`   Error: ${error.response?.data?.detail || error.message}`);
    throw error;
  }
}

async function testLogin() {
  console.log('\n2️⃣ TESTING USER LOGIN');
  console.log('---------------------');
  
  try {
    const response = await axios.post(`${API_BASE}/api/v1/auth/login`, {
      email: TEST_USER.email,
      password: TEST_USER.password
    });
    
    console.log('✅ Login successful');
    console.log(`   Access token: ${response.data.access_token ? 'Provided' : 'Missing'}`);
    console.log(`   User ID: ${response.data.user?.id}`);
    console.log(`   Onboarding completed: ${response.data.user?.onboarding_completed || false}`);
    console.log(`   Onboarding step: ${response.data.user?.onboarding_step || 1}`);
    
    return {
      token: response.data.access_token,
      user: response.data.user
    };
  } catch (error) {
    console.log('❌ Login failed');
    console.log(`   Error: ${error.response?.data?.detail || error.message}`);
    throw error;
  }
}

async function testOnboardingFlow(token, userId) {
  console.log('\n3️⃣ TESTING ONBOARDING FLOW');
  console.log('---------------------------');
  
  const headers = { Authorization: `Bearer ${token}` };
  
  // Step 1: Check initial onboarding state
  console.log('\n📋 Checking initial onboarding state...');
  try {
    const response = await axios.get(`${API_BASE}/api/v1/onboarding/${userId}`, { headers });
    console.log(`   Current step: ${response.data.step_number}`);
    console.log(`   Step data: ${JSON.stringify(response.data.data)}`);
  } catch (error) {
    console.log(`   ⚠️ Could not get onboarding state: ${error.response?.data?.detail || error.message}`);
  }
  
  // Step 2: Complete onboarding steps
  const onboardingSteps = [
    {
      step: 1,
      name: 'Personal Info',
      data: {
        firstName: TEST_USER.first_name,
        lastName: TEST_USER.last_name,
        phone: TEST_USER.phone
      }
    },
    {
      step: 2,
      name: 'Company Details',
      data: {
        company: 'Test Real Estate',
        position: 'Test Agent',
        licenseNumber: 'TEST123'
      }
    },
    {
      step: 3,
      name: 'AI Preferences',
      data: {
        aiStyle: 'Professional',
        aiTone: 'Friendly'
      }
    },
    {
      step: 4,
      name: 'Social (Skip)',
      data: {}
    },
    {
      step: 5,
      name: 'Terms',
      data: {
        termsAccepted: true,
        privacyAccepted: true
      }
    }
  ];
  
  for (const stepInfo of onboardingSteps) {
    console.log(`\n📝 Completing step ${stepInfo.step}: ${stepInfo.name}`);
    try {
      const response = await axios.post(`${API_BASE}/api/v1/onboarding/${userId}`, {
        step_number: stepInfo.step,
        data: stepInfo.data
      }, { headers });
      
      console.log(`   ✅ Step ${stepInfo.step} completed successfully`);
    } catch (error) {
      console.log(`   ❌ Step ${stepInfo.step} failed: ${error.response?.data?.detail || error.message}`);
      throw error;
    }
  }
  
  // Step 3: Complete onboarding
  console.log('\n🎯 Completing onboarding...');
  try {
    const response = await axios.post(`${API_BASE}/api/v1/onboarding/${userId}/complete`, {}, { headers });
    console.log('   ✅ Onboarding completion API call successful');
    console.log(`   Response: ${JSON.stringify(response.data)}`);
  } catch (error) {
    console.log(`   ❌ Onboarding completion failed: ${error.response?.data?.detail || error.message}`);
    throw error;
  }
  
  // Step 4: Verify user state after completion
  console.log('\n🔍 Verifying user state after completion...');
  try {
    const response = await axios.get(`${API_BASE}/api/v1/auth/me`, { headers });
    console.log(`   Onboarding completed: ${response.data.onboarding_completed}`);
    console.log(`   Onboarding step: ${response.data.onboarding_step}`);
    console.log(`   User ID: ${response.data.id}`);
    
    // This is the critical check - if onboarding_completed is false, that's the bug!
    if (!response.data.onboarding_completed) {
      console.log('   🚨 BUG FOUND: onboarding_completed is still false after completion!');
      return { bugFound: true, userState: response.data };
    } else {
      console.log('   ✅ User correctly marked as onboarding completed');
      return { bugFound: false, userState: response.data };
    }
  } catch (error) {
    console.log(`   ❌ Could not verify user state: ${error.response?.data?.detail || error.message}`);
    throw error;
  }
}

async function testPropertyFeatures(token, userId) {
  console.log('\n4️⃣ TESTING PROPERTY FEATURES');
  console.log('-----------------------------');
  
  const headers = { Authorization: `Bearer ${token}` };
  
  // Test property creation
  console.log('\n🏠 Testing property creation...');
  try {
    const propertyData = {
      title: 'Test Property',
      description: 'A beautiful test property',
      price: 500000,
      property_type: 'House',
      bedrooms: 3,
      bathrooms: 2,
      area: 1500,
      address: '123 Test Street, Test City',
      status: 'for-sale'
    };
    
    const response = await axios.post(`${API_BASE}/api/v1/properties`, propertyData, { headers });
    console.log('   ✅ Property creation successful');
    console.log(`   Property ID: ${response.data.id}`);
    return response.data.id;
  } catch (error) {
    console.log(`   ⚠️ Property creation not available: ${error.response?.data?.detail || error.message}`);
    return null;
  }
}

async function runCompleteTest() {
  try {
    await waitForServices();
    
    // Test registration
    const registrationResult = await testRegistration();
    
    // Test login
    const loginResult = await testLogin();
    const { token, user } = loginResult;
    
    if (!user?.id) {
      throw new Error('User ID not provided in login response');
    }
    
    // Test onboarding flow
    const onboardingResult = await testOnboardingFlow(token, user.id);
    
    // Test property features
    await testPropertyFeatures(token, user.id);
    
    // Final summary
    console.log('\n🎉 TEST SUMMARY');
    console.log('===============');
    console.log('✅ Registration: PASSED');
    console.log('✅ Login: PASSED');
    
    if (onboardingResult.bugFound) {
      console.log('❌ Onboarding: BUG FOUND - User not marked as completed');
      console.log('\n🐛 ROOT CAUSE ANALYSIS:');
      console.log('The onboarding completion API call succeeds, but the user\'s onboarding_completed flag remains false.');
      console.log('This causes the dashboard to redirect back to onboarding, creating the loop you experienced.');
      console.log('\n🔧 RECOMMENDED FIXES:');
      console.log('1. Check the onboarding completion service in backend/app/services/onboarding_service.py');
      console.log('2. Verify the database update is actually persisting');
      console.log('3. Check if the auth/me endpoint returns updated user data');
    } else {
      console.log('✅ Onboarding: PASSED');
    }
    
    console.log('\n📊 Property features: Tested (may need API implementation)');
    
  } catch (error) {
    console.log('\n❌ TEST FAILED');
    console.log(`Error: ${error.message}`);
    console.log('\nPlease check the error details above and ensure both services are running.');
  }
}

// Run the test
runCompleteTest();