#!/usr/bin/env python3
"""
Playwright MCP E2E Testing Setup for PropertyAI
==============================================

This module sets up and configures Playwright MCP for natural language
end-to-end testing of the PropertyAI platform.

Key Features:
- Natural language test descriptions
- Cross-browser testing (Chromium, Firefox, WebKit)
- API + UI integration testing
- CI/CD pipeline integration
"""

import subprocess
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import asyncio

class PlaywrightMCPSetup:
    """Setup and configuration for Playwright MCP E2E testing"""
    
    def __init__(self):
        self.project_root = "/workspace"
        self.frontend_dir = "/workspace/frontend"
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        
    def setup_playwright_mcp(self) -> bool:
        """Setup Playwright MCP environment"""
        try:
            print("🎭 Setting up Playwright MCP for PropertyAI...")
            
            # Install Playwright if not already installed
            self._install_playwright()
            
            # Install Playwright browsers
            self._install_playwright_browsers()
            
            # Create Playwright configuration
            self._create_playwright_config()
            
            # Create natural language test templates
            self._create_test_templates()
            
            print("✅ Playwright MCP setup completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Playwright MCP setup failed: {str(e)}")
            return False
    
    def _install_playwright(self):
        """Install Playwright and dependencies"""
        print("📦 Installing Playwright...")
        
        # Install Playwright
        subprocess.run([
            "npm", "install", "-D", "@playwright/test", "@playwright/mcp"
        ], cwd=self.frontend_dir, check=True)
        
        print("✅ Playwright installed successfully")
    
    def _install_playwright_browsers(self):
        """Install Playwright browsers"""
        print("🌐 Installing Playwright browsers...")
        
        subprocess.run([
            "npx", "playwright", "install"
        ], cwd=self.frontend_dir, check=True)
        
        print("✅ Playwright browsers installed successfully")
    
    def _create_playwright_config(self):
        """Create Playwright configuration file"""
        config_content = """import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright MCP Configuration for PropertyAI
 * ===========================================
 * 
 * This configuration enables natural language testing across
 * multiple browsers with API + UI integration.
 */

export default defineConfig({
  testDir: './e2e/mcp-tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['json', { outputFile: 'e2e-results.json' }],
    ['junit', { outputFile: 'e2e-results.xml' }]
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
"""
        
        config_path = os.path.join(self.frontend_dir, "playwright.config.ts")
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        print("✅ Playwright configuration created")
    
    def _create_test_templates(self):
        """Create natural language test templates"""
        print("📝 Creating natural language test templates...")
        
        # Create MCP test directory
        mcp_test_dir = os.path.join(self.frontend_dir, "e2e", "mcp-tests")
        os.makedirs(mcp_test_dir, exist_ok=True)
        
        # Create test templates for critical user journeys
        templates = {
            "01-authentication-flow.spec.ts": self._get_auth_test_template(),
            "02-property-management.spec.ts": self._get_property_test_template(),
            "03-social-publishing.spec.ts": self._get_social_test_template(),
            "04-analytics-dashboard.spec.ts": self._get_analytics_test_template(),
            "05-complete-user-journey.spec.ts": self._get_complete_journey_template()
        }
        
        for filename, content in templates.items():
            file_path = os.path.join(mcp_test_dir, filename)
            with open(file_path, 'w') as f:
                f.write(content)
        
        print("✅ Natural language test templates created")
    
    def _get_auth_test_template(self) -> str:
        """Get authentication flow test template"""
        return '''import { test, expect } from '@playwright/test';

/**
 * Natural Language Test: User Authentication Flow
 * ==============================================
 * 
 * Test Description: "User can register, login, and access dashboard"
 * 
 * This test validates the complete authentication journey including:
 * - User registration with valid data
 * - Email verification (if implemented)
 * - User login with correct credentials
 * - Dashboard access after authentication
 * - Logout functionality
 */

test.describe('Authentication Flow - Natural Language Testing', () => {
  test('User can register and login successfully', async ({ page }) => {
    // Natural Language: "Go to the application and verify it loads"
    await page.goto('/');
    await expect(page).toHaveTitle(/PropertyAI/);
    
    // Natural Language: "Navigate to registration page"
    await page.click('text=Sign Up');
    await expect(page).toHaveURL(/.*register/);
    
    // Natural Language: "Fill registration form with valid user data"
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.fill('input[name="confirmPassword"]', 'SecurePassword123!');
    
    // Natural Language: "Submit registration and verify success"
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Registration successful')).toBeVisible();
    
    // Natural Language: "Navigate to login page"
    await page.click('text=Sign In');
    await expect(page).toHaveURL(/.*login/);
    
    // Natural Language: "Login with registered credentials"
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.click('button[type="submit"]');
    
    // Natural Language: "Verify user is logged in and dashboard loads"
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('text=Welcome, John')).toBeVisible();
    
    // Natural Language: "Verify logout functionality works"
    await page.click('button[data-testid="logout-button"]');
    await expect(page).toHaveURL(/.*login/);
  });
  
  test('User login fails with invalid credentials', async ({ page }) => {
    // Natural Language: "Go to login page"
    await page.goto('/login');
    
    // Natural Language: "Try to login with invalid credentials"
    await page.fill('input[name="email"]', 'invalid@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    
    // Natural Language: "Verify error message is displayed"
    await expect(page.locator('text=Invalid credentials')).toBeVisible();
    await expect(page).toHaveURL(/.*login/);
  });
});
'''
    
    def _get_property_test_template(self) -> str:
        """Get property management test template"""
        return '''import { test, expect } from '@playwright/test';

/**
 * Natural Language Test: Property Management Flow
 * ==============================================
 * 
 * Test Description: "User can create, view, edit, and delete properties"
 * 
 * This test validates the complete property management journey:
 * - Create new property with all required fields
 * - View property in the properties list
 * - Edit property details
 * - Delete property
 * - Search and filter properties
 */

test.describe('Property Management Flow - Natural Language Testing', () => {
  test.beforeEach(async ({ page }) => {
    // Natural Language: "Login as authenticated user"
    await page.goto('/login');
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*dashboard/);
  });
  
  test('User can create and manage properties', async ({ page }) => {
    // Natural Language: "Navigate to properties management page"
    await page.click('text=Properties');
    await expect(page).toHaveURL(/.*properties/);
    
    // Natural Language: "Click add new property button"
    await page.click('button[data-testid="add-property-button"]');
    await expect(page.locator('text=Add New Property')).toBeVisible();
    
    // Natural Language: "Fill property form with complete details"
    await page.fill('input[name="title"]', 'Luxury Villa in Mumbai');
    await page.fill('textarea[name="description"]', 'Beautiful 4BHK villa with garden and pool');
    await page.fill('input[name="price"]', '15000000');
    await page.selectOption('select[name="propertyType"]', 'villa');
    await page.fill('input[name="location"]', 'Bandra West, Mumbai');
    await page.fill('input[name="bedrooms"]', '4');
    await page.fill('input[name="bathrooms"]', '3');
    await page.fill('input[name="areaSqft"]', '2500');
    
    // Natural Language: "Add property amenities and features"
    await page.check('input[name="amenities"][value="parking"]');
    await page.check('input[name="amenities"][value="garden"]');
    await page.check('input[name="amenities"][value="pool"]');
    await page.check('input[name="features"][value="modular_kitchen"]');
    await page.check('input[name="features"][value="wooden_flooring"]');
    
    // Natural Language: "Submit property and verify it was created"
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Property created successfully')).toBeVisible();
    
    // Natural Language: "Verify property appears in properties list"
    await expect(page.locator('text=Luxury Villa in Mumbai')).toBeVisible();
    await expect(page.locator('text=₹1,50,00,000')).toBeVisible();
    
    // Natural Language: "Edit the created property"
    await page.click('button[data-testid="edit-property-button"]');
    await page.fill('input[name="title"]', 'Updated Luxury Villa in Mumbai');
    await page.fill('input[name="price"]', '16000000');
    await page.click('button[type="submit"]');
    
    // Natural Language: "Verify property was updated"
    await expect(page.locator('text=Property updated successfully')).toBeVisible();
    await expect(page.locator('text=Updated Luxury Villa in Mumbai')).toBeVisible();
    await expect(page.locator('text=₹1,60,00,000')).toBeVisible();
    
    // Natural Language: "Search for the property"
    await page.fill('input[placeholder*="Search properties"]', 'Luxury Villa');
    await expect(page.locator('text=Updated Luxury Villa in Mumbai')).toBeVisible();
    
    // Natural Language: "Delete the property"
    await page.click('button[data-testid="delete-property-button"]');
    await page.click('button[data-testid="confirm-delete"]');
    await expect(page.locator('text=Property deleted successfully')).toBeVisible();
    await expect(page.locator('text=Updated Luxury Villa in Mumbai')).not.toBeVisible();
  });
});
'''
    
    def _get_social_test_template(self) -> str:
        """Get social publishing test template"""
        return '''import { test, expect } from '@playwright/test';

/**
 * Natural Language Test: Social Media Publishing Flow
 * ==================================================
 * 
 * Test Description: "User can generate AI content and publish to social media"
 * 
 * This test validates the complete social publishing journey:
 * - Select property for social media promotion
 * - Generate AI-powered content for different platforms
 * - Preview and customize the generated content
 * - Publish to multiple social media platforms
 * - Track publishing status and analytics
 */

test.describe('Social Media Publishing Flow - Natural Language Testing', () => {
  test.beforeEach(async ({ page }) => {
    // Natural Language: "Login and navigate to properties"
    await page.goto('/login');
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.click('button[type="submit"]');
    await page.click('text=Properties');
  });
  
  test('User can generate and publish AI content', async ({ page }) => {
    // Natural Language: "Select a property for social media promotion"
    await page.click('button[data-testid="promote-property-button"]');
    await expect(page.locator('text=Social Media Publishing')).toBeVisible();
    
    // Natural Language: "Choose target platforms for promotion"
    await page.check('input[name="platforms"][value="facebook"]');
    await page.check('input[name="platforms"][value="instagram"]');
    await page.check('input[name="platforms"][value="linkedin"]');
    
    // Natural Language: "Select content tone and style"
    await page.selectOption('select[name="tone"]', 'luxury');
    await page.selectOption('select[name="language"]', 'en');
    await page.selectOption('select[name="length"]', 'medium');
    
    // Natural Language: "Generate AI-powered content"
    await page.click('button[data-testid="generate-content-button"]');
    await expect(page.locator('text=Generating content')).toBeVisible();
    
    // Wait for AI generation to complete
    await expect(page.locator('text=Content generated successfully')).toBeVisible({ timeout: 30000 });
    
    // Natural Language: "Preview generated content for each platform"
    await expect(page.locator('[data-testid="facebook-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="instagram-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="linkedin-preview"]')).toBeVisible();
    
    // Natural Language: "Customize content if needed"
    await page.click('button[data-testid="edit-facebook-content"]');
    await page.fill('textarea[name="facebook-content"]', 'Customized Facebook content with property highlights');
    await page.click('button[data-testid="save-content"]');
    
    // Natural Language: "Schedule or publish immediately"
    await page.selectOption('select[name="publish-option"]', 'immediate');
    
    // Natural Language: "Publish to all selected platforms"
    await page.click('button[data-testid="publish-all-button"]');
    await expect(page.locator('text=Publishing to social media')).toBeVisible();
    
    // Natural Language: "Verify publishing status and success"
    await expect(page.locator('text=Published successfully to Facebook')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('text=Published successfully to Instagram')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('text=Published successfully to LinkedIn')).toBeVisible({ timeout: 30000 });
    
    // Natural Language: "Navigate to publishing history"
    await page.click('text=Publishing History');
    await expect(page.locator('text=Recent Publications')).toBeVisible();
    
    // Natural Language: "Verify published posts appear in history"
    await expect(page.locator('text=Facebook Post')).toBeVisible();
    await expect(page.locator('text=Instagram Post')).toBeVisible();
    await expect(page.locator('text=LinkedIn Post')).toBeVisible();
  });
  
  test('User can save content as draft', async ({ page }) => {
    // Natural Language: "Start social media publishing process"
    await page.click('button[data-testid="promote-property-button"]');
    
    // Natural Language: "Generate content but save as draft instead of publishing"
    await page.check('input[name="platforms"][value="facebook"]');
    await page.selectOption('select[name="tone"]', 'friendly');
    await page.click('button[data-testid="generate-content-button"]');
    await expect(page.locator('text=Content generated successfully')).toBeVisible({ timeout: 30000 });
    
    // Natural Language: "Save as draft instead of publishing"
    await page.click('button[data-testid="save-draft-button"]');
    await expect(page.locator('text=Draft saved successfully')).toBeVisible();
    
    // Natural Language: "Navigate to drafts and verify content was saved"
    await page.click('text=Drafts');
    await expect(page.locator('text=Saved Drafts')).toBeVisible();
    await expect(page.locator('text=Facebook Draft')).toBeVisible();
  });
});
'''
    
    def _get_analytics_test_template(self) -> str:
        """Get analytics dashboard test template"""
        return '''import { test, expect } from '@playwright/test';

/**
 * Natural Language Test: Analytics Dashboard Flow
 * ==============================================
 * 
 * Test Description: "User can view and interact with analytics dashboard"
 * 
 * This test validates the analytics dashboard functionality:
 * - View key performance metrics
 * - Interact with charts and visualizations
 * - Filter data by time periods
 * - Export analytics reports
 * - View AI-powered insights and recommendations
 */

test.describe('Analytics Dashboard Flow - Natural Language Testing', () => {
  test.beforeEach(async ({ page }) => {
    // Natural Language: "Login and navigate to analytics"
    await page.goto('/login');
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.click('button[type="submit"]');
    await page.click('text=Analytics');
  });
  
  test('User can view and interact with analytics dashboard', async ({ page }) => {
    // Natural Language: "Verify analytics dashboard loads with key metrics"
    await expect(page.locator('text=Analytics Dashboard')).toBeVisible();
    await expect(page.locator('[data-testid="total-properties"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-views"]')).toBeVisible();
    await expect(page.locator('[data-testid="conversion-rate"]')).toBeVisible();
    await expect(page.locator('[data-testid="revenue"]')).toBeVisible();
    
    // Natural Language: "View property performance charts"
    await page.click('text=Property Performance');
    await expect(page.locator('[data-testid="property-performance-chart"]')).toBeVisible();
    
    // Natural Language: "Filter data by time period"
    await page.selectOption('select[name="time-period"]', 'last-30-days');
    await expect(page.locator('text=Last 30 Days')).toBeVisible();
    
    // Natural Language: "View revenue trends"
    await page.click('text=Revenue Trends');
    await expect(page.locator('[data-testid="revenue-chart"]')).toBeVisible();
    
    // Natural Language: "Interact with chart elements"
    await page.hover('[data-testid="revenue-chart"] .recharts-bar');
    await expect(page.locator('.recharts-tooltip')).toBeVisible();
    
    // Natural Language: "View user analytics"
    await page.click('text=User Analytics');
    await expect(page.locator('[data-testid="user-analytics-chart"]')).toBeVisible();
    
    // Natural Language: "Access AI insights and recommendations"
    await page.click('text=AI Insights');
    await expect(page.locator('[data-testid="ai-insights-panel"]')).toBeVisible();
    await expect(page.locator('text=AI-Powered Recommendations')).toBeVisible();
    
    // Natural Language: "View market insights and trends"
    await expect(page.locator('[data-testid="market-insights"]')).toBeVisible();
    await expect(page.locator('text=Market Trends')).toBeVisible();
    
    // Natural Language: "Export analytics report"
    await page.click('button[data-testid="export-report-button"]');
    await page.selectOption('select[name="report-format"]', 'pdf');
    await page.click('button[data-testid="download-report"]');
    
    // Natural Language: "Verify report download started"
    await expect(page.locator('text=Report download started')).toBeVisible();
  });
  
  test('User can view detailed property analytics', async ({ page }) => {
    // Natural Language: "Navigate to property-specific analytics"
    await page.click('text=Property Analytics');
    await expect(page.locator('text=Property Performance')).toBeVisible();
    
    // Natural Language: "Select a specific property for detailed view"
    await page.click('[data-testid="property-selector"]');
    await page.click('text=Luxury Villa in Mumbai');
    
    // Natural Language: "View property-specific metrics and charts"
    await expect(page.locator('[data-testid="property-views-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="property-inquiries-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="property-engagement-chart"]')).toBeVisible();
    
    // Natural Language: "View property comparison with similar properties"
    await page.click('text=Compare Properties');
    await expect(page.locator('[data-testid="property-comparison-chart"]')).toBeVisible();
    
    // Natural Language: "View social media performance for this property"
    await page.click('text=Social Media Performance');
    await expect(page.locator('[data-testid="social-performance-chart"]')).toBeVisible();
    await expect(page.locator('text=Facebook Performance')).toBeVisible();
    await expect(page.locator('text=Instagram Performance')).toBeVisible();
  });
});
'''
    
    def _get_complete_journey_template(self) -> str:
        """Get complete user journey test template"""
        return '''import { test, expect } from '@playwright/test';

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
'''

if __name__ == "__main__":
    setup = PlaywrightMCPSetup()
    success = setup.setup_playwright_mcp()
    
    if success:
        print("\n🎉 Playwright MCP setup completed successfully!")
        print("📋 Next steps:")
        print("1. Start backend server: cd /workspace/backend && python -m uvicorn app.main:app --reload")
        print("2. Start frontend server: cd /workspace/frontend && npm run dev")
        print("3. Run E2E tests: cd /workspace/frontend && npx playwright test")
        print("4. View test results: cd /workspace/frontend && npx playwright show-report")
    else:
        print("\n❌ Playwright MCP setup failed. Please check the errors above.")