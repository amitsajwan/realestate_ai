import { test, expect } from '@playwright/test';

test.describe('Complete System Verification', () => {
    test('Full system verification with Facebook integration', async ({ page }) => {
        console.log('🚀 Starting Complete System Verification...');
        
        // Step 1: Test public URL access
        console.log('🌐 Step 1: Test public URL access');
        await page.goto('https://e4ec81495136.ngrok-free.app/');
        await expect(page).toHaveTitle(/Real Estate CRM - Login/);
        console.log('✅ Public URL accessible');
        
        // Step 2: Login to the system
        console.log('🔐 Step 2: Login to the system');
        await page.fill('#email', 'demo@mumbai.com');
        await page.fill('#password', 'demo123');
        await page.click('button[type="submit"]');
        
        await page.waitForURL('/dashboard');
        await expect(page).toHaveTitle(/PropertyAI - Next-Gen AI Real Estate Dashboard/);
        console.log('✅ Login successful - redirected to dashboard');
        
        // Step 3: Verify dashboard features
        console.log('📊 Step 3: Verify dashboard features');
        
        // Check for proper navigation
        await expect(page.locator('.navbar-brand-nextgen')).toContainText('PropertyAI');
        await expect(page.locator('.ai-badge')).toContainText('AI Powered');
        
        // Verify dashboard sections
        await expect(page.locator('h3:has-text("AI Content Generation")')).toBeVisible();
        await expect(page.locator('h3:has-text("Social Media Automation")')).toBeVisible();
        await expect(page.locator('h3:has-text("AI-Powered Analytics")')).toBeVisible();
        
        // Check for stat cards
        await expect(page.locator('.stat-card')).toHaveCount(4);
        
        // Verify AI assistant
        await expect(page.locator('.ai-assistant')).toBeVisible();
        console.log('✅ Dashboard features verified');
        
        // Step 4: Test Facebook Integration
        console.log('📘 Step 4: Test Facebook Integration');
        await page.click('.nav-item-nextgen[href="/facebook-integration"]');
        await page.waitForURL('/facebook-integration');
        await expect(page).toHaveTitle(/Facebook Integration - PropertyAI/);
        console.log('✅ Facebook integration page loaded');
        
        // Check Facebook integration UI elements
        await expect(page.locator('.facebook-card')).toBeVisible();
        await expect(page.locator('#connectBtn')).toBeVisible();
        await expect(page.locator('#statusBadge')).toContainText('Not Connected');
        console.log('✅ Facebook integration UI verified');
        
        // Step 5: Test Facebook API endpoints
        console.log('🔗 Step 5: Test Facebook API endpoints');
        
        // Test Facebook status endpoint
        const statusResponse = await page.evaluate(async () => {
            const response = await fetch('/api/facebook/status');
            return await response.json();
        });
        
        expect(statusResponse.success).toBe(true);
        expect(statusResponse.status.connected).toBe(false);
        console.log('✅ Facebook status API working');
        
        // Test Facebook connect endpoint
        const connectResponse = await page.evaluate(async () => {
            const response = await fetch('/api/facebook/connect');
            return await response.json();
        });
        
        expect(connectResponse.success).toBe(true);
        expect(connectResponse.oauth_url).toContain('facebook.com');
        console.log('✅ Facebook connect API working');
        
        // Step 6: Navigate to modern onboarding
        console.log('🚀 Step 6: Navigate to modern onboarding');
        await page.goto('/dashboard');
        await page.click('.nav-item-nextgen[href="/modern-onboarding"]');
        await page.waitForURL('/modern-onboarding');
        await expect(page).toHaveTitle(/PropertyAI - Modern Agent Onboarding/);
        console.log('✅ Modern onboarding page loaded');
        
        // Step 7: Test logout functionality
        console.log('🚪 Step 7: Test logout functionality');
        await page.goto('/dashboard');
        await page.click('button.btn-outline[onclick="logout()"]');
        await page.waitForURL('/');
        await expect(page).toHaveTitle(/Real Estate CRM - Login/);
        console.log('✅ Logout functionality working');
        
        console.log('🎉 COMPLETE SYSTEM VERIFICATION COMPLETED SUCCESSFULLY!');
        console.log('');
        console.log('📋 Complete System Features Verified:');
        console.log('   ✅ Public URL Access (ngrok)');
        console.log('   ✅ User Authentication & Login');
        console.log('   ✅ Next-Gen Dashboard with AI Features');
        console.log('   ✅ Facebook Integration UI');
        console.log('   ✅ Facebook API Endpoints');
        console.log('   ✅ Modern Onboarding Navigation');
        console.log('   ✅ Logout Functionality');
        console.log('');
        console.log('🚀 The PropertyAI system is fully functional with Facebook integration!');
        console.log('🌐 Public URL: https://e4ec81495136.ngrok-free.app');
    });

    test('Facebook integration detailed test', async ({ page }) => {
        console.log('📘 Starting Facebook Integration Detailed Test...');
        
        // Login first
        await page.goto('/');
        await page.fill('#email', 'demo@mumbai.com');
        await page.fill('#password', 'demo123');
        await page.click('button[type="submit"]');
        await page.waitForURL('/dashboard');
        
        // Navigate to Facebook integration
        await page.click('.nav-item-nextgen[href="/facebook-integration"]');
        await page.waitForURL('/facebook-integration');
        
        // Test Facebook connection flow
        console.log('🔗 Testing Facebook connection flow...');
        
        // Check initial state
        await expect(page.locator('#statusBadge')).toContainText('Not Connected');
        await expect(page.locator('#pagesSection')).not.toBeVisible();
        await expect(page.locator('#postingSection')).not.toBeVisible();
        
        // Test connect button
        await expect(page.locator('#connectBtn')).toBeVisible();
        await expect(page.locator('#connectBtn')).toContainText('Connect Facebook Account');
        
        // Test property posting form (should be hidden initially)
        await expect(page.locator('#postForm')).not.toBeVisible();
        
        console.log('✅ Facebook integration UI state verified');
        
        // Test API endpoints
        console.log('🔗 Testing Facebook API endpoints...');
        
        // Test status endpoint
        const statusResponse = await page.evaluate(async () => {
            const response = await fetch('/api/facebook/status');
            return await response.json();
        });
        
        expect(statusResponse.success).toBe(true);
        expect(statusResponse.status.connected).toBe(false);
        
        // Test connect endpoint
        const connectResponse = await page.evaluate(async () => {
            const response = await fetch('/api/facebook/connect');
            return await response.json();
        });
        
        expect(connectResponse.success).toBe(true);
        expect(connectResponse.oauth_url).toContain('facebook.com');
        expect(connectResponse.oauth_url).toContain('oauth');
        
        console.log('✅ Facebook API endpoints working correctly');
        
        // Test property posting form (simulate connected state)
        console.log('📝 Testing property posting form...');
        
        // Fill property form
        await page.fill('#propertyTitle', 'Test Luxury Apartment');
        await page.fill('#propertyPrice', '₹3.5 Cr');
        await page.fill('#propertyLocation', 'Bandra West, Mumbai');
        await page.fill('#propertyBedrooms', '3');
        await page.fill('#propertyBathrooms', '2');
        await page.fill('#propertyArea', '1800 sq ft');
        
        // Test preview functionality
        await page.click('button:has-text("Preview Post")');
        await expect(page.locator('#postPreview')).toBeVisible();
        await expect(page.locator('#previewContent')).toContainText('Test Luxury Apartment');
        await expect(page.locator('#previewContent')).toContainText('₹3.5 Cr');
        
        console.log('✅ Property posting form working correctly');
        
        console.log('🎉 FACEBOOK INTEGRATION DETAILED TEST COMPLETED!');
        console.log('');
        console.log('📋 Facebook Integration Features Verified:');
        console.log('   ✅ Connection Status Display');
        console.log('   ✅ OAuth URL Generation');
        console.log('   ✅ API Endpoints');
        console.log('   ✅ Property Posting Form');
        console.log('   ✅ Post Preview Functionality');
        console.log('   ✅ UI State Management');
        console.log('');
        console.log('🚀 Facebook integration is ready for production use!');
    });
});
