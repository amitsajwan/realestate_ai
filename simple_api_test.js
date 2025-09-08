// Simple API test without starting services
const axios = require('axios');

async function testAPI() {
  console.log('🔍 Testing API endpoints...\n');
  
  // Test different possible backend URLs
  const possibleURLs = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://0.0.0.0:8000'
  ];
  
  for (const baseURL of possibleURLs) {
    console.log(`Testing ${baseURL}...`);
    try {
      const response = await axios.get(`${baseURL}/docs`, { timeout: 2000 });
      console.log(`✅ ${baseURL} is responding`);
      
      // Test a simple registration
      console.log('Testing registration...');
      const regResponse = await axios.post(`${baseURL}/api/v1/auth/register`, {
        email: `test_${Date.now()}@example.com`,
        password: 'TestPass123!',
        first_name: 'Test',
        last_name: 'User',
        phone: '+1234567890'
      });
      console.log('✅ Registration works!');
      console.log('User data:', regResponse.data.user);
      break;
      
    } catch (error) {
      console.log(`❌ ${baseURL} not responding: ${error.message}`);
    }
  }
}

testAPI();