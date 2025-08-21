import { test, expect } from '@playwright/test';

test.describe('Improved Dashboard Tests', () => {
    test('should load improved dashboard with better UX', async ({ page }) => {
        // Login first
        await page.goto('/');
        await page.fill('#email', 'demo@mumbai.com');
        await page.fill('#password', 'demo123');
        await page.click('button[type="submit"]');
        
        // Wait for redirect to dashboard
        await page.waitForURL('/dashboard');
        
                // Verify dashboard title
        await expect(page).toHaveTitle(/PropertyAI - Next-Gen AI Real Estate Dashboard/);

        // Check for improved navigation
        await expect(page.locator('.navbar-brand-nextgen')).toContainText('PropertyAI');
        
        // Verify onboarding link goes to modern onboarding
        const sidebarOnboardingLink = page.locator('.nav-item-nextgen[href="/modern-onboarding"]');
        await expect(sidebarOnboardingLink).toBeVisible();
        await expect(sidebarOnboardingLink).toContainText('AI Onboarding');
        
        // Check for functional sections
        await expect(page.locator('h3:has-text("AI Content Generation")')).toBeVisible();
        await expect(page.locator('h3:has-text("Social Media Automation")')).toBeVisible();
        await expect(page.locator('h3:has-text("AI-Powered Analytics")')).toBeVisible();
        
                // Verify stat cards are properly styled
        const statCards = page.locator('.stat-card');
        await expect(statCards).toHaveCount(4);

        // Check for AI assistant
        await expect(page.locator('.ai-assistant')).toBeVisible();
        
        // Verify AI branding button
        const aiBrandingBtn = page.locator('button:has-text("AI Branding Suggestions")');
        await expect(aiBrandingBtn).toBeVisible();
        
        // Check Facebook integration
        await expect(page.locator('button:has-text("Connect Facebook")')).toBeVisible();
        
        // Verify content generation area
        await expect(page.locator('#generatedContent')).toBeVisible();
        await expect(page.locator('#propertyLocation')).toBeVisible();
        await expect(page.locator('#propertyPrice')).toBeVisible();
        await expect(page.locator('#propertyBedrooms')).toBeVisible();
        await expect(page.locator('#propertyFeatures')).toBeVisible();
    });

    test('should be mobile responsive', async ({ page }) => {
        // Set mobile viewport
        await page.setViewportSize({ width: 375, height: 667 });
        
        // Login first
        await page.goto('/');
        await page.fill('#email', 'demo@mumbai.com');
        await page.fill('#password', 'demo123');
        await page.click('button[type="submit"]');
        
        // Wait for redirect to dashboard
        await page.waitForURL('/dashboard');
        
        // Verify mobile navigation works - check for responsive design
        const sidebar = page.locator('.sidebar-nextgen');
        await expect(sidebar).toBeVisible();
        
        // Check that content is properly sized for mobile
        const cards = page.locator('.card');
        await expect(cards.first()).toBeVisible();
        
        // Verify buttons are properly sized
        const buttons = page.locator('.btn');
        await expect(buttons.first()).toBeVisible();
        
        // Check form controls are mobile-friendly
        await expect(page.locator('#firstName')).toBeVisible();
        await expect(page.locator('#lastName')).toBeVisible();
        
        // Verify status badges are readable on mobile
        const statusBadges = page.locator('.status-badge');
        await expect(statusBadges.first()).toBeVisible();
    });

    test('should navigate to modern onboarding correctly', async ({ page }) => {
        // Login first
        await page.goto('/');
        await page.fill('#email', 'demo@mumbai.com');
        await page.fill('#password', 'demo123');
        await page.click('button[type="submit"]');
        
        // Wait for redirect to dashboard
        await page.waitForURL('/dashboard');
        
        // Click the modern onboarding link
        await page.click('a[href="/modern-onboarding"]');
        
        // Verify we're on the modern onboarding page
        await page.waitForURL('/modern-onboarding');
        await expect(page).toHaveTitle(/PropertyAI - Modern Agent Onboarding/);
        
        // Verify it's the 6-step modern onboarding
        await expect(page.locator('#step1')).toBeVisible();
        await expect(page.locator('.progress-bar')).toBeVisible();
    });

    test('should have working AI features', async ({ page }) => {
        // Login first
        await page.goto('/');
        await page.fill('#email', 'demo@mumbai.com');
        await page.fill('#password', 'demo123');
        await page.click('button[type="submit"]');
        
        // Wait for redirect to dashboard
        await page.waitForURL('/dashboard');
        
        // Test AI features - navigate to onboarding first
        await page.click('.nav-item-nextgen[href="/modern-onboarding"]');
        await page.waitForURL('/modern-onboarding');
        
        // Fill onboarding form
        await page.fill('#firstName', 'John');
        await page.fill('#lastName', 'Doe');
        
        // Wait for response (this might take a moment)
        await page.waitForTimeout(2000);
        
        // Check if tagline was populated (indicating AI worked)
        const taglineValue = await page.locator('#tagline').inputValue();
        expect(taglineValue.length).toBeGreaterThan(0);
        
        // Test content generation
        await page.fill('#propertyLocation', 'Kharadi, Pune');
        await page.fill('#propertyPrice', '1.5 Cr');
        await page.fill('#propertyBedrooms', '2 BHK');
        await page.fill('#propertyFeatures', 'Gym, Pool, Garden');
        await page.click('button:has-text("Generate AI Content")');
        
        // Wait for content generation
        await page.waitForTimeout(2000);
        
        // Verify content was generated
        const generatedContent = page.locator('#generatedContent');
        await expect(generatedContent).not.toContainText('AI-generated content will appear here...');
        await expect(generatedContent).toContainText('Kharadi, Pune');
    });

    test('should have proper logout functionality', async ({ page }) => {
        // Login first
        await page.goto('/');
        await page.fill('#email', 'demo@mumbai.com');
        await page.fill('#password', 'demo123');
        await page.click('button[type="submit"]');
        
        // Wait for redirect to dashboard
        await page.waitForURL('/dashboard');
        
        // Click logout - look for logout in the sidebar
        await page.click('.nav-item-nextgen:has-text("Logout")');
        
        // Verify redirect to login page
        await page.waitForURL('/');
        await expect(page).toHaveTitle(/Real Estate CRM - Login/);
        
        // Verify we can't access dashboard without login
        await page.goto('/dashboard');
        await page.waitForURL('/');
    });
});
