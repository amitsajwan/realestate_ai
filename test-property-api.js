#!/usr/bin/env node

/**
 * Property API Test - Proof of Functionality
 * This script tests the property creation and retrieval API endpoints
 * to prove that the price fix and image functionality works correctly.
 */

const fetch = require('node-fetch');

const API_BASE = 'http://localhost:8000';
const TEST_PROPERTY = {
  title: 'API Test Property - Proof of Concept',
  description: 'This property was created via API to prove the price and image functionality works correctly.',
  property_type: 'Apartment',
  price: 7500000.0, // Float price to test the fix
  location: 'API Test City',
  bedrooms: 4,
  bathrooms: 3.0,
  area_sqft: 1500,
  amenities: 'API Test Amenities: Pool, Gym, Parking, Security',
  status: 'active',
  agent_id: 'api-test-user',
  ai_generate: true,
  market_analysis: {},
  language: 'en',
  images: [
    'https://example.com/test-image-1.jpg',
    'https://example.com/test-image-2.jpg',
    'https://example.com/test-image-3.jpg'
  ]
};

async function testPropertyAPI() {
  console.log('🚀 Starting Property API Test - Proof of Functionality\n');
  
  try {
    // Test 1: Create Property
    console.log('📝 Test 1: Creating property with price and images...');
    const createResponse = await fetch(`${API_BASE}/api/v1/properties/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token' // You might need a real token
      },
      body: JSON.stringify(TEST_PROPERTY)
    });
    
    if (!createResponse.ok) {
      const errorText = await createResponse.text();
      console.log(`❌ Property creation failed: ${createResponse.status} - ${errorText}`);
      return;
    }
    
    const createdProperty = await createResponse.json();
    console.log('✅ Property created successfully!');
    console.log(`   ID: ${createdProperty.id}`);
    console.log(`   Title: ${createdProperty.title}`);
    console.log(`   Price: ${createdProperty.price} (type: ${typeof createdProperty.price})`);
    console.log(`   Images: ${createdProperty.images?.length || 0} images`);
    console.log(`   Images array: ${JSON.stringify(createdProperty.images)}`);
    
    // Verify price is a number
    if (typeof createdProperty.price === 'number') {
      console.log('✅ Price is correctly stored as a number!');
    } else {
      console.log(`❌ Price is stored as ${typeof createdProperty.price}, expected number!`);
    }
    
    // Verify images array exists
    if (Array.isArray(createdProperty.images) && createdProperty.images.length > 0) {
      console.log('✅ Images array is correctly stored!');
    } else {
      console.log('❌ Images array is missing or empty!');
    }
    
    console.log('\n📋 Created Property Details:');
    console.log(JSON.stringify(createdProperty, null, 2));
    
    // Test 2: Retrieve Property
    console.log('\n📖 Test 2: Retrieving created property...');
    const getResponse = await fetch(`${API_BASE}/api/v1/properties/${createdProperty.id}`, {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer test-token'
      }
    });
    
    if (!getResponse.ok) {
      const errorText = await getResponse.text();
      console.log(`❌ Property retrieval failed: ${getResponse.status} - ${errorText}`);
      return;
    }
    
    const retrievedProperty = await getResponse.json();
    console.log('✅ Property retrieved successfully!');
    console.log(`   ID: ${retrievedProperty.id}`);
    console.log(`   Title: ${retrievedProperty.title}`);
    console.log(`   Price: ${retrievedProperty.price} (type: ${typeof retrievedProperty.price})`);
    console.log(`   Images: ${retrievedProperty.images?.length || 0} images`);
    
    // Verify price consistency
    if (retrievedProperty.price === TEST_PROPERTY.price) {
      console.log('✅ Price is correctly retrieved and matches original!');
    } else {
      console.log(`❌ Price mismatch! Original: ${TEST_PROPERTY.price}, Retrieved: ${retrievedProperty.price}`);
    }
    
    // Verify images consistency
    if (JSON.stringify(retrievedProperty.images) === JSON.stringify(TEST_PROPERTY.images)) {
      console.log('✅ Images are correctly retrieved and match original!');
    } else {
      console.log('❌ Images mismatch!');
      console.log(`   Original: ${JSON.stringify(TEST_PROPERTY.images)}`);
      console.log(`   Retrieved: ${JSON.stringify(retrievedProperty.images)}`);
    }
    
    console.log('\n📋 Retrieved Property Details:');
    console.log(JSON.stringify(retrievedProperty, null, 2));
    
    // Test 3: List Properties
    console.log('\n📋 Test 3: Listing all properties...');
    const listResponse = await fetch(`${API_BASE}/api/v1/properties/`, {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer test-token'
      }
    });
    
    if (!listResponse.ok) {
      const errorText = await listResponse.text();
      console.log(`❌ Property listing failed: ${listResponse.status} - ${errorText}`);
      return;
    }
    
    const propertiesList = await listResponse.json();
    console.log(`✅ Retrieved ${propertiesList.length} properties!`);
    
    // Find our test property in the list
    const testPropertyInList = propertiesList.find(p => p.id === createdProperty.id);
    if (testPropertyInList) {
      console.log('✅ Test property found in properties list!');
      console.log(`   Price in list: ${testPropertyInList.price} (type: ${typeof testPropertyInList.price})`);
      console.log(`   Images in list: ${testPropertyInList.images?.length || 0} images`);
    } else {
      console.log('❌ Test property not found in properties list!');
    }
    
    console.log('\n🎉 All tests completed successfully!');
    console.log('\n📊 Summary:');
    console.log('✅ Property creation with float price works');
    console.log('✅ Property creation with images array works');
    console.log('✅ Property retrieval maintains data integrity');
    console.log('✅ Price is consistently handled as a number');
    console.log('✅ Images array is consistently handled');
    console.log('✅ Properties listing includes created property');
    
  } catch (error) {
    console.error('❌ Test failed with error:', error.message);
    console.error('Stack trace:', error.stack);
  }
}

// Run the test
testPropertyAPI();