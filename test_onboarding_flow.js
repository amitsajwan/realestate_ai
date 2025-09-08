// Simple test script to verify onboarding flow
const axios = require('axios');

const API_BASE = 'http://localhost:8000';

async function testOnboardingFlow() {
  try {
    console.log('🧪 Testing Onboarding Flow...\n');

    // Step 1: Register a new user
    console.log('1️⃣ Registering new user...');
    const uniqueEmail = `test${Date.now()}@example.com`;
    const registerData = {
      email: uniqueEmail,
      password: 'MySecurePass1!',
      first_name: 'John',
      last_name: 'Doe',
      phone: '+1234567890'
    };

    const registerResponse = await axios.post(`${API_BASE}/api/v1/auth/register`, registerData);
    console.log('✅ Registration successful:', registerResponse.data);

    // Step 1.5: Login to get tokens
    console.log('\n1.5️⃣ Logging in to get tokens...');
    const loginData = {
      email: uniqueEmail,
      password: 'MySecurePass1!'
    };
    const loginResponse = await axios.post(`${API_BASE}/api/v1/auth/login`, loginData);
    console.log('✅ Login successful:', loginResponse.data);

    const { access_token, user } = loginResponse.data;
    const userId = user.id;

    // Step 2: Check initial onboarding state
    console.log('\n2️⃣ Checking initial onboarding state...');
    const initialOnboardingResponse = await axios.get(`${API_BASE}/api/v1/onboarding/${userId}`, {
      headers: { Authorization: `Bearer ${access_token}` }
    });
    console.log('✅ Initial onboarding state:', initialOnboardingResponse.data);

    // Step 3: Update onboarding step 1
    console.log('\n3️⃣ Updating onboarding step 1...');
    const step1Data = {
      step_number: 1,
      data: {
        firstName: 'John',
        lastName: 'Doe',
        phone: '+1234567890'
      }
    };
    const step1Response = await axios.post(`${API_BASE}/api/v1/onboarding/${userId}`, step1Data, {
      headers: { Authorization: `Bearer ${access_token}` }
    });
    console.log('✅ Step 1 updated:', step1Response.data);

    // Step 4: Update onboarding step 2
    console.log('\n4️⃣ Updating onboarding step 2...');
    const step2Data = {
      step_number: 2,
      data: {
        company: 'Test Company',
        position: 'Test Agent'
      }
    };
    const step2Response = await axios.post(`${API_BASE}/api/v1/onboarding/${userId}`, step2Data, {
      headers: { Authorization: `Bearer ${access_token}` }
    });
    console.log('✅ Step 2 updated:', step2Response.data);

    // Step 5: Complete onboarding
    console.log('\n5️⃣ Completing onboarding...');
    const completeResponse = await axios.post(`${API_BASE}/api/v1/onboarding/${userId}/complete`, {}, {
      headers: { Authorization: `Bearer ${access_token}` }
    });
    console.log('✅ Onboarding completed:', completeResponse.data);

    // Step 6: Verify user state after completion
    console.log('\n6️⃣ Verifying user state after completion...');
    const userResponse = await axios.get(`${API_BASE}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${access_token}` }
    });
    console.log('✅ User state after completion:', {
      onboardingCompleted: userResponse.data.onboarding_completed,
      onboardingStep: userResponse.data.onboarding_step
    });

    // Step 7: Check onboarding state after completion
    console.log('\n7️⃣ Checking onboarding state after completion...');
    const finalOnboardingResponse = await axios.get(`${API_BASE}/api/v1/onboarding/${userId}`, {
      headers: { Authorization: `Bearer ${access_token}` }
    });
    console.log('✅ Final onboarding state:', finalOnboardingResponse.data);

    console.log('\n🎉 Onboarding flow test completed successfully!');

  } catch (error) {
    console.error('❌ Test failed:', error.response?.data || error.message);
  }
}

testOnboardingFlow();