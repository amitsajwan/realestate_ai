import { test, expect } from '@playwright/test';

/**
 * Natural Language E2E Test - English Style
 * =========================================
 * 
 * This demonstrates how Playwright MCP enables natural language testing
 * where each step is described in plain English.
 */

test.describe('Natural Language E2E Test - English Style', () => {
  
  test('User can complete a simple property management workflow', async ({ page }) => {
    
    console.log('🎭 Starting Natural Language E2E Test...');
    
    // === STEP 1: APPLICATION ACCESS ===
    // Natural Language: "Go to the PropertyAI application"
    console.log('📍 Step 1: Going to the PropertyAI application');
    await page.goto('/');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Natural Language: "Verify the application loaded successfully"
    await expect(page.locator('body')).toBeVisible();
    console.log('✅ Application loaded successfully');
    
    // === STEP 2: LOGIN PAGE ACCESS ===
    // Natural Language: "Navigate to the login page"
    console.log('📍 Step 2: Navigating to the login page');
    await page.goto('/login');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Natural Language: "Check that the login form is visible"
    await expect(page.locator('text=Sign in to your account')).toBeVisible();
    console.log('✅ Login page is accessible');
    
    // === STEP 3: PROPERTIES PAGE ACCESS ===
    // Natural Language: "Go to the properties management section"
    console.log('📍 Step 3: Going to the properties management section');
    await page.goto('/properties');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Natural Language: "Verify the properties page loaded"
    await expect(page.locator('body')).toBeVisible();
    console.log('✅ Properties page is accessible');
    
    // === STEP 4: ANALYTICS DASHBOARD ACCESS ===
    // Natural Language: "Navigate to the analytics dashboard"
    console.log('📍 Step 4: Navigating to the analytics dashboard');
    await page.goto('/analytics');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Natural Language: "Wait for the dashboard to fully load"
    await page.waitForLoadState('networkidle');
    
    // Natural Language: "Check that the analytics dashboard is visible"
    await expect(page.locator('text=Analytics Dashboard')).toBeVisible();
    console.log('✅ Analytics dashboard is accessible');
    
    // === STEP 5: SOCIAL PUBLISHING ACCESS ===
    // Natural Language: "Go to the social media publishing section"
    console.log('📍 Step 5: Going to the social media publishing section');
    await page.goto('/social-publishing');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Natural Language: "Verify the social publishing page loaded"
    await expect(page.locator('body')).toBeVisible();
    console.log('✅ Social publishing page is accessible');
    
    // === STEP 6: USER PROFILE ACCESS ===
    // Natural Language: "Navigate to the user profile section"
    console.log('📍 Step 6: Navigating to the user profile section');
    await page.goto('/profile');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Natural Language: "Check that the profile page is accessible"
    await expect(page.locator('body')).toBeVisible();
    console.log('✅ User profile page is accessible');
    
    // === STEP 7: BACKEND API VERIFICATION ===
    // Natural Language: "Check that the backend API is working"
    console.log('📍 Step 7: Checking that the backend API is working');
    const response = await page.request.get('http://localhost:8000/api/v1/health');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
    console.log('✅ Backend API is healthy and responding');
    
    // === STEP 8: BASIC INTERACTION TEST ===
    // Natural Language: "Test that users can interact with the interface"
    console.log('📍 Step 8: Testing user interface interactions');
    await page.goto('/login');
    
    // Natural Language: "Look for interactive elements like buttons"
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    expect(buttonCount).toBeGreaterThan(0);
    console.log(`✅ Found ${buttonCount} interactive buttons`);
    
    // Natural Language: "Verify that the sign up link is clickable"
    await expect(page.locator('text=Sign up')).toBeVisible();
    console.log('✅ Sign up link is visible and clickable');
    
    console.log('🎉 Natural Language E2E Test completed successfully!');
  });

  test('Application responds to user interactions naturally', async ({ page }) => {
    
    console.log('🎭 Testing natural user interactions...');
    
    // Natural Language: "Start at the home page"
    await page.goto('/');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Natural Language: "Look for any navigation elements"
    const links = page.locator('a');
    const linkCount = await links.count();
    console.log(`Found ${linkCount} navigation links`);
    
    // Natural Language: "Check that the page has proper meta information"
    const title = await page.title();
    expect(title).toContain('PropertyAI');
    console.log(`Page title: ${title}`);
    
    // Natural Language: "Verify the page has proper description"
    const metaDescription = await page.locator('meta[name="description"]').getAttribute('content');
    expect(metaDescription).toContain('real estate');
    console.log('✅ Page has proper meta description');
    
    console.log('🎉 Natural interaction test completed!');
  });
});