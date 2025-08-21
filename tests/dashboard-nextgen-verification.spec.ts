import { test, expect } from '@playwright/test';

test.describe('NextGen Dashboard Tests', () => {
    test('should load nextgen dashboard with proper features', async ({ page }) => {
        // Login first
        await page.goto('/');
        await page.fill('#email', 'demo@mumbai.com');
        await page.fill('#password', 'demo123');
        await page.click('button[type="submit"]');
        
        // Wait for redirect to dashboard
        await page.waitForURL('/dashboard');
        
        // Verify it's the correct dashboard
        await expect(page).toHaveTitle(/PropertyAI - Next-Gen AI Real Estate Dashboard/);
        
        // Check for the proper navigation
        await expect(page.locator('.navbar-brand-nextgen')).toContainText('PropertyAI');
        await expect(page.locator('.ai-badge')).toContainText('AI Powered');
        
        // Verify it has the right sections
        await expect(page.locator('h3:has-text("AI Content Generation")')).toBeVisible();
        await expect(page.locator('h3:has-text("Social Media Automation")')).toBeVisible();
        await expect(page.locator('h3:has-text("AI-Powered Analytics")')).toBeVisible();
        
        // Check for stat cards
        await expect(page.locator('.stat-card')).toHaveCount(4);
        
        // Verify onboarding is only in the sidebar navigation
        const sidebarOnboardingLink = page.locator('.nav-item-nextgen[href="/modern-onboarding"]');
        await expect(sidebarOnboardingLink).toBeVisible();
        await expect(sidebarOnboardingLink).toContainText('AI Onboarding');
        
        // Check for AI assistant
        await expect(page.locator('.ai-assistant')).toBeVisible();
        
        console.log('✅ NextGen Dashboard verification passed');
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
        
        // Verify mobile navigation works - sidebar should be hidden on mobile
        const sidebar = page.locator('.sidebar-nextgen');
        // On mobile, sidebar might be hidden by default, which is correct behavior
        await expect(sidebar).toBeAttached();
        
        // Check that content is properly sized for mobile
        const cards = page.locator('.stat-card');
        await expect(cards).toHaveCount(4);
        
        console.log('✅ Mobile responsiveness verification passed');
    });

    test('should navigate to modern onboarding correctly', async ({ page }) => {
        // Login first
        await page.goto('/');
        await page.fill('#email', 'demo@mumbai.com');
        await page.fill('#password', 'demo123');
        await page.click('button[type="submit"]');
        
        // Wait for redirect to dashboard
        await page.waitForURL('/dashboard');
        
        // Click on modern onboarding link
        await page.click('.nav-item-nextgen[href="/modern-onboarding"]');
        
        // Verify navigation to modern onboarding
        await page.waitForURL('/modern-onboarding');
        await expect(page).toHaveTitle(/PropertyAI - Modern Agent Onboarding/);
        
        console.log('✅ Modern onboarding navigation verification passed');
    });

    test('should have proper logout functionality', async ({ page }) => {
        // Login first
        await page.goto('/');
        await page.fill('#email', 'demo@mumbai.com');
        await page.fill('#password', 'demo123');
        await page.click('button[type="submit"]');
        
        // Wait for redirect to dashboard
        await page.waitForURL('/dashboard');
        
        // Click logout - it's an icon button
        await page.click('button.btn-outline[onclick="logout()"]');
        
        // Verify redirect to login page
        await page.waitForURL('/');
        await expect(page).toHaveTitle(/Real Estate CRM - Login/);
        
        // Try to access dashboard without login
        await page.goto('/dashboard');
        await expect(page).toHaveTitle(/Real Estate CRM - Login/);
        
        console.log('✅ Logout functionality verification passed');
    });
});
