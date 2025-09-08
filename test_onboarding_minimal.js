// Minimal Onboarding Test - Focus on Core Flow
const axios = require('axios');

const API_BASE = 'http://localhost:8000';

async function testOnboardingMinimal() {
  try {
    console.log('🧪 Testing Minimal Onboarding Flow...\n');

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

    // Step 2: Login to get tokens
    console.log('\n2️⃣ Logging in...');
    const loginData = {
      email: uniqueEmail,
      password: 'MySecurePass1!'
    };
    const loginResponse = await axios.post(`${API_BASE}/api/v1/auth/login`, loginData);
    console.log('✅ Login successful');

    const { access_token, user } = loginResponse.data;
    const userId = user.id;

    console.log('\n3️⃣ User details:');
    console.log('User ID:', userId);
    console.log('User onboarding status:', {
      onboardingCompleted: user.onboarding_completed,
      onboardingStep: user.onboarding_step
    });

    // Step 3: Test onboarding step 1
    console.log('\n4️⃣ Testing onboarding step 1...');
    const step1Data = {
      step_number: 1,
      data: {
        firstName: 'John',
        lastName: 'Doe',
        phone: '+1234567890'
      }
    };

    try {
      const step1Response = await axios.post(`${API_BASE}/api/v1/onboarding/${userId}`, step1Data, {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      console.log('✅ Step 1 completed:', step1Response.data);
    } catch (error) {
      console.log('❌ Step 1 failed:', error.response?.data || error.message);
    }

    // Step 4: Test onboarding completion
    console.log('\n5️⃣ Testing onboarding completion...');
    try {
      const completeResponse = await axios.post(`${API_BASE}/api/v1/onboarding/${userId}/complete`, {}, {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      console.log('✅ Onboarding completed:', completeResponse.data);
    } catch (error) {
      console.log('❌ Completion failed:', error.response?.data || error.message);
    }

    // Step 5: Verify final user state
    console.log('\n6️⃣ Verifying final user state...');
    try {
      const userResponse = await axios.get(`${API_BASE}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      console.log('✅ Final user state:', {
        onboardingCompleted: userResponse.data.onboarding_completed,
        onboardingStep: userResponse.data.onboarding_step
      });
    } catch (error) {
      console.log('❌ User verification failed:', error.response?.data || error.message);
    }

    console.log('\n🎉 Minimal onboarding test completed!');

  } catch (error) {
    console.error('❌ Test failed:', error.response?.data || error.message);
  }
}

testOnboardingMinimal();