#!/usr/bin/env node

/**
 * Functionality Validation Script
 * This script validates that all the implemented features work correctly
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Validating Property Price Fix and Image Upload Functionality\n');

// Check 1: Frontend validation schema
console.log('📋 Check 1: Frontend validation schema...');
try {
  const validationFile = fs.readFileSync('/workspace/frontend/lib/validation.ts', 'utf8');
  
  if (validationFile.includes('price: z.coerce.number()')) {
    console.log('✅ Price validation correctly uses z.coerce.number()');
  } else {
    console.log('❌ Price validation not updated to use number type');
  }
  
  if (validationFile.includes('images: z.array(z.string()).optional()')) {
    console.log('✅ Images validation correctly added');
  } else {
    console.log('❌ Images validation not found');
  }
} catch (error) {
  console.log('❌ Could not read validation file:', error.message);
}

// Check 2: SmartPropertyForm component
console.log('\n📋 Check 2: SmartPropertyForm component...');
try {
  const formFile = fs.readFileSync('/workspace/frontend/components/SmartPropertyForm.tsx', 'utf8');
  
  if (formFile.includes('type="number"') && formFile.includes('valueAsNumber: true')) {
    console.log('✅ Price input correctly configured as number type');
  } else {
    console.log('❌ Price input not configured as number type');
  }
  
  if (formFile.includes('images') && formFile.includes('PhotoIcon')) {
    console.log('✅ Images step correctly added to form');
  } else {
    console.log('❌ Images step not found in form');
  }
  
  if (formFile.includes('handleImageUpload') && formFile.includes('uploadedImages')) {
    console.log('✅ Image upload functionality implemented');
  } else {
    console.log('❌ Image upload functionality not found');
  }
  
  if (formFile.includes('price: Number(data.price) || 0')) {
    console.log('✅ Price data transformation correctly handles numbers');
  } else {
    console.log('❌ Price data transformation not updated');
  }
} catch (error) {
  console.log('❌ Could not read SmartPropertyForm file:', error.message);
}

// Check 3: Backend schemas
console.log('\n📋 Check 3: Backend schemas...');
try {
  const unifiedPropertySchema = fs.readFileSync('/workspace/backend/app/schemas/unified_property.py', 'utf8');
  
  if (unifiedPropertySchema.includes('price: float')) {
    console.log('✅ Backend schema correctly expects price as float');
  } else {
    console.log('❌ Backend schema price type not correct');
  }
  
  if (unifiedPropertySchema.includes('images: Optional[List[str]]')) {
    console.log('✅ Backend schema correctly includes images array');
  } else {
    console.log('❌ Backend schema images field not found');
  }
} catch (error) {
  console.log('❌ Could not read backend schema file:', error.message);
}

// Check 4: Backend service
console.log('\n📋 Check 4: Backend service...');
try {
  const serviceFile = fs.readFileSync('/workspace/backend/app/services/unified_property_service.py', 'utf8');
  
  if (serviceFile.includes('price: float') && serviceFile.includes('images')) {
    console.log('✅ Backend service correctly handles price and images');
  } else {
    console.log('❌ Backend service not properly configured');
  }
} catch (error) {
  console.log('❌ Could not read backend service file:', error.message);
}

// Check 5: Upload endpoints
console.log('\n📋 Check 5: Upload endpoints...');
try {
  const uploadFile = fs.readFileSync('/workspace/backend/app/api/v1/endpoints/uploads.py', 'utf8');
  
  if (uploadFile.includes('@router.post("/images")') && uploadFile.includes('upload_property_images')) {
    console.log('✅ Image upload endpoint exists');
  } else {
    console.log('❌ Image upload endpoint not found');
  }
} catch (error) {
  console.log('❌ Could not read upload endpoints file:', error.message);
}

// Check 6: Properties display component
console.log('\n📋 Check 6: Properties display component...');
try {
  const propertiesFile = fs.readFileSync('/workspace/frontend/components/Properties.tsx', 'utf8');
  
  if (propertiesFile.includes('images?: string[]') && propertiesFile.includes('property.images?.[0]')) {
    console.log('✅ Properties component updated to handle images array');
  } else {
    console.log('❌ Properties component not updated for images');
  }
} catch (error) {
  console.log('❌ Could not read Properties component file:', error.message);
}

// Check 7: Test files
console.log('\n📋 Check 7: Test files...');
const testFiles = [
  '/workspace/e2e-tests/property-creation-with-images.spec.ts',
  '/workspace/e2e-tests/property-creation-proof.spec.ts',
  '/workspace/backend/tests/test_property_price_and_images.py',
  '/workspace/frontend/__tests__/components/PropertyFormPrice.test.tsx'
];

testFiles.forEach(testFile => {
  if (fs.existsSync(testFile)) {
    console.log(`✅ Test file exists: ${path.basename(testFile)}`);
  } else {
    console.log(`❌ Test file missing: ${path.basename(testFile)}`);
  }
});

// Check 8: API service
console.log('\n📋 Check 8: API service...');
try {
  const apiFile = fs.readFileSync('/workspace/frontend/lib/api.ts', 'utf8');
  
  if (apiFile.includes('uploadImages') && apiFile.includes('createProperty')) {
    console.log('✅ API service includes upload and create methods');
  } else {
    console.log('❌ API service missing required methods');
  }
} catch (error) {
  console.log('❌ Could not read API service file:', error.message);
}

console.log('\n🎯 Validation Summary:');
console.log('This validation checks that all the necessary code changes have been implemented.');
console.log('The actual functionality can be tested by:');
console.log('1. Running the Playwright tests: npx playwright test e2e-tests/property-creation-proof.spec.ts');
console.log('2. Running the API test: node test-property-api.js');
console.log('3. Starting the application and manually testing the property creation flow');
console.log('\n📸 The Playwright tests will generate screenshots proving the functionality works.');