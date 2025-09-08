# Manual Testing Guide - Complete Flow

## Prerequisites
1. Backend server running on `http://localhost:8000`
2. Frontend server running on `http://localhost:3000`

## Complete Flow Test: Onboarding → Property → Post → Promote

### Phase 1: User Setup & Onboarding

#### 1.1 Registration
1. Navigate to `http://localhost:3000/login`
2. Click "Sign up" to switch to registration mode
3. Fill in the registration form:
   - Email: `test@example.com`
   - First Name: `John`
   - Last Name: `Doe`
   - Phone: `+1234567890`
   - Password: `MySecurePass1!`
   - Confirm Password: `MySecurePass1!`
4. Click "Sign up"
5. **Expected**: Redirected to onboarding page

#### 1.2 Onboarding Flow
1. **Step 1 - Personal Info**:
   - Fill in First Name: `John`
   - Fill in Last Name: `Doe`
   - Fill in Phone: `+1234567890`
   - Click "Next Step"
   - **Expected**: Progress to Step 2

2. **Step 2 - Company Details**:
   - Fill in Company Name: `Test Real Estate`
   - Fill in Position: `Senior Agent`
   - Fill in License Number: `RE123456`
   - Click "Next Step"
   - **Expected**: Progress to Step 3

3. **Step 3 - AI Branding**:
   - Select AI Content Style: `Professional`
   - Select AI Tone: `Friendly`
   - (Optional) Click "Generate Branding" to test AI features
   - Click "Next Step"
   - **Expected**: Progress to Step 4

4. **Step 4 - Social Integration**:
   - Click "Next Step" (skip Facebook integration for now)
   - **Expected**: Progress to Step 5

5. **Step 5 - Terms & Privacy**:
   - Check "I agree to the Terms of Service"
   - Check "I agree to the Privacy Policy"
   - Click "Next Step"
   - **Expected**: Progress to Step 6

6. **Step 6 - Profile Photo**:
   - Click "Complete Onboarding"
   - **Expected**: Redirected to dashboard with success message

#### 1.3 Verify Onboarding Completion
1. Check that you're on the dashboard page
2. Verify the user profile shows onboarding is completed
3. Try navigating to `/onboarding` - should redirect back to dashboard

### Phase 2: Property Management

#### 2.1 Create Property
1. On the dashboard, click "Add Property" or navigate to "Properties" section
2. Fill in the property form:
   - Title: `Beautiful Test Property`
   - Description: `A stunning property for testing purposes`
   - Price: `500000`
   - Property Type: `House`
   - Bedrooms: `3`
   - Bathrooms: `2`
   - Area: `1500`
   - Address: `123 Test Street, Test City`
   - Status: `For Sale`
3. Click "Save Property"
4. **Expected**: Property created successfully, redirected to properties list

#### 2.2 Post Property
1. From the properties list, find the created property
2. Click "Post" or "List Property"
3. Select platforms (Website, MLS, etc.)
4. Click "Post Property"
5. **Expected**: Property posted to selected platforms

#### 2.3 Promote Property
1. From the properties list, find the posted property
2. Click "Promote" or "Share"
3. Select social media platforms (Facebook, Instagram, etc.)
4. Customize the promotion message
5. Click "Promote Property"
6. **Expected**: Property promoted on selected social platforms

### Phase 3: Verification

#### 3.1 Dashboard Verification
1. Check dashboard stats are updated
2. Verify property appears in recent properties
3. Check that all navigation works correctly

#### 3.2 Property Management Verification
1. Navigate to Properties section
2. Verify property is listed with correct status
3. Test property editing functionality
4. Test property deletion (if needed)

#### 3.3 Social Integration Verification
1. Check that social media posts were created
2. Verify Facebook integration (if connected)
3. Test social media analytics (if available)

## Expected Results

### Successful Flow Indicators:
- ✅ User can register and login
- ✅ Onboarding completes without returning to step 1
- ✅ User is redirected to dashboard after onboarding
- ✅ Property can be created successfully
- ✅ Property can be posted to listings
- ✅ Property can be promoted on social media
- ✅ All navigation works correctly
- ✅ User state persists across page refreshes

### Error Scenarios to Test:
- ❌ Invalid registration data
- ❌ Incomplete onboarding steps
- ❌ Invalid property data
- ❌ Network connectivity issues
- ❌ Authentication token expiration

## Troubleshooting

### Common Issues:
1. **Onboarding returns to step 1**: Check auth state management
2. **Property creation fails**: Verify property form validation
3. **Social media integration fails**: Check API keys and permissions
4. **Navigation issues**: Verify routing configuration

### Debug Steps:
1. Check browser console for errors
2. Check network tab for failed API calls
3. Verify backend server is running
4. Check database connectivity
5. Verify authentication tokens

## Test Data

### Test User:
- Email: `test@example.com`
- Password: `MySecurePass1!`
- Name: `John Doe`

### Test Property:
- Title: `Beautiful Test Property`
- Price: `$500,000`
- Type: `House`
- Location: `123 Test Street, Test City`

This manual testing guide ensures the complete flow works from user registration through property promotion.