// Test script to check user lookup
const axios = require('axios');

const API_BASE = 'http://localhost:8000';

async function testUserLookup() {
  try {
    console.log('🔍 Testing User Lookup...\n');

    // First, register a new user
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

    // Login to get tokens
    console.log('\n2️⃣ Logging in to get tokens...');
    const loginData = {
      email: uniqueEmail,
      password: 'MySecurePass1!'
    };
    const loginResponse = await axios.post(`${API_BASE}/api/v1/auth/login`, loginData);
    console.log('✅ Login successful:', loginResponse.data);

    const { access_token, user } = loginResponse.data;
    const userId = user.id;

    console.log('\n3️⃣ User details:');
    console.log('User ID:', userId);
    console.log('User ID type:', typeof userId);
    console.log('User ID length:', userId.length);

    // Test if user ID is a valid MongoDB ObjectId format (24 hex characters)
    const objectIdRegex = /^[0-9a-fA-F]{24}$/;
    const isValidObjectId = objectIdRegex.test(userId);
    console.log('Is valid ObjectId format:', isValidObjectId);

    // Try to get current user info
    console.log('\n4️⃣ Getting current user info...');
    try {
      const userResponse = await axios.get(`${API_BASE}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      console.log('✅ Current user info:', userResponse.data);
    } catch (error) {
      console.log('❌ Failed to get current user:', error.response?.data || error.message);
    }

    // Try onboarding endpoint
    console.log('\n5️⃣ Testing onboarding endpoint...');
    try {
      const onboardingResponse = await axios.get(`${API_BASE}/api/v1/onboarding/${userId}`, {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      console.log('✅ Onboarding response:', onboardingResponse.data);
    } catch (error) {
      console.log('❌ Onboarding failed:', error.response?.data || error.message);
    }

  } catch (error) {
    console.error('❌ Test failed:', error.response?.data || error.message);
  }
}

testUserLookup();