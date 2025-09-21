import { test, expect } from '@playwright/test';

/**
 * Natural Language Test: Complete User Journey
 * ===========================================
 * 
 * Test Description: "Complete end-to-end user journey from registration to property sale"
 * 
 * This comprehensive test validates the entire user workflow:
 * 1. User registration and onboarding
 * 2. Property creation and management
 * 3. AI-powered content generation
 * 4. Social media publishing
 * 5. Lead management and CRM
 * 6. Analytics and reporting
 * 7. Property sale completion
 */

test.describe('Complete User Journey - Natural Language Testing', () => {
  test('Complete end-to-end user workflow', async ({ page }) => {
    // === PHASE 1: USER ONBOARDING ===
    // Natural Language: "New user registers and completes onboarding"
    await page.goto('/register');
    await page.fill('input[name="firstName"]', 'Jane');
    await page.fill('input[name="lastName"]', 'Smith');
    await page.fill('input[name="email"]', 'jane.smith@example.com');
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.fill('input[name="confirmPassword"]', 'SecurePassword123!');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=Welcome to PropertyAI')).toBeVisible();
    await page.click('button[data-testid="complete-onboarding"]');
    
    // === PHASE 2: PROPERTY MANAGEMENT ===
    // Natural Language: "User creates their first property listing"
    await page.click('text=Add Property');
    await page.fill('input[name="title"]', 'Modern Apartment in Bangalore');
    await page.fill('textarea[name="description"]', 'Spacious 3BHK with modern amenities');
    await page.fill('input[name="price"]', '8500000');
    await page.selectOption('select[name="propertyType"]', 'apartment');
    await page.fill('input[name="location"]', 'Whitefield, Bangalore');
    await page.fill('input[name="bedrooms"]', '3');
    await page.fill('input[name="bathrooms"]', '2');
    await page.fill('input[name="areaSqft"]', '1800');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=Property created successfully')).toBeVisible();
    
    // === PHASE 3: AI CONTENT GENERATION ===
    // Natural Language: "User generates AI-powered marketing content"
    await page.click('button[data-testid="promote-property-button"]');
    await page.check('input[name="platforms"][value="facebook"]');
    await page.check('input[name="platforms"][value="instagram"]');
    await page.selectOption('select[name="tone"]', 'professional');
    await page.click('button[data-testid="generate-content-button"]');
    
    await expect(page.locator('text=Content generated successfully')).toBeVisible({ timeout: 30000 });
    
    // === PHASE 4: SOCIAL MEDIA PUBLISHING ===
    // Natural Language: "User publishes content to social media"
    await page.click('button[data-testid="publish-all-button"]');
    await expect(page.locator('text=Published successfully to Facebook')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('text=Published successfully to Instagram')).toBeVisible({ timeout: 30000 });
    
    // === PHASE 5: LEAD MANAGEMENT ===
    // Natural Language: "User receives and manages leads"
    await page.click('text=CRM');
    await expect(page.locator('text=CRM Dashboard')).toBeVisible();
    
    // Simulate lead generation
    await page.click('button[data-testid="add-lead-button"]');
    await page.fill('input[name="name"]', 'Potential Buyer');
    await page.fill('input[name="email"]', 'buyer@example.com');
    await page.fill('input[name="phone"]', '+91-9876543210');
    await page.fill('input[name="budget"]', '10000000');
    await page.selectOption('select[name="urgency"]', 'high');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=Lead created successfully')).toBeVisible();
    
    // === PHASE 6: ANALYTICS AND REPORTING ===
    // Natural Language: "User views performance analytics"
    await page.click('text=Analytics');
    await expect(page.locator('[data-testid="total-properties"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-views"]')).toBeVisible();
    await expect(page.locator('[data-testid="conversion-rate"]')).toBeVisible();
    
    // View AI insights
    await page.click('text=AI Insights');
    await expect(page.locator('[data-testid="ai-insights-panel"]')).toBeVisible();
    
    // === PHASE 7: PROPERTY SALE ===
    // Natural Language: "User marks property as sold"
    await page.click('text=Properties');
    await page.click('button[data-testid="edit-property-button"]');
    await page.selectOption('select[name="status"]', 'sold');
    await page.fill('input[name="salePrice"]', '8200000');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=Property marked as sold')).toBeVisible();
    
    // === PHASE 8: FINAL REPORTING ===
    // Natural Language: "User generates final sales report"
    await page.click('text=Analytics');
    await page.click('button[data-testid="export-report-button"]');
    await page.selectOption('select[name="report-format"]', 'pdf');
    await page.click('button[data-testid="download-report"]');
    
    await expect(page.locator('text=Report download started')).toBeVisible();
    
    // Natural Language: "Verify complete journey was successful"
    await expect(page.locator('text=Property sold successfully')).toBeVisible();
    await expect(page.locator('[data-testid="total-revenue"]')).toContainText('₹82,00,000');
  });
});
